import os
from collections import Counter

from datasources.neo4j import get_gds_connection
from queries import feature_queries, utils
from config.base import (
    DIR_CFG,
    MODEL_CFG,
    DATASET_CFG,
)


def run_query(query):
    gds = get_gds_connection()
    return gds.run_cypher(query)

### GraphRAG ###

def create_heterogenous_projection(projection_name):
    gds = get_gds_connection()
    if gds.graph.exists(projection_name)['exists']:
        gds.graph.drop(gds.graph.get(projection_name))

    # KG has defaultWeight attribute for all relationships with value 0.5
    default_weight_params = {'properties': { 'weight': { 'property': 'defaultWeight' } } } 
    projection = gds.graph.project(
        graph_name=projection_name,
        node_spec=['OpenVirome'],
        relationship_spec={
            'HAS_BIOPROJECT': { 'orientation': 'UNDIRECTED', **default_weight_params },
            'HAS_DISEASE_METADATA': { 'orientation': 'UNDIRECTED',  **default_weight_params },
            'HAS_HOST_METADATA': { 'orientation': 'UNDIRECTED',  **default_weight_params },
            'HAS_HOST_STAT': { 'orientation': 'UNDIRECTED', 'properties': { 'weight': { 'property': 'percentIdentity' } } },
            'HAS_INFERRED_TAXON': { 'orientation': 'UNDIRECTED',  'properties': { 'weight': { 'property': 'percentIdentity' } } },
            # 'HAS_PALMPRINT': { 'orientation': 'UNDIRECTED' },
            'HAS_PARENT': { 'orientation': 'UNDIRECTED',  **default_weight_params },
            'HAS_SOTU': { 'orientation': 'UNDIRECTED',  **default_weight_params },
            'HAS_TISSUE_METADATA': { 'orientation': 'UNDIRECTED',  **default_weight_params },
            'SEQUENCE_ALIGNMENT': { 'orientation': 'UNDIRECTED', 'properties': { 'weight': { 'property': 'percentIdentity' } } },
        }
    )
    return projection


def create_leiden_communities(projection_name, seed_property=None, edge_weight_property=None, max_levels=10):
    gds = get_gds_connection()
    projection = gds.graph.get(projection_name)
    communities = gds.leiden.stream(
        projection,
        relationshipWeightProperty=edge_weight_property,
        seedProperty=seed_property,
        minCommunitySize=2,
        maxLevels=max_levels,
        includeIntermediateCommunities=True,
        consecutiveIds=False,
        gamma=5.0, # Default: 1.0, Resolution parameter for modularity, higher -> more communities
        theta=0.01, # Default: 0.01, Randomness when breaking communities
        tolerance=0.0001, # Default: 0.0001, Min change in modularity between iterations
    )
    if 'componentId' in communities.columns:
        communities['communityId'] = communities['componentId']
    return communities


def get_sra_node_mapping():
    query = """
        MATCH (n:SRA)
        RETURN n.runId as runId, id(n) as nodeId
    """
    df = run_query(query)
    return df


def get_run_to_community_df(communities, data_dir):
    run_node_mapping = get_sra_node_mapping()
    run_node_mapping = run_node_mapping.set_index('nodeId')

    selected_community = communities.copy()
    target_level = -1
    selected_community['communityId'] = communities['intermediateCommunityIds'].apply(lambda x: x[target_level])
    selected_community = selected_community[['nodeId', 'communityId']]


    run_to_community_df = run_node_mapping.merge(selected_community, left_on='nodeId', right_on='nodeId', how='left')
    run_to_community_df = run_to_community_df[['runId', 'communityId']]
    run_to_community_df = run_to_community_df.rename(columns={'communityId': 'community_id', 'runId': 'run'})

    # drop communities with only 1 member
    community_counts = run_to_community_df['community_id'].value_counts()
    single_communities = community_counts[community_counts == 1].index
    run_to_community_df = run_to_community_df[~run_to_community_df['community_id'].isin(single_communities)]
    run_to_community_df = run_to_community_df.dropna()
    run_to_community_df['community_id'] = run_to_community_df['community_id'].astype(int)

    print(run_to_community_df['community_id'].nunique())
    print(run_to_community_df['community_id'].value_counts().describe())
    run_to_community_df.to_csv(f'{data_dir}/run_to_community.csv', index=False)
    return run_to_community_df


