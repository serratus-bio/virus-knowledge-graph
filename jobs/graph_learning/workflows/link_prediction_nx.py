from queries import utils, pyg_queries, nx_queries
from config.base import MODEL_CFG, DATASET_CFG


def run():
    run_uid = 'trad-lp'
    subgraph_size = 5000

    utils.store_run_artifact(
        run_uid, MODEL_CFG, 'model_cfg')
    utils.store_run_artifact(
        run_uid, DATASET_CFG, 'data_cfg')
    utils.store_run_artifact(
        run_uid, subgraph_size, 'subgraph_size')

    data, mappings = pyg_queries.create_pyg_graph()
    train_data, val_data, test_data = pyg_queries.split_data(data)

    # batch loader with negative sampling
    # batch_size relates to num nodes used for lp algo
    # Tuned with Error code 12 (Cannot allocate memory) on 16GB RAM
    loader = pyg_queries.get_train_loader(train_data, batch_size=subgraph_size)
    # loader = pyg_queries.get_val_loader(val_data)

    lp_fts = nx_queries.run_link_pred(
        loader, mappings)
    utils.store_run_artifact(run_uid, lp_fts, 'lp_fts')

    stats = nx_queries.evaluate_link_pred(lp_fts)
    for name, df in stats:
        utils.store_run_artifact(run_uid, df, name)

    # TODO: use the measures as features to train a classifier
    # TODO: compute feature importance of different measures
