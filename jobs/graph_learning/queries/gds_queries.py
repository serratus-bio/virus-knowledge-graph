import os

from datasources.neo4j import gds
from queries import feature_queries, utils
from config.base import (
    DIR_CFG,
    MODEL_CFG,
    DATASET_CFG,
)


def run_query(query):
    return gds.run_cypher(query)


def create_projection_from_dataset(
    sampling_ratio=MODEL_CFG['SAMPLING_RATIO'],
    dataset_cfg=DATASET_CFG,
    model_cfg=MODEL_CFG,
):
    graph_name = \
        f"{model_cfg['PROJECTION_NAME']}_{sampling_ratio}"

    if gds.graph.exists(graph_name)['exists']:
        return gds.graph.get(graph_name)
        # gds.graph.drop(gds.graph.get(graph_name))

    if sampling_ratio < 1:
        dir_name = f"{DIR_CFG['DATASETS_DIR']}{sampling_ratio}/"
    else:
        # Use full feature set if sampling_ratio is 1
        # dir_name = f"{DIR_CFG['FEATURE_STORE_DIR']}"
        dir_name = f"{DIR_CFG['QUERY_CACHE_DIR']}"

    nodes = feature_queries.get_all_node_features(
        dir_name=dir_name,
        dataset_cfg=dataset_cfg,
    )
    relationships = feature_queries.get_all_relationship_features(
        dir_name=dir_name,
        dataset_cfg=dataset_cfg,
    )

    undirected_relationship_types = list(
        map(
            (lambda cfg: cfg['TYPES'][0]),
            dataset_cfg['REL_TYPES']
        )
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
    model_cfg=MODEL_CFG,
    start_nodes=None
):
    graph_name = \
        f"{model_cfg['PROJECTION_NAME']}_{sampling_ratio}"
    if gds.graph.exists(graph_name)['exists']:
        # return gds.graph.get(graph_name)
        gds.graph.drop(gds.graph.get(graph_name))

    relationship_types = list(
        map(
            (lambda cfg: cfg['TYPES'][0]),
            DATASET_CFG['REL_TYPES']
        )
    )

    G_dataset, _ = gds.alpha.graph.sample.rwr(
        graph_name=graph_name,
        from_G=G,
        concurrency=1,
        randomSeed=model_cfg['RANDOM_SEED'],
        samplingRatio=sampling_ratio,
        nodeLabelStratification=True,
        relationshipWeightProperty='weight',
        relationshipTypes=relationship_types,
        startNodes=start_nodes,
    )
    return G_dataset


