# TODO: use yaml config library to manage versioning
from .models import MODEL_CFGS, CUR_MODEL_VERSION
from .datasets import DATASET_CFGS

MODEL_CFG = MODEL_CFGS[CUR_MODEL_VERSION]

CUR_DATASET_VERSION = MODEL_CFG['DATASET_VERSION']
DATASET_CFG = DATASET_CFGS[CUR_DATASET_VERSION]


DIR_CFG = {
    'QUERY_CACHE_DIR': '/mnt/graphdata/query_cache/neo4j/',
    'FEATURE_STORE_DIR': '/mnt/graphdata/features/'
    + CUR_DATASET_VERSION + '/',
    'GRAPHRAG_DIR': '/mnt/graphdata/graphrag/',
    'EMBEDDINGS_DIR': '/mnt/graphdata/features/embeddings/',
    'DATASETS_DIR': '/mnt/graphdata/datasets/'
    + CUR_DATASET_VERSION + '/',
    'RESULTS_DIR': '/mnt/graphdata/results/'
    + CUR_DATASET_VERSION + '/',
}
