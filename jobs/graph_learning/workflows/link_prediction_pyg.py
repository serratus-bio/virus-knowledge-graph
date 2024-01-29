from queries import pyg_queries, utils
from config.base import MODEL_CFG, DATASET_CFG


def run():
    run_uid = 'pyg-lp'
    utils.store_run_artifact(
        run_uid, MODEL_CFG, 'model_cfg')
    utils.store_run_artifact(
        run_uid, DATASET_CFG, 'data_cfg')

    print('Creating Pytorch Geometric graph')
    data, mappings = pyg_queries.create_pyg_graph()
    utils.store_run_artifact(run_uid, data, 'data')
    utils.store_run_artifact(run_uid, mappings, 'mappings')

    model = pyg_queries.get_model(data)
    utils.store_run_artifact(run_uid, model, 'model')

    print('Splitting data int train, val, test sets')
    train_data, val_data, test_data = pyg_queries.split_data(data)

    print('Initalize batch loaders')
    train_loader = pyg_queries.get_train_loader(train_data)
    val_loader = pyg_queries.get_val_loader(val_data)
    test_loader = pyg_queries.get_val_loader(train_data)

    print('Running train and eval loop')
    stats = pyg_queries.train_and_eval_loop(
        model, train_loader, val_loader, test_loader)
    utils.store_run_artifact(
        run_uid, stats, 'stats')

    print('Storing model weights')
    pyg_queries.save_model(
        run_uid, model 
    )
    