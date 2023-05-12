import ast
import os

import pandas as pd

from datasources.neo4j import gds 


CONFIG = {
    'FEATURE_STORE_DIR': './data/features/',
    'DATASET_DIR': './data/datasets/',
    'MODELS_DIR': './data/models/',
    'FULL_PROJECTION_NAME': 'palmprint-host-full',
    'DATASET_PROJECTION_NAME': 'palmprint-host-dataset',
    'PIPELINE_NAME': 'lp-pipeline',
    'MODEL_NAME': 'lp-model',
    'RANDOM_SEED': 42,
    'SAMPLING_RATIO': 0.1,
}

def read_df_from_disk(file_path=''):
    try:
        df = pd.read_csv(file_path, index_col=0)
        print('Using local file for dataframe: ', file_path)
        return df
    except:
        print('No local file found: ', file_path)
        return None


def get_dataset_from_cache():
    graph_name = CONFIG['DATASET_PROJECTION_NAME']
    if gds.graph.exists(graph_name)['exists']:
        return gds.graph.get(graph_name)

    sampling_ratio = CONFIG['SAMPLING_RATIO']
    random_seed = CONFIG['RANDOM_SEED']
    nodes = read_df_from_disk(
        CONFIG['DATASET_DIR'] + f"palmprint_host_dataset_nodes_{sampling_ratio}_{random_seed}.csv"
    )
    relationships = read_df_from_disk(
        CONFIG['DATASET_DIR'] + f"palmprint_host_dataset_relationships_{sampling_ratio}_{random_seed}.csv"
    )
    if not nodes or not relationships:
        return None

    return gds.alpha.graph.construct(
        graph_name=graph_name,
        nodes=nodes,
        relationships=relationships,
        concurrency=4,
        undirected_relationship_types=['HAS_PARENT', 'HAS_SOTU', 'HAS_HOST'],
    )


def merge_and_unserialize(file_paths):
    if not file_paths:
        return pd.DataFrame()

    df = pd.concat([
        read_df_from_disk(file_path)
        for file_path
        in file_paths
    ]).drop_duplicates()

    # convert labels to list (must be done after concatenation)
    if 'labels' in df:
        df['labels'] = df['labels'].apply(lambda x: ast.literal_eval(x))
    return df


def create_palmprint_host_projection():
    graph_name = CONFIG['FULL_PROJECTION_NAME']
    if gds.graph.exists(graph_name)['exists']:
        gds.graph.drop(gds.graph.get(graph_name))

    dir_name = CONFIG['FEATURE_STORE_DIR']

    node_file_paths = [
        dir_name + 'n4j_palmprint_nodes.csv',
        dir_name + 'n4j_taxon_nodes.csv',
    ]
    nodes = merge_and_unserialize(node_file_paths)
    relationship_file_paths = [
        dir_name + 'n4j_has_sotu_edges.csv',
        dir_name + 'n4j_has_parent_edges.csv',
        dir_name + 'n4j_has_host_edges.csv',
    ]
    relationships = merge_and_unserialize(relationship_file_paths)
    return gds.alpha.graph.construct(
        graph_name=graph_name,
        nodes=nodes,
        relationships=relationships,
        concurrency=4,
        undirected_relationship_types=['HAS_PARENT', 'HAS_SOTU', 'HAS_HOST'],
    )


def create_subgraph_dataset(G):
    graph_name = CONFIG['DATASET_PROJECTION_NAME']
    if gds.graph.exists(graph_name)['exists']:
        gds.graph.drop(gds.graph.get(graph_name))

    random_seed = CONFIG['RANDOM_SEED']
    sampling_ratio = CONFIG['SAMPLING_RATIO']

    G_dataset, _ = gds.alpha.graph.sample.rwr(
        graph_name=graph_name,
        from_G=G,
        concurrency=1,
        randomSeed=random_seed, # can only use if concurrency=1
        samplingRatio=sampling_ratio,
        nodeLabelStratification=True,
    )
    return G_dataset


def store_subgraph_dataset(G):
    sampling_ratio = CONFIG['SAMPLING_RATIO']
    random_seed = CONFIG['RANDOM_SEED']

    if not os.path.exists(CONFIG['DATASET_DIR']):
        os.makedirs(CONFIG['DATASET_DIR'])

    df_dataset_relationships = gds.beta.graph.relationships.stream(G)
    df_dataset_relationships.to_csv(
        CONFIG['DATASET_DIR'] + f"palmprint_host_dataset_relationships_{sampling_ratio}_{random_seed}.csv"
    )
    df_dataset_nodes = gds.graph.nodeProperty.stream(
        G,
        node_properties=['*'],
        nodeLabels=['*'],
        separate_property_columns=True,
    )
    df_dataset_nodes.to_csv(
        CONFIG['DATASET_DIR'] + f"palmprint_host_dataset_nodes_{sampling_ratio}_{random_seed}.csv"
    )


def log_graph(G):
    print('Node counts:\n', G.node_count())
    print('Node labels:\n', G.node_labels())
    print('Node properties:\n', G.node_properties())
    print('Relationship count:\n', G.relationship_count())
    print('Relationship types:\n', G.relationship_types())
    print('Relationship properties:\n', G.relationship_properties())


def create_lp_pipeline():
    pipeline_name = CONFIG['PIPELINE_NAME']
    if gds.beta.pipeline.exists(pipeline_name)['exists']:
        gds.beta.pipeline.drop(gds.pipeline.get(pipeline_name))
    
    pipeline, _ = gds.beta.pipeline.linkPrediction.create(pipeline_name)
    pipeline.addNodeProperty(
        procedure_name="fastRP",
        embeddingDimension=256,
        mutateProperty="embedding",
        randomSeed=CONFIG['RANDOM_SEED'],
        contextRelationshipTypes=['HAS_PARENT', 'HAS_SOTU'],
        contextNodeLabels=['Host', 'SOTU'],
    )
    pipeline.addFeature("hadamard", nodeProperties=["embedding"])
    
    # Add a Degree Centrality feature to the pipeline
    pipeline.addNodeProperty("degree", mutateProperty="rank")
    # pipeline.selectFeatures("rank")
    
    # pipeline.configureSplit(trainFraction=0.6, testFraction=0.25, validationFolds=3)
    pipeline.configureSplit(trainFraction=0.25, testFraction=0.0625, validationFolds=3)
    return pipeline

def add_training_method(pipeline):
    # pipeline.addLogisticRegression(penalty=(0.1, 2))
    # Add a random forest model with tuning over `maxDepth`
    # pipe.addRandomForest(maxDepth=(2, 20))
    pipeline.addMLP(hiddenLayerSizes=[4, 2], penalty=1, patience=2)
    # pipeline.addMLP(hiddenLayerSizes=[64, 16, 4], penalty=0.1, patience=2)
    return pipeline


def log_pipeline(pipeline):
    print('Number of steps:\n', len(pipeline.feature_steps()))
    print('Steps:\n', pipeline.feature_steps())


def train_model(G, pipeline):
    model_name = CONFIG['MODEL_NAME']
    if gds.beta.model.exists(model_name)['exists']:
        gds.beta.model.drop(gds.model.get(model_name))
    
    model, train_result = pipeline.train(
        G=G,
        modelName=model_name,
        targetRelationshipType="HAS_HOST",
        sourceNodeLabel='Palmprint',
        targetNodeLabel='Taxon',
        randomSeed=CONFIG['RANDOM_SEED'],
        metrics=["AUCPR", "OUT_OF_BAG_ERROR"],
    )
    assert train_result["trainMillis"] >= 0
    print("Train result:\n", train_result['modelSelectionStats'])
    print("Model:\n", model)
    return model, train_result


def store_model_results(model, train_result):
    model_dir = CONFIG['MODELS_DIR'] + f"link_prediction/{CONFIG['SAMPLING_RATIO']}/"
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    train_result.to_csv(
        model_dir + f"train_results.csv"
    )
    # Not available for unlicensed GDS.
    # gds.alpha.model.store(model=model)


def stream_predictions(G, model):
    predictions = model.predict_stream(G, topN=3, threshold=0.5)
    print(predictions)
    model_dir = CONFIG['MODELS_DIR'] + f"link_prediction/{CONFIG['SAMPLING_RATIO']}/"
    predictions.to_csv(
        model_dir + f"train_results.csv"
    )
    return predictions


def mutate_predictions(G, model):
    mutate_result = model.predict_mutate(G, topN=5, mutateRelationshipType="HAS_HOST")
    print(mutate_result)
    return mutate_result
