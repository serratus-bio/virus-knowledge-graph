import time

from queries import gds_queries
from config.base import MODEL_CFGS, CUR_MODEL_VERSION


def run(args):
    G_dataset = None
    custom_run_name = 'ft-eng-degree'
    run_uid = custom_run_name if custom_run_name else int(time.time())

    gds_queries.store_run_artifact(
        run_uid, MODEL_CFGS[CUR_MODEL_VERSION], 'config')

    G_dataset = gds_queries.create_projection_from_dataset()
    gds_queries.store_run_artifact(run_uid, G_dataset, 'dataset')

    # use pyg to create test/train split, consider writing directly to dataset
    # create mapping of all palmids to all taxIds for sets
    # convert pyg graph to networkx graph, compute trad lp measures
    # use the measures directly to make high probability predictions
    # use the measures as features to train a classifier
    # compute feature importance of different measures