def get_top_nested(data, k):
    counter = Counter()
    for key in data:
        for sub_key in key:
            counter.update(sub_key)
    top_k = counter.most_common(k)
    top_k = [x[0] for x in top_k]
    return top_k


def get_sra_data(run_str):
    query = f'''
        MATCH (run:SRA)-[:HAS_BIOPROJECT]->(bioproject:BioProject)
        WHERE run.runId in [{run_str}]
        RETURN
            COLLECT(DISTINCT run.bioSampleTitle) as bioSampleTitles,
            COLLECT(DISTINCT run.bioSampleGeoAttributeValues) as geoAttributeValues,
            COLLECT(DISTINCT run.bioSampleGeoBiomeName) as geoBiomeNames,
            COLLECT(DISTINCT bioproject.bioProject) as bioproject,
            COLLECT(DISTINCT bioproject.title) as bioProjectTitles,
            COLLECT(DISTINCT bioproject.description) as bioProjectDescriptions
    '''
    response = run_query(query)
    return response

def get_stat_host_counts(run_str, limit=10):
    query = f'''
        MATCH (run:SRA)-[:HAS_HOST_STAT]->(host_stat:Taxon)
        WHERE run.runId in [{run_str}]
        RETURN host_stat.taxOrder as statOrganism, COUNT(run) as count
        LIMIT {limit}
    '''
    response = run_query(query)
    return response

def get_host_label_counts(run_str, limit=10):
    query = f'''
        MATCH (run:SRA)-[:HAS_HOST_METADATA]->(host_label:Taxon)
        WHERE run.runId in [{run_str}]
        RETURN 
            CASE host_label.rank
                    WHEN 'species' THEN host_label.taxSpecies 
                    WHEN 'genus' THEN host_label.taxGenus
                    WHEN 'family' THEN host_label.taxFamily
                    WHEN 'order' THEN host_label.taxOrder
                    WHEN 'phylum' THEN host_label.taxPhylum
                    WHEN 'kingdom' THEN host_label.taxKingdom
                    ELSE 'N/A'
            END as label, COUNT(run) as count
        LIMIT {limit}
    '''
    response = run_query(query)
    return response

def get_disease_counts(run_str, limit=10):
    query = f'''
        MATCH (run:SRA)-[:HAS_DISEASE_METADATA]->(disease:Disease)
        WHERE run.runId in [{run_str}]
        RETURN disease.name as disease, COUNT(run) as count
        LIMIT {limit}
    '''
    response = run_query(query)
    return response

def get_tissue_counts(run_str, limit=10):
    query = f'''
        MATCH (run:SRA)-[:HAS_TISSUE_METADATA]->(tissue:Tissue)
        WHERE run.runId in [{run_str}]
        RETURN tissue.scientificName as tissue, COUNT(run) as count
        LIMIT {limit}
    '''
    response = run_query(query)
    return response

def get_sotu_species_counts(run_str, limit=15):
    query = f'''
        MATCH (run:SRA)-[r:HAS_SOTU]->(sotu:SOTU)
        WHERE run.runId in [{run_str}]
        AND r.OpenVirome = true
        RETURN sotu.taxSpecies as species, COUNT(run) as count
        LIMIT 15
    '''
    response = run_query(query)
    return response


def get_sotu_family_counts(run_str, limit=15):
    query = f'''
        MATCH (run:SRA)-[r:HAS_SOTU]->(sotu:SOTU)
        WHERE run.runId in [{run_str}]
        AND r.OpenVirome = true
        RETURN sotu.taxFamily as family, COUNT(run) as count
        LIMIT {limit}
    '''
    response = run_query(query)
    return response


