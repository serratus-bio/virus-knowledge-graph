import os

from datasources.neo4j import gds
from queries import feature_queries, utils
from config import (
    DIR_CFG,
    MODEL_CFGS,
    CUR_MODEL_VERSION,
)

import pandas as pd


MODEL_CFG = MODEL_CFGS[CUR_MODEL_VERSION]


def run_query(query):
    return gds.run_cypher(query)


def store_run_artifact(run_uid, obj, filename):
    print("Storing artifact", obj)
    results_dir = f"{DIR_CFG['RESULTS_DIR']}link_prediction"\
        + f"/{MODEL_CFG['SAMPLING_RATIO']}/{run_uid}/"

    if not os.path.exists(results_dir):
        os.makedirs(results_dir, exist_ok=True)

    if isinstance(obj, pd.DataFrame) or isinstance(obj, pd.Series):
        obj.to_csv(results_dir + filename + '.csv', index=False)
    else:
        with open(results_dir + filename + '.txt', 'w') as f:
            f.write(obj.__repr__())


def create_projection_from_dataset(
    sampling_ratio=MODEL_CFG['SAMPLING_RATIO'],
    graph_name=MODEL_CFG['PROJECTION_NAME'],
    undirected_relationship_types=['HAS_PARENT', 'HAS_SOTU', 'HAS_HOST'],
    enriched_features=False,
):
    graph_name = \
        f"{MODEL_CFG['PROJECTION_NAME']}_{sampling_ratio}"

    if gds.graph.exists(graph_name)['exists']:
        return gds.graph.get(graph_name)
        # gds.graph.drop(gds.graph.get(graph_name))

    if sampling_ratio < 1:
        dir_name = f"{DIR_CFG['DATASETS_DIR']}{graph_name}/"
    else:
        # Use full feature set if sampling_ratio is 1
        dir_name = f"{DIR_CFG['FEATURE_STORE_DIR']}"

    nodes = feature_queries.get_all_node_features(
        dir_name=dir_name,
        enriched_features=enriched_features,
    )
    relationships = feature_queries.get_all_relationship_features(
        dir_name=dir_name,
    )

    return gds.alpha.graph.construct(
        graph_name=graph_name,
        nodes=nodes,
        relationships=relationships,
        concurrency=4,
        undirected_relationship_types=undirected_relationship_types,
    )


def create_random_walk_subgraph(
    G,
    sampling_ratio=MODEL_CFG['SAMPLING_RATIO'],
    random_seed=MODEL_CFG['RANDOM_SEED'],
):
    graph_name = \
        f"{MODEL_CFG['PROJECTION_NAME']}_{sampling_ratio}"
    if gds.graph.exists(graph_name)['exists']:
        # return gds.graph.get(graph_name)
        gds.graph.drop(gds.graph.get(graph_name))

    G_dataset, _ = gds.alpha.graph.sample.rwr(
        graph_name=graph_name,
        from_G=G,
        concurrency=1,
        randomSeed=random_seed,
        samplingRatio=sampling_ratio,
        nodeLabelStratification=True,
        relationshipWeightProperty='weight',
        relationshipTypes=['HAS_PARENT', 'HAS_SOTU', 'HAS_HOST'],
    )
    return G_dataset


def create_lp_pipeline():
    pipeline_name = MODEL_CFG['PIPELINE_NAME']
    if gds.beta.pipeline.exists(pipeline_name)['exists']:
        gds.beta.pipeline.drop(gds.pipeline.get(pipeline_name))

    pipeline, _ = gds.beta.pipeline.linkPrediction.create(pipeline_name)

    # pipeline.addNodeProperty(
    #     procedure_name="degree",
    #     mutateProperty="degree",
    #     contextRelationshipTypes=['HAS_PARENT', 'HAS_SOTU'],
    #     contextNodeLabels=['SOTU'],
    # )
    pipeline.addFeature("l2", nodeProperties=["degree"])

    _ = pipeline.addNodeProperty(
        "beta.hashgnn",
        mutateProperty="hashGNN",
        iterations=4,
        heterogeneous=True,
        embeddingDensity=512,
        neighborInfluence=0.7,
        generateFeatures={'dimension': 6, 'densityLevel': 1},
        # binarizeFeatures={'dimension': 6, 'threshold': 32},
        # featureProperties=["features", "degree"],
        randomSeed=MODEL_CFG['RANDOM_SEED'],
        contextRelationshipTypes=['HAS_PARENT', 'HAS_SOTU'],
        contextNodeLabels=['SOTU'],  # 'Host'
    )
    pipeline.addFeature("hadamard", nodeProperties=["hashGNN"])

    # pipeline.addNodeProperty(
    #     procedure_name="fastRP",
    #     embeddingDimension=256,
    #     mutateProperty="fastRP",
    #     randomSeed=MODEL_CFG['RANDOM_SEED'],
    #     contextRelationshipTypes=['HAS_PARENT', 'HAS_SOTU'],
    #     contextNodeLabels=['SOTU'],
    # )
    # pipeline.addFeature("hadamard", nodeProperties=["fastRP"])

    # trainFraction is % of all nodes
    # testFraction is % of complement of trainFraction
    # feature-input is remainder used for generating features
    pipeline.configureSplit(
        trainFraction=MODEL_CFG['TRAIN_FRACTION'],
        testFraction=MODEL_CFG['TEST_FRACTION'],
        validationFolds=MODEL_CFG['VALIDATION_FOLDS'],
        negativeSamplingRatio=MODEL_CFG['NEGATIVE_SAMPLING_RATIO'],
    )
    return pipeline