def create_lp_pipeline(
        dataset_cfg=DATASET_CFG,
        model_cfg=MODEL_CFG,
):
    pipeline_name = model_cfg['PIPELINE_NAME']
    if gds.beta.pipeline.exists(pipeline_name)['exists']:
        gds.beta.pipeline.drop(gds.pipeline.get(pipeline_name))

    pipeline, _ = gds.beta.pipeline.linkPrediction.create(pipeline_name)

    all_relationship_types = list(
        map(
            (lambda cfg: cfg['TYPES'][0]),
            dataset_cfg['REL_TYPES']
        )
    )
    context_relationship_types = list(
        filter(lambda x: x !=
               dataset_cfg['TARGET_REL_TYPE'],
               all_relationship_types)
    )
    all_node_labels = list(
        map(
            (lambda cfg: cfg['LABELS']),
            dataset_cfg['NODE_TYPES']
        )
    )
    all_node_labels = [
        item for sublist in all_node_labels
        for item in sublist
    ]
    context_node_labels = list(
        filter(
            (lambda x: x not in ['SOTU', 'Palmprint', 'Taxon']),
            all_node_labels
        )
    )

    # pipeline.addNodeProperty(
    #     procedure_name="pageRank",
    #     mutateProperty="pageRank",
    #     dampingFactor=0.85,
    #     tolerance=0.0000001,
    #     contextRelationshipTypes=context_relationship_types,
    #     contextNodeLabels=context_node_labels,
    # )
    # pipeline.addFeature("l2", nodeProperties=["pageRank"])

    # pipeline.addNodeProperty(
    #     procedure_name="degree",
    #     mutateProperty="degree",
    #     contextRelationshipTypes=context_relationship_types,
    #     contextNodeLabels=context_node_labels,
    # )
    # pipeline.addFeature("l2", nodeProperties=["degree"])

    _ = pipeline.addNodeProperty(
        "beta.hashgnn",
        mutateProperty="hashGNN",
        iterations=4,
        heterogeneous=True,
        embeddingDensity=512,
        neighborInfluence=0.7,
        binarizeFeatures={'dimension': 6, 'threshold': 32},
        # generateFeatures={'dimension': 6, 'densityLevel': 1},
        # featureProperties=["features", "degree", "pageRank"],
        featureProperties=["features"],
        randomSeed=MODEL_CFG['RANDOM_SEED'],
        contextRelationshipTypes=context_relationship_types,
        contextNodeLabels=context_node_labels,
    )
    pipeline.addFeature("hadamard", nodeProperties=["hashGNN"])

    # pipeline.addNodeProperty(
    #     procedure_name="fastRP",
    #     embeddingDimension=256,
    #     mutateProperty="fastRP",
    #     randomSeed=MODEL_CFG['RANDOM_SEED'],
    #     featureProperties=["features"],
    #     contextRelationshipTypes=context_relationship_types,
    #     contextNodeLabels=context_node_labels,
    # )
    # pipeline.addFeature("hadamard", nodeProperties=["fastRP"])

    # pipeline.addNodeProperty(
    #     procedure_name="graphSage",
    #     mutateProperty="graphSage",
    #     contextRelationshipTypes=context_relationship_types,
    #     contextNodeLabels=context_node_labels,
    # )
    # pipeline.addFeature("hadamard", nodeProperties=["graphSage"])

    # trainFraction is % of all nodes
    # testFraction is % of complement of trainFraction
    # feature-input is remainder used for generating features
    pipeline.configureSplit(
        trainFraction=model_cfg['TRAIN_FRACTION'],
        testFraction=model_cfg['TEST_FRACTION'],
        validationFolds=model_cfg['VALIDATION_FOLDS'],
        negativeSamplingRatio=model_cfg['NEGATIVE_SAMPLING_RATIO'],
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


def train_model(G, pipeline, model_cfg=MODEL_CFG, dataset_cfg=DATASET_CFG):
    model_name = model_cfg['MODEL_NAME']
    if gds.beta.model.exists(model_name)['exists']:
        gds.beta.model.drop(gds.model.get(model_name))

    model, eval = pipeline.train(
        G=G,
        modelName=model_name,
        targetRelationshipType=dataset_cfg['TARGET_REL_TYPE'][0],
        sourceNodeLabel='Palmprint',
        targetNodeLabel='Taxon',
        randomSeed=model_cfg['RANDOM_SEED'],
        metrics=["AUCPR", "OUT_OF_BAG_ERROR"],
        negativeClassWeight=model_cfg['NEGATIVE_CLASS_WEIGHT'],
    )
    assert eval["trainMillis"] >= 0
    print("Train result:\n", eval['modelSelectionStats'])
    print("Model:\n", model)
    return model, eval


def map_ids_to_predictions(predictions, dataset_cfg=DATASET_CFG,):
    node_mapping = feature_queries.get_node_mapping(dataset_cfg)
    predictions = predictions.merge(
        node_mapping,
        left_on='node1',
        right_on='nodeId',
        how='left',
    )
    predictions = predictions.rename({'appId': 'sourceAppId'}, axis=1)
    predictions = predictions.merge(
        node_mapping,
        left_on='node2',
        right_on='nodeId',
        how='left',
    )
    predictions = predictions.rename({'appId': 'targetAppId'}, axis=1)
    predictions = predictions.drop(
        predictions.filter(regex='^nodeId').columns, axis=1)
    return predictions


def stream_approx_predictions(
        G,
        model,
        model_cfg=MODEL_CFG,
        dataset_cfg=DATASET_CFG,
):
    predictions = model.predict_stream(
        G,
        topK=1,
        relationshipTypes=dataset_cfg['TARGET_REL_TYPE'],
        sampleRate=0.5,
        randomJoins=2,
        maxIterations=3,
        deltaThreshold=model_cfg['PREDICTION_THRESHOLD'],
    )
    predictions = predictions.sort_values('probability')
    predictions = map_ids_to_predictions(predictions, dataset_cfg)
    print(predictions)
    return predictions


def stream_exhaustive_predictions(
        G,
        model,
        model_cfg=MODEL_CFG,
        dataset_cfg=DATASET_CFG
):
    predictions = model.predict_stream(
        G,
        topN=1,
        threshold=model_cfg['PREDICTION_THRESHOLD'],
        relationshipTypes=dataset_cfg['TARGET_REL_TYPE'],
    )
    predictions = predictions.sort_values('probability')
    predictions = map_ids_to_predictions(predictions, dataset_cfg)
    print(predictions)
    return predictions


def mutate_predictions(G, model, dataset_cfg=DATASET_CFG):
    mutate_result = model.predict_mutate(
        G, topN=5, mutateRelationshipType=dataset_cfg["TARGET_REL_TYPE"])
    print(mutate_result)
    return mutate_result


# TODO: simplify code
# use alt conditional branching (nodes/rels, features/dataset)
def export_projection(G, export_prefix=1, dataset_cfg=DATASET_CFG):

    destination_dir = f"{DIR_CFG['DATASETS_DIR']}{export_prefix}/"

    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    for entity_type, entity_mappings in zip(
        ['nodes', 'rels'],
        [dataset_cfg['NODE_TYPES'], dataset_cfg['REL_TYPES']]
    ):
        for mapping in entity_mappings:
            if entity_type == 'nodes':
                stream_fnc = gds.graph.nodeProperties.stream
                stream_fnc_args = {
                    'node_properties': ['features'],
                    'node_labels': mapping['LABELS'],
                    'separate_property_columns': True,
                    'db_node_properties': mapping['APP_ID'],
                }
                merge_left_on = mapping['APP_ID']
                merge_right_on = ['appId']
            else:
                stream_fnc = gds.beta.graph.relationships.stream
                stream_fnc_args = {
                    'relationship_types': mapping['TYPES']
                }
                merge_left_on = ['sourceNodeId', 'targetNodeId']
                merge_right_on = ['sourceNodeId', 'targetNodeId']

            df_fts = feature_queries.get_features_from_file(
                mapping['FILE_NAME'])
            df_fts = df_fts.astype(str)
            df_projection = stream_fnc(G, **stream_fnc_args)
            df_projection = utils.df_to_ddf(df_projection)
            df_projection = df_projection.astype(str)

            merged = df_projection.merge(
                df_fts,
                left_on=merge_left_on,
                right_on=merge_right_on,
                how='left',
                suffixes=('', '_dup'),
            )
            merged = merged.dropna()
            merged = merged.loc[:, ~merged.columns.str.contains('_dup$')]
            merged = merged.compute()

            merged.to_csv(
                destination_dir + mapping['FILE_NAME'], index=False)



def create_homogenous_projection(graph_name='homogenous-graph'):
    if gds.graph.exists(graph_name)['exists']:
        return gds.graph.get(graph_name)
        gds.graph.drop(gds.graph.get(graph_name))

    projection = gds.graph.project(
        graph_name=graph_name,
        node_spec=[
            'Taxon',
            'Tissue',
            'SOTU',
        ],
        relationship_spec={
            'HAS_PARENT': {'orientation': 'UNDIRECTED'},
            'SEQUENCE_ALIGNMENT': {'orientation': 'UNDIRECTED'},
        },
    )
    return projection


def generate_shallow_embeddings(
    G,
    model_cfg=MODEL_CFG,
):
    return gds.fastRP.mutate(
        G=G,
        nodeLabels=['Taxon', 'Tissue', 'SOTU'],
        relationshipTypes=['HAS_PARENT', 'SEQUENCE_ALIGNMENT', 'HAS_INFERRED_TAXON', 'HAS_TISSUE_METADATA'],
        randomSeed=MODEL_CFG['RANDOM_SEED'],
        embeddingDimension=128,
        featureProperties='features',
        mutateProperty='features',
        relationshipWeightProperty='weight',
    )


# TODO: mutate projection then use export_projection instead of stream
def generate_shallow_embeddings_alt():
    random_seed = 42
    projection_name = 'homogenous'

    projection_cfgs = [
        {
            'node_labels': ['Taxon'],
            'relationship_types': ['HAS_PARENT'],
            'appId': 'taxId',
        },
        {
            'node_labels': ['Tissue'],
            'relationship_types': ['HAS_PARENT'],
            'appId': 'btoId',
        },
        {
            'node_labels': ['SOTU'],
            'relationship_types': ['SEQUENCE_ALIGNMENT'],
            'appId': 'palmId',
        },
    ]

    create_homogenous_projection(projection_name)

    for cfg in projection_cfgs:
        cur_type = cfg['node_labels'][0]
        
        gds.fastRP.mutate(
            G=gds.graph.get(projection_name),
            nodeLabels=cfg['node_labels'],
            relationshipTypes=cfg['relationship_types'],
            randomSeed=random_seed,
            embeddingDimension=128,
            mutateProperty='features'
            # relationshipWeightProperty='weight',
        )
        df_emb = utils.df_to_ddf(df_emb)
        filename = 'FastRP_' + cur_type + '.csv'
        df_emb.to_csv(DIR_CFG['EMBEDDINGS_DIR'] + filename, single_file=True, index=False)

        # df_emb = gds.hashgnn.stream(
        #     G=gds.graph.get(projection_name),
        #     nodeLabels=cfg['node_labels'],
        #     relationshipTypes=cfg['relationship_types'],
        #     randomSeed=random_seed,
        #     generateFeatures={
        #         'dimension': 256, # dimension of the embedding vector
        #         'densityLevel': 1, # number of initial values equalling 1
        #     },
        #     iterations=5, # maximum number of hops
        #     embeddingDensity=128,
        #     neighborInfluence=1.0,
        # )
        # df_emb = utils.df_to_ddf(df_emb)
        # filename = 'HashGNN_' + cur_type + '.csv'
        # df_emb.to_csv(DIR_CFG['EMBEDDINGS_DIR'] + filename, single_file=True, index=False)

    gds.graph.drop(gds.graph.get(projection_name))