def get_max_biosafety_level(run_str):
    query = f'''
        MATCH (run:SRA)-[:HAS_HOST_METADATA]->(host_label:Taxon)
        WHERE run.runId in [{run_str}]
        WITH run, host_label
        OPTIONAL MATCH (run:SRA)-[:HAS_HOST_STAT]->(host_stat:Taxon)
        WITH run, host_label, host_stat
        OPTIONAL MATCH (run)-[r:HAS_SOTU]->(sotu:SOTU)-[:HAS_INFERRED_TAXON]->(sotu_taxon:Taxon)
        WHERE r.OpenVirome = true
        WITH run, host_label, host_stat, sotu_taxon
        RETURN
            CASE apoc.meta.cypher.type(host_label.AnimalRiskGroup)
                WHEN 'NULL' THEN 'N/A'
                WHEN 'FLOAT' THEN 'N/A'
                ELSE host_label.AnimalRiskGroup
            END as host_label_animal_risk_groups,
            CASE apoc.meta.cypher.type(host_label.HumanRiskGroup)
                WHEN 'NULL' THEN 'N/A'
                WHEN 'FLOAT' THEN 'N/A'
                ELSE host_label.HumanRiskGroup
            END as host_label_human_risk_groups,
            CASE apoc.meta.cypher.type(host_stat.AnimalRiskGroup)
                WHEN 'NULL' THEN 'N/A'
                WHEN 'FLOAT' THEN 'N/A'
                ELSE host_stat.AnimalRiskGroup
            END as host_stat_animal_risk_groups,
            CASE apoc.meta.cypher.type(host_stat.HumanRiskGroup)
                WHEN 'NULL' THEN 'N/A'
                WHEN 'FLOAT' THEN 'N/A'
                ELSE host_stat.HumanRiskGroup
            END as host_stat_human_risk_groups,
            CASE apoc.meta.cypher.type(sotu_taxon.AnimalRiskGroup)
                WHEN 'NULL' THEN 'N/A'
                WHEN 'FLOAT' THEN 'N/A'
                ELSE sotu_taxon.AnimalRiskGroup
            END as sotu_taxon_animal_risk_groups,
            CASE apoc.meta.cypher.type(sotu_taxon.HumanRiskGroup)
                WHEN 'NULL' THEN 'N/A'
                WHEN 'FLOAT' THEN 'N/A'
                ELSE sotu_taxon.HumanRiskGroup
            END as sotu_taxon_human_risk_groups
    '''
    response = run_query(query)
    # Get the max biosafety level from the response, RG4 > RG3 > RG2 > RG1
    bsl_priority = {'RG4': 4, 'RG3': 3, 'RG2': 2, 'RG1': 1, 'N/A': 0}
    max_bsl = 'N/A'
    for row in response:
        for value in response[row]:
            if value in bsl_priority:
                if bsl_priority[value] > bsl_priority[max_bsl]:
                    max_bsl = value
    return max_bsl


### Link Prediction ###


