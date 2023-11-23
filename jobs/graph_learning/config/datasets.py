DATASET_VERSION_1 = 'data-v1'
DATASET_VERSION_2 = 'data-v2'
DATASET_VERSION_3 = 'data-v3'
DATASET_VERSION_4 = 'data-v4'
DATASET_VERSION_5 = 'data-v5'


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
}
REL_PALMPRINT_HAS_SOTU = {
    'FILE_NAME': 'has_sotu_edges.csv',
    'TYPES': ['HAS_SOTU'],
}
REL_PALMPRINT_HAS_HOST = {
    'FILE_NAME': 'palmprint_has_host_edges.csv',
    'TYPES': ['HAS_HOST_METADATA'],
}
REL_SOTU_HAS_HOST_METADATA = {
    'FILE_NAME': 'sotu_has_host_metadata_edges.csv',
    'TYPES': ['HAS_HOST_METADATA'],
}
REL_SOTU_HAS_HOST_STAT = {
    'FILE_NAME': 'sotu_has_host_stat_edges.csv',
    'TYPES': ['HAS_HOST_STAT'],
}
REL_SOTU_SEQUENCE_ALIGNMENT = {
    'FILE_NAME': 'sotu_sequence_alignment_edges.csv',
    'TYPES': ['SEQUENCE_ALIGNMENT'],
}
REL_SOTU_HAS_INFERRED_TAXON = {
    'FILE_NAME': 'sotu_has_inferred_taxon_edges.csv',
    'TYPES': ['HAS_INFERRED_TAXON'],
}


DATASET_CFGS = {
    DATASET_VERSION_1: {
        'NODE_META': [NODE_PALMPRINT, NODE_TAXON],
        'REL_META': [REL_TAXON_HAS_PARENT, REL_PALMPRINT_HAS_HOST,
                     REL_PALMPRINT_HAS_SOTU],
        'TARGET_REL_TYPE': ['HAS_HOST_METADATA'],
        'SOURCE_NODE_LABEL': 'Palmprint',
        'TARGET_NODE_LABEL': 'Taxon',
    },
    DATASET_VERSION_2: {
        'NODE_META': [NODE_SOTU, NODE_TAXON],
        'REL_META': [REL_TAXON_HAS_PARENT, REL_SOTU_HAS_HOST_METADATA],
        'TARGET_REL_TYPE': ['HAS_HOST_METADATA'],
        'SOURCE_NODE_LABEL': 'SOTU',
        'TARGET_NODE_LABEL': 'Taxon',
    },
    DATASET_VERSION_3: {
        'NODE_META': [NODE_SOTU, NODE_TAXON],
        'REL_META': [REL_TAXON_HAS_PARENT, REL_SOTU_HAS_HOST_METADATA,
                     REL_SOTU_SEQUENCE_ALIGNMENT],
        'TARGET_REL_TYPE': ['HAS_HOST_METADATA'],
        'SOURCE_NODE_LABEL': 'SOTU',
        'TARGET_NODE_LABEL': 'Taxon',
    },
    DATASET_VERSION_4: {
        'NODE_META': [NODE_SOTU, NODE_TAXON],
        'REL_META': [REL_TAXON_HAS_PARENT, REL_SOTU_HAS_HOST_METADATA,
                     REL_SOTU_SEQUENCE_ALIGNMENT, REL_SOTU_HAS_INFERRED_TAXON,
                     ],
        'TARGET_REL_TYPE': ['HAS_HOST_METADATA'],
        'SOURCE_NODE_LABEL': 'SOTU',
        'TARGET_NODE_LABEL': 'Taxon',
    },
    DATASET_VERSION_5: {
        'NODE_META': [NODE_SOTU, NODE_TAXON],
        'REL_META': [REL_TAXON_HAS_PARENT, REL_SOTU_HAS_HOST_STAT,
                     REL_SOTU_SEQUENCE_ALIGNMENT, REL_SOTU_HAS_INFERRED_TAXON,
                     ],
        'TARGET_REL_TYPE': ['REL_SOTU_HAS_HOST_STAT'],
        'SOURCE_NODE_LABEL': 'SOTU',
        'TARGET_NODE_LABEL': 'Taxon',
    },
}
