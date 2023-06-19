DATASET_VERSION_1 = 'data-v1'
DATASET_VERSION_2 = 'data-v2'
DATASET_VERSION_3 = 'data-v3'
DATASET_VERSION_4 = 'data-v4'


NODE_PALMPRINT = {
    'FILE_NAME': 'palmprint_nodes.csv',
    'LABELS': ['Palmprint', 'SOTU'],
    'APP_ID': ['palmId'],
}
NODE_SOTU = {
    'FILE_NAME': 'sotu_nodes.csv',
    'LABELS': ['SOTU'],
    'APP_ID': ['palmId'],
}
NODE_TAXON = {
    'FILE_NAME': 'taxon_nodes.csv',
    'LABELS': ['Host', 'Taxon'],
    'APP_ID': ['taxId'],
}
NODE_HOST = {
    'FILE_NAME': 'taxon_nodes.csv',
    'LABELS': ['Host'],
    'APP_ID': ['taxId'],
}
REL_TAXON_HAS_PARENT = {
    'FILE_NAME': 'has_parent_edges.csv',
    'TYPES': ['HAS_PARENT'],
    'APP_ID': ['sourceNodeId', 'targetNodeId'],
}
REL_PALMPRINT_HAS_SOTU = {
    'FILE_NAME': 'has_sotu_edges.csv',
    'TYPES': ['HAS_SOTU'],
}
REL_PALMPRINT_HAS_HOST = {
    'FILE_NAME': 'palmprint_has_host_edges.csv',
    'TYPES': ['HAS_HOST'],
}
REL_SOTU_HAS_HOST = {
    'FILE_NAME': 'sotu_has_host_edges.csv',
    'TYPES': ['HAS_HOST'],
}
REL_SOTU_SEQUENCE_ALIGNMENT = {
    'FILE_NAME': 'sotu_sequence_alignment_edges.csv',
    'TYPES': ['SEQUENCE_ALIGNMENT'],
}

DATASET_CFGS = {
    DATASET_VERSION_1: {
        'NODE_META': [NODE_PALMPRINT, NODE_TAXON],
        'REL_META': [REL_TAXON_HAS_PARENT, REL_PALMPRINT_HAS_HOST,
                     REL_PALMPRINT_HAS_SOTU],
        'TARGET_REL_TYPE': ['HAS_HOST'],
        'SOURCE_NODE_LABEL': 'Palmprint',
        'TARGET_NODE_LABEL': 'Taxon',
    },
    DATASET_VERSION_2: {
        'NODE_META': [NODE_SOTU, NODE_TAXON],
        'REL_META': [REL_TAXON_HAS_PARENT, REL_SOTU_HAS_HOST],
        'TARGET_REL_TYPE': ['HAS_HOST'],
        'SOURCE_NODE_LABEL': 'SOTU',
        'TARGET_NODE_LABEL': 'Taxon',
    },
    DATASET_VERSION_3: {
        'NODE_META': [NODE_SOTU, NODE_TAXON],
        'REL_META': [REL_TAXON_HAS_PARENT, REL_SOTU_HAS_HOST,
                     REL_SOTU_SEQUENCE_ALIGNMENT],
        'TARGET_REL_TYPE': ['HAS_HOST'],
        'SOURCE_NODE_LABEL': 'SOTU',
        'TARGET_NODE_LABEL': 'Taxon',
    },
    DATASET_VERSION_4: {
        'NODE_META': [NODE_PALMPRINT, NODE_TAXON],
        'REL_META': [REL_TAXON_HAS_PARENT, REL_SOTU_HAS_HOST,
                     REL_PALMPRINT_HAS_SOTU, REL_SOTU_SEQUENCE_ALIGNMENT],
        'TARGET_REL_TYPE': ['HAS_HOST'],
        'SOURCE_NODE_LABEL': 'SOTU',
        'TARGET_NODE_LABEL': 'Taxon',
    }
}