def add_training_method(pipeline):
    # Add a random forest model with auto tuning over `penalty`
    pipeline.addLogisticRegression(penalty=(0.1, 2))
    # Add a random forest model with auto tuning over `maxDepth`
    pipeline.addRandomForest(maxDepth=(5, 10))
    # pipeline.addMLP(hiddenLayerSizes=[4, 2], penalty=1, patience=2)
    pipeline.addMLP(hiddenLayerSizes=[64, 16, 4], penalty=1, patience=2)
    return pipeline


def train_model(G, pipeline):
    model_name = MODEL_CFG['MODEL_NAME']
    if gds.beta.model.exists(model_name)['exists']:
        gds.beta.model.drop(gds.model.get(model_name))

    model, eval = pipeline.train(
        G=G,
        modelName=model_name,
        targetRelationshipType="HAS_HOST",
        sourceNodeLabel='Palmprint',
        targetNodeLabel='Taxon',
        randomSeed=MODEL_CFG['RANDOM_SEED'],
        metrics=["AUCPR", "OUT_OF_BAG_ERROR"],
        negativeClassWeight=MODEL_CFG['NEGATIVE_CLASS_WEIGHT'],
    )
    assert eval["trainMillis"] >= 0
    print("Train result:\n", eval['modelSelectionStats'])
    print("Model:\n", model)
    return model, eval


def stream_approx_predictions(G, model):
    predictions = model.predict_stream(
        G,
        topK=1,
        relationshipTypes=['HAS_HOST'],
        sampleRate=0.5,
        randomJoins=2,
        maxIterations=3,
        deltaThreshold=MODEL_CFG['PREDICTION_THRESHOLD'],
    )
    # predictions = predictions[
    #     predictions.probability >= MODEL_CFG['PREDICTION_THRESHOLD']]
    predictions = predictions.sort_values('probability')
    print(predictions)
    return predictions


def stream_exhaustive_predictions(G, model):
    predictions = model.predict_stream(
        G,
        topN=1,
        threshold=MODEL_CFG['PREDICTION_THRESHOLD'],
        relationshipTypes=['HAS_HOST'],
    )
    predictions = predictions.sort_values('probability')
    print(predictions)
    return predictions


def mutate_predictions(G, model):
    mutate_result = model.predict_mutate(
        G, topN=5, mutateRelationshipType="HAS_HOST")
    print(mutate_result)
    return mutate_result


def mutate_degree_property(G):
    gds.degree.mutate(
        G,
        mutateProperty="degree",
        orientation="UNDIRECTED",
    )
    gds.degree.mutate(
        G,
        mutateProperty="degreeWeighted",
        orientation="UNDIRECTED",
        relationshipWeightProperty="weight",
    )
    return G


# TODO: simplify code
# use alt conditional branching (nodes/rels, features/dataset)
def export_projection(G, destination='features'):
    if destination not in ['features', 'dataset']:
        raise Exception("Invalid destination arg")

    destination_dir = DIR_CFG['FEATURE_STORE_DIR']
    if destination == 'dataset':
        destination_dir = DIR_CFG['DATASETS_DIR'] + f"{G.name()}"

    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    node_mappings = [
        {
            'filename': 'palmprint_nodes.csv',
            'labels': ['Palmprint', 'SOTU'],
            'app_id': ['palmId'],
        },
        {
            'filename': 'taxon_nodes.csv',
            'labels': ['Host', 'Taxon'],
            'app_id': ['taxId'],
        },
    ]

    rel_mappings = [
        {
            'filename': 'has_parent_edges.csv',
            'types': ['HAS_PARENT'],
            'app_id': ['sourceNodeId', 'targetNodeId'],
        },
        {
            'filename': 'has_sotu_edges.csv',
            'types': ['HAS_SOTU'],
            'app_id': ['sourceNodeId', 'targetNodeId'],
        },
        {
            'filename': 'has_host_edges.csv',
            'types': ['HAS_HOST'],
        },
    ]

    for entity_type, entity_mappings in zip(
        ['nodes', 'rels'],
        [node_mappings, rel_mappings]
    ):
        for mapping in entity_mappings:
            if entity_type == 'nodes':
                stream_fnc = gds.graph.nodeProperties.stream
                stream_fnc_args = {
                    'node_properties': [
                        'features', 'degree', 'degreeWeighted'],
                    'node_labels': mapping['labels'],
                    'separate_property_columns': True,
                    'db_node_properties': mapping['app_id'],
                }
                merge_left_on = mapping['app_id']
                merge_right_on = ['appId']
            else:
                stream_fnc = gds.beta.graph.relationships.stream
                stream_fnc_args = {
                    'relationship_types': mapping['types']
                }
                merge_left_on = ['sourceNodeId', 'targetNodeId']
                merge_right_on = ['sourceNodeId', 'targetNodeId']

            df_fts = feature_queries.get_features_from_file(
                mapping['filename'])
            df_fts = df_fts.astype(str)
            df_projection = stream_fnc(G, **stream_fnc_args)
            df_projection = utils.df_to_ddf(df_projection)
            df_projection = df_projection.astype(str)

            how = 'left' if destination == 'dataset' else 'right'

            merged = df_projection.merge(
                df_fts,
                left_on=merge_left_on,
                right_on=merge_right_on,
                how=how,
                suffixes=('', '_dup'),
            )
            merged = merged.dropna()
            merged = merged.loc[:, ~merged.columns.str.contains('_dup$')]
            merged = merged.compute()

            merged.to_csv(
                destination_dir + '/' + mapping['filename'], index=False)
