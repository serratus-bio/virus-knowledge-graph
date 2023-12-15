DATASET_VERSION_1 = 'data-v1'
DATASET_VERSION_2 = 'data-v2'
DATASET_VERSION_3 = 'data-v3'
DATASET_VERSION_4 = 'data-v4'
DATASET_VERSION_5 = 'data-v5'
DATASET_VERSION_6 = 'data-v6'
DATASET_VERSION_7 = 'data-v7'
DATASET_VERSION_8 = 'data-v8'
DATASET_VERSION_9 = 'data-v9'


NODE_PALMPRINT = {
    'FILE_NAME': 'n4j_palmprint_nodes.csv',
    'LABELS': ['Palmprint', 'SOTU'],
    'APP_ID': ['palmId'],
}
NODE_SOTU = {
    'FILE_NAME': 'n4j_sotu_nodes.csv',
    'LABELS': ['SOTU'],
    'APP_ID': ['palmId'],
}
NODE_TAXON = {
    'FILE_NAME': 'n4j_taxon_nodes.csv',
    'LABELS': ['Taxon'],
    'APP_ID': ['taxId'],
}
NODE_TISSUE = {
    'FILE_NAME': 'n4j_tissue_nodes.csv',
    'LABELS': ['Tissue'],
    'APP_ID': ['btoId'],
}
REL_TAXON_HAS_PARENT = {
    'FILE_NAME': 'n4j_taxon_has_parent_edges.csv',
    'TYPES': ['HAS_PARENT'],
}
REL_PALMPRINT_HAS_SOTU = {
    'FILE_NAME': 'n4j_palmprint_has_sotu_edges.csv',
    'TYPES': ['HAS_SOTU'],
}
REL_PALMPRINT_HAS_HOST_METADATA = {
    'FILE_NAME': 'n4j_palmprint_has_host_metadata_edges.csv',
    'TYPES': ['HAS_HOST_METADATA'],
}
REL_SOTU_HAS_HOST_METADATA = {
    'FILE_NAME': 'n4j_sotu_has_host_metadata_edges.csv',
    'TYPES': ['HAS_HOST_METADATA'],
}
REL_SOTU_HAS_HOST_STAT = {
    'FILE_NAME': 'n4j_sotu_has_host_stat_edges.csv',
    'TYPES': ['HAS_HOST_STAT'],
}
REL_SOTU_SEQUENCE_ALIGNMENT = {
    'FILE_NAME': 'n4j_sotu_sequence_alignment_edges.csv',
    'TYPES': ['SEQUENCE_ALIGNMENT'],
}
REL_SOTU_HAS_INFERRED_TAXON = {
    'FILE_NAME': 'n4j_sotu_has_inferred_taxon_edges.csv',
    'TYPES': ['HAS_INFERRED_TAXON'],
}
REL_SOTU_HAS_TISSUE_METADATA = {
    'FILE_NAME': 'n4j_sotu_has_tissue_metadata.csv',
    'TYPES': ['HAS_TISSUE_METADATA'],
}


DATASET_CFGS = {
    DATASET_VERSION_1: {
        'NODE_TYPES': [NODE_PALMPRINT, NODE_TAXON],
        'REL_TYPES': [REL_PALMPRINT_HAS_HOST_METADATA,
                     REL_PALMPRINT_HAS_SOTU],
        'TARGET_REL_TYPE': ['HAS_HOST_METADATA'],
        'SOURCE_NODE_LABEL': 'Palmprint',
        'TARGET_NODE_LABEL': 'Taxon',
    },
    DATASET_VERSION_2: {
        'NODE_TYPES': [NODE_SOTU, NODE_TAXON],
        'REL_TYPES': [REL_SOTU_HAS_HOST_METADATA],
        'TARGET_REL_TYPE': ['HAS_HOST_METADATA'],
        'SOURCE_NODE_LABEL': 'SOTU',
        'TARGET_NODE_LABEL': 'Taxon',
    },
    DATASET_VERSION_3: {
        'NODE_TYPES': [NODE_SOTU, NODE_TAXON],
        'REL_TYPES': [REL_SOTU_HAS_HOST_STAT],
        'TARGET_REL_TYPE': ['REL_SOTU_HAS_HOST_STAT'],
        'SOURCE_NODE_LABEL': 'SOTU',
        'TARGET_NODE_LABEL': 'Taxon',
    },
    DATASET_VERSION_4: {
        'NODE_TYPES': [NODE_SOTU, NODE_TAXON],
        'REL_TYPES': [REL_SOTU_HAS_HOST_METADATA, REL_SOTU_HAS_HOST_STAT],
        'TARGET_REL_TYPE': ['REL_SOTU_HAS_HOST_STAT'],
        'SOURCE_NODE_LABEL': 'SOTU',
        'TARGET_NODE_LABEL': 'Taxon',
    },
    DATASET_VERSION_5: {
        'NODE_TYPES': [NODE_SOTU, NODE_TAXON],
        'REL_TYPES': [REL_TAXON_HAS_PARENT, REL_SOTU_HAS_HOST_STAT],
        'TARGET_REL_TYPE': ['REL_SOTU_HAS_HOST_STAT'],
        'SOURCE_NODE_LABEL': 'SOTU',
        'TARGET_NODE_LABEL': 'Taxon',
    },
    DATASET_VERSION_6: {
        'NODE_TYPES': [NODE_SOTU, NODE_TAXON],
        'REL_TYPES': [REL_SOTU_HAS_HOST_STAT, REL_SOTU_SEQUENCE_ALIGNMENT],
        'TARGET_REL_TYPE': ['REL_SOTU_HAS_HOST_STAT'],
        'SOURCE_NODE_LABEL': 'SOTU',
        'TARGET_NODE_LABEL': 'Taxon',
    },
    DATASET_VERSION_7: {
        'NODE_TYPES': [NODE_SOTU, NODE_TAXON],
        'REL_TYPES': [REL_SOTU_HAS_HOST_STAT, REL_SOTU_HAS_INFERRED_TAXON],
        'TARGET_REL_TYPE': ['REL_SOTU_HAS_HOST_STAT'],
        'SOURCE_NODE_LABEL': 'SOTU',
        'TARGET_NODE_LABEL': 'Taxon',
    },
    DATASET_VERSION_8: {
        'NODE_TYPES': [NODE_SOTU, NODE_TAXON, NODE_TISSUE],
        'REL_TYPES': [REL_SOTU_HAS_HOST_STAT, REL_SOTU_HAS_TISSUE_METADATA],
        'TARGET_REL_TYPE': ['REL_SOTU_HAS_HOST_STAT'],
        'SOURCE_NODE_LABEL': 'SOTU',
        'TARGET_NODE_LABEL': 'Taxon',
    },
    DATASET_VERSION_9: {
        'NODE_TYPES': [NODE_SOTU, NODE_TAXON, NODE_TISSUE],
        'REL_TYPES': [REL_SOTU_HAS_HOST_STAT, REL_TAXON_HAS_PARENT,
                     REL_SOTU_SEQUENCE_ALIGNMENT, REL_SOTU_HAS_INFERRED_TAXON,
                     REL_SOTU_HAS_TISSUE_METADATA,
                     ],
        'TARGET_REL_TYPE': ['REL_SOTU_HAS_HOST_STAT'],
        'SOURCE_NODE_LABEL': 'SOTU',
        'TARGET_NODE_LABEL': 'Taxon',
    },
}
