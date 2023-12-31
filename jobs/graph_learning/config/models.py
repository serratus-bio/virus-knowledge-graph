from .datasets import (
    DATASET_VERSION_1,
    DATASET_VERSION_2,
    DATASET_VERSION_3,
    DATASET_VERSION_4,
    DATASET_VERSION_5,
    DATASET_VERSION_6,
    DATASET_VERSION_7,
    DATASET_VERSION_8,
    DATASET_VERSION_9,
)

MODEL_VERSION_1 = 'model-v1'
MODEL_VERSION_2 = 'model-v2'
MODEL_VERSION_3 = 'model-v3'
MODEL_VERSION_4 = 'model-v4'
MODEL_VERSION_5 = 'model-v5'
MODEL_VERSION_6 = 'model-v6'
MODEL_VERSION_7 = 'model-v7'
MODEL_VERSION_8 = 'model-v8'
MODEL_VERSION_9 = 'model-v9'
MODEL_VERSION_10 = 'model-v10'
MODEL_VERSION_11 = 'model-v11'

CUR_MODEL_VERSION = MODEL_VERSION_11

BASE_MODEL_CFG = {
    'PROJECTION_NAME': 'virus-host-projection',
    'PIPELINE_NAME': 'lp-pipeline',
    'MODEL_NAME': 'lp-model',
    'RANDOM_SEED': 42,
    'TEST_FRACTION': 0.25, # fraction of total data
    'TRAIN_FRACTION': 0.6, # fraction of test complement for training, remaining is used for features
    'VALIDATION_FOLDS': 10,
    'MIN_EPOCHS': 1,
    'MAX_EPOCHS': 100,
    'LR': 0.001,
    'PREDICTION_THRESHOLD': 0.2,
    'SAMPLING_RATIO': 0.1,
    'NEGATIVE_SAMPLING_RATIO': 100,
    'NEGATIVE_CLASS_WEIGHT': 1,
}

MODEL_CFGS = {
    MODEL_VERSION_1: {
        **BASE_MODEL_CFG,
        'PROJECTION_NAME': 'incl-palmprint-excl-sotu',
        'DATASET_VERSION': DATASET_VERSION_1,
        'SAMPLING_RATIO': 0.1,
    },
    MODEL_VERSION_2: {
        **BASE_MODEL_CFG,
        'PROJECTION_NAME': 'excl-palmprint-incl-sotu',
        'DATASET_VERSION': DATASET_VERSION_2,
        'SAMPLING_RATIO': 0.1,
    },
    MODEL_VERSION_3: {
        **BASE_MODEL_CFG,
        'PROJECTION_NAME': 'incl-stat-excl-metadata',
        'DATASET_VERSION': DATASET_VERSION_3,
        'SAMPLING_RATIO': 0.1,
    },
    MODEL_VERSION_4: {
        **BASE_MODEL_CFG,
        'PROJECTION_NAME': 'incl-metadata-incl-stat',
        'DATASET_VERSION': DATASET_VERSION_4,
        'SAMPLING_RATIO': 0.1,
    },
    MODEL_VERSION_5: {
        **BASE_MODEL_CFG,
        'PROJECTION_NAME': 'incl-taxon-parent',
        'DATASET_VERSION': DATASET_VERSION_5,
        'SAMPLING_RATIO': 0.1,
    },
    MODEL_VERSION_6: {
        **BASE_MODEL_CFG,
        'PROJECTION_NAME': 'incl-seq-alignment',
        'DATASET_VERSION': DATASET_VERSION_6,
        'SAMPLING_RATIO': 0.1,
    },
    MODEL_VERSION_7: {
        **BASE_MODEL_CFG,
        'PROJECTION_NAME': 'incl-inferred-tax',
        'DATASET_VERSION': DATASET_VERSION_7,
        'SAMPLING_RATIO': 0.1,
    },
    MODEL_VERSION_8: {
        **BASE_MODEL_CFG,
        'PROJECTION_NAME': 'incl-tissue',
        'DATASET_VERSION': DATASET_VERSION_8,
        'SAMPLING_RATIO': 0.1,
    },
    MODEL_VERSION_9: {
        **BASE_MODEL_CFG,
        'PROJECTION_NAME': 'full-1',
        'DATASET_VERSION': DATASET_VERSION_9,
        'SAMPLING_RATIO': 0.1,
        'NEGATIVE_SAMPLING_RATIO': 1.32,
    },
    MODEL_VERSION_10: {
        **BASE_MODEL_CFG,
        'PROJECTION_NAME': 'full-2',
        'DATASET_VERSION': DATASET_VERSION_9,
        'SAMPLING_RATIO': 0.5,
    },
    MODEL_VERSION_11: {
        **BASE_MODEL_CFG,
        'PROJECTION_NAME': 'full-3',
        'DATASET_VERSION': DATASET_VERSION_9,
        'SAMPLING_RATIO': 1,
    },
}
