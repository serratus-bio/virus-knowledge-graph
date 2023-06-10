DIR_CFG = {
    'FEATURE_STORE_DIR': '/mnt/graphdata/features/',
    'DATASETS_DIR': '/mnt/graphdata/datasets/',
    'RESULTS_DIR': '/mnt/graphdata/results/',
}

CUR_MODEL_VERSION = 'V1'

MODEL_CFGS = {
    'V1': {
        'PROJECTION_NAME': 'palmprint-host-dataset',
        'PIPELINE_NAME': 'lp-pipeline',
        'MODEL_NAME': 'lp-model',
        'RANDOM_SEED': 42,
        'SAMPLING_RATIO': 0.1,
        'TEST_FRACTION': 0.3,
        'TRAIN_FRACTION': 0.6,
        'VALIDATION_FOLDS': 10,
        'NEGATIVE_SAMPLING_RATIO': 1.34,
        'NEGATIVE_CLASS_WEIGHT': 1,
        'PREDICTION_THRESHOLD': 0.7,
    }
}
