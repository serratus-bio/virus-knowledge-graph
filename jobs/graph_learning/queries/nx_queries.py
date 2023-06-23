import networkx as nx
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.ensemble import RandomForestClassifier
import torch
from torch_geometric.utils import to_networkx


def run_link_pred(loader, mappings):
    sotu_mapping = {v: k for k, v in mappings['sotu'].items()}
    taxon_mapping = {v: k for k, v in mappings['taxon'].items()}
    fts = []

    for batch in loader:
        batch_homogenous = batch.to_homogeneous()
        G = to_networkx(batch_homogenous).to_undirected()

        G_connected = G.copy()
        isolated_nodes = [node for node in G.nodes() if G.degree(node) == 0]
        [G_connected.remove_node(i_n) for i_n in isolated_nodes]

        edge_index = batch_homogenous['edge_index'].tolist()
        ebunch = list(zip(edge_index[0], edge_index[1]))
        lp_iters = [
            ('jaccard_coefficient',
             lambda: nx.jaccard_coefficient(G, ebunch)),
            ('preferential_attachment',
             lambda: nx.preferential_attachment(G, ebunch)),
            ('adamic_adar_index',
             lambda: nx.adamic_adar_index(G_connected, ebunch)),
            ('resource_allocation_index',
             lambda: nx.resource_allocation_index(G, ebunch)),
            ('common_neighbor_centrality',
             lambda: nx.common_neighbor_centrality(G, ebunch)),
        ]
        fts_batch = []
        for alg_name, get_iter in lp_iters:
            iter = get_iter()
            for i, val in enumerate(iter):
                # Handle Adamic Adar division by 0 edge case
                if i > len(batch_homogenous['edge_label']) - 1 or torch.isnan(
                        batch_homogenous['edge_label'][i]):
                    if len(fts_batch) > i:
                        fts_batch[i][alg_name] = 0
                    continue
                if len(fts_batch) == i:
                    fts_batch.append({
                        'sourceAppId': sotu_mapping[val[0]],
                        'targetAppId': taxon_mapping[val[1]],
                        'actual': batch_homogenous[
                            'edge_label'][i].long().numpy(),
                    })
                cur_row = fts_batch[i]
                cur_row[alg_name] = val[2]
        fts.extend(fts_batch)
    return pd.DataFrame(fts)


def evaluate(ground_truths, preds):
    accuracy = accuracy_score(ground_truths, preds)
    precision = precision_score(ground_truths, preds)
    recall = recall_score(ground_truths, preds)
    f1 = f1_score(ground_truths, preds)
    roc_auc = roc_auc_score(ground_truths, preds)
    average_precision = average_precision_score(ground_truths, preds)
    metrics = ["accuracy", "precision", "recall",
               "f1", "roc_auc", "average_precision"]
    values = [accuracy, precision, recall, f1, roc_auc, average_precision]
    return pd.DataFrame(data={'metric': metrics, 'value': values})


def evaluate_link_pred(fts):
    cols = [
        'jaccard_coefficient',
        'preferential_attachment',
        'adamic_adar_index',
        'resource_allocation_index',
        'common_neighbor_centrality',
    ]
    stats = []
    ground_truths = torch.tensor(fts['actual'].values.astype(int))
    ground_truths = ground_truths.clamp(min=0, max=1)
    for lp_alg in cols:
        preds = torch.tensor(fts[lp_alg].values.astype(float))
        # TODO: review if mid-point is best threshold for all algos
        threshold = torch.div(torch.min(preds) + torch.max(preds), 2)
        preds = (preds > threshold).clamp(min=0, max=1).long()
        stats.append(
            (lp_alg, evaluate(ground_truths, preds))
        )
    return stats


def get_classifier():
    return RandomForestClassifier(n_estimators=30, max_depth=10,
                                  random_state=0)


def feature_importance(columns, classifier):
    features = list(zip(columns, classifier.feature_importances_))
    sorted_features = sorted(features, key=lambda x: x[1]*-1)

    keys = [value[0] for value in sorted_features]
    values = [value[1] for value in sorted_features]
    return pd.DataFrame(data={'feature': keys, 'value': values})
