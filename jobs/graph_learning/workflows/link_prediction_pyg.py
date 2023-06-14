import time

from queries import pyg_queries, utils
from config.base import MODEL_CFG, DATASET_CFG


def run(args):
    run_uid = f'pyg-lp-{int(time.time())}'
    utils.store_run_artifact(
        run_uid, MODEL_CFG, 'model_cfg')
    utils.store_run_artifact(
        run_uid, DATASET_CFG, 'data_cfg')

    data = pyg_queries.create_pyg_graph()
    utils.store_run_artifact(run_uid, data, 'data')

    model = pyg_queries.get_model(data)
    utils.store_run_artifact(run_uid, model, 'model')

    train_data, val_data, test_data = pyg_queries.split_data(data)

    train_loader = pyg_queries.get_train_loader(train_data)
    utils.store_run_artifact(run_uid, train_loader, 'train_loader')

    val_loader = pyg_queries.get_val_loader(val_data)

    train_stats = pyg_queries.train(model, train_loader)
    utils.store_run_artifact(run_uid, train_stats, 'train_stats')

    val_stats = pyg_queries.eval(model, val_loader)
    utils.store_run_artifact(run_uid, val_stats, 'val_stats')

    # stats = pyg_queries.train_and_eval_loop(model, train_loader, val_loader)
    # print(stats)

    # utils.store_run_artifact(
    #     run_uid, stats, 'stats')