def create_projection_from_dataset(
    sampling_ratio=MODEL_CFG['SAMPLING_RATIO'],
    dataset_cfg=DATASET_CFG,
    model_cfg=MODEL_CFG,
    start_nodes=None
):
    graph_name = \
        f"{model_cfg['PROJECTION_NAME']}_{sampling_ratio}"
    gds = get_gds_connection()
    if gds.graph.exists(graph_name)['exists']:
        # return gds.graph.get(graph_name)
        gds.graph.drop(gds.graph.get(graph_name))

    dir_name = f"{DIR_CFG['DATASETS_DIR']}{sampling_ratio}/"
    if not os.path.exists(dir_name) or start_nodes:
        print("Using neo4j query cache with base features")
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

    if start_nodes:
        nodes, relationships = filter_dataset_by_start_nodes(
            start_nodes,
            nodes,
            relationships,
            undirected_relationship_types,
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
  
    if start_nodes:
        graph_name = \
        f"{model_cfg['PROJECTION_NAME']}_{sampling_ratio}_start1"
    
    gds = get_gds_connection()
    if gds.graph.exists(graph_name)['exists']:
        # return gds.graph.get(graph_name)
        gds.graph.drop(gds.graph.get(graph_name))

    relationship_types = list(
        map(
            (lambda cfg: cfg['TYPES'][0]),
            DATASET_CFG['REL_TYPES']
        )
    )
    # gds.alpha.graph.sample.rwr 
    G_dataset, _ = gds.graph.sample.cnarw(
        graph_name=graph_name,
        from_G=G,
        concurrency=1 if start_nodes is None else 4,
        randomSeed=model_cfg['RANDOM_SEED'] if start_nodes is None else None,
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
    gds = get_gds_connection()
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
    gds = get_gds_connection()
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
                    'node_properties': ['features', 'FastRP_embedding'],
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

            df_attributes = feature_queries.get_features_from_file(
                mapping['FILE_NAME'],
                DIR_CFG['QUERY_CACHE_DIR'],
            )
            df_attributes = df_attributes.astype(str)
            df_projection = stream_fnc(G, **stream_fnc_args)
            df_projection = utils.df_to_ddf(df_projection)
            df_projection = df_projection.astype(str)

            merged = df_projection.merge(
                df_attributes,
                left_on=merge_left_on,
                right_on=merge_right_on,
                how='left',
                suffixes=('', '_dup'),
            )
            merged = merged.dropna()
            merged = merged.loc[:, ~merged.columns.str.contains('_dup$')]
            merged = merged.compute()

            merged.to_csv(destination_dir + mapping['FILE_NAME'], index=False)


def generate_shallow_embeddings(
    G,
    model_cfg=MODEL_CFG,
):
    gds = get_gds_connection()
    return gds.fastRP.mutate(
        G=G,
        nodeLabels=['Taxon', 'Tissue', 'SOTU'],
        relationshipTypes=['HAS_PARENT', 'SEQUENCE_ALIGNMENT', 'HAS_INFERRED_TAXON', 'HAS_TISSUE_METADATA'],
        randomSeed=MODEL_CFG['RANDOM_SEED'],
        embeddingDimension=128,
        featureProperties=['features'],
        mutateProperty='FastRP_embedding',
        relationshipWeightProperty='weight',
    )
    # gds.hashgnn.mutate(
    #     G=G,
    #     nodeLabels=['Taxon', 'Tissue', 'SOTU'],
    #     relationshipTypes=['HAS_PARENT', 'SEQUENCE_ALIGNMENT', 'HAS_INFERRED_TAXON', 'HAS_TISSUE_METADATA'],
    #     randomSeed=MODEL_CFG['RANDOM_SEED'],
    #     generateFeatures={
    #         'dimension': 256, # dimension of the embedding vector
    #         'densityLevel': 1, # number of initial values equalling 1
    #     },
    #     iterations=5, # maximum number of hops
    #     embeddingDensity=128,
    #     neighborInfluence=1.0,
    #     mutateProperty='FastRP_embedding',
    # )


def filter_dataset_by_start_nodes(
    start_nodes,
    nodes,
    relationships,
    undirected_relationship_types
):
    excl_mask = nodes.loc[
        (nodes.labels.apply(lambda x: 'SOTU' in x)) &
        (~nodes['nodeId'].isin(start_nodes))
    ]
    nodes = nodes[~nodes['nodeId'].isin(excl_mask.nodeId)]

    sotu_in_source = [
        'HAS_HOST_STAT',
        'HAS_INFERRED_TAXON',
        'HAS_INFERRED_TAXON',
        'HAS_TISSUE_METADATA',
    ]
    sotu_in_source_and_target = [
        'SEQUENCE_ALIGNMENT'
    ]

    for rel_type in sotu_in_source:
        excl_mask = relationships.loc[
            (relationships['relationshipType'] == rel_type) &
            (~relationships['sourceNodeId'].isin(start_nodes))
        ]
        relationships = relationships[~relationships.index.isin(excl_mask.index)]

    for rel_type in sotu_in_source_and_target:
        excl_mask = relationships.loc[
            (relationships['relationshipType'] == rel_type) &
            (~relationships['sourceNodeId'].isin(start_nodes) | ~relationships['targetNodeId'].isin(start_nodes)) 
        ]
        relationships = relationships[~relationships.index.isin(excl_mask.index)]

    return nodes, relationships
