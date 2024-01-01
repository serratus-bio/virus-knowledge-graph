import os

from queries.feature_queries import (
    IdentityEncoder,
    ListEncoder,
    load_edge_tensor,
    load_node_tensor,
)
from queries.utils import read_ddf_from_disk
from models.model_v3 import Model
from config.base import (
    DIR_CFG,
    MODEL_CFG,
    DATASET_CFG,
)

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
import torch
from torch_geometric import seed_everything
from torch_geometric.data import HeteroData
from torch_geometric.loader import LinkNeighborLoader
from torch_geometric.utils import to_networkx
import torch_geometric.transforms as T
import torch.nn.functional as F


seed_everything(MODEL_CFG['RANDOM_SEED'])


def create_pyg_graph(
    sampling_rate=MODEL_CFG['SAMPLING_RATIO'],
    dataset_cfg=DATASET_CFG,
):
    data = HeteroData()
    mappings = {}
    dir_name = f"{DIR_CFG['DATASETS_DIR']}{sampling_rate}"
    node_file_paths = list(
        map(
            (lambda cfg: cfg['FILE_NAME']),
            dataset_cfg['NODE_TYPES']
        )
    )
    rel_file_paths = list(
        map(
            (lambda cfg: cfg['FILE_NAME']),
            dataset_cfg['REL_TYPES']
        )
    )

    if 'taxon_nodes.csv' in node_file_paths:
        taxon_x, taxon_mapping = load_node_tensor(
            filename=f'{dir_name}/taxon_nodes.csv',
            index_col='appId',
            encoders={
                # 'rankEncoded': IdentityEncoder(
                #     dtype=torch.long, is_tensor=True),
                'features': ListEncoder(),
                # 'FastRP_embedding': ListEncoder(),
            }
        )
        data['taxon'].x = taxon_x
        data['taxon'].node_id = torch.arange(len(taxon_mapping))

        mappings['taxon'] = taxon_mapping

    if 'sotu_nodes.csv' in node_file_paths:
        sotu_x, sotu_mapping = load_node_tensor(
            filename=f'{dir_name}/sotu_nodes.csv',
            index_col='appId',
            encoders={
                # 'centroidEncoded': IdentityEncoder(
                #   dtype=torch.long, is_tensor=True),
                'features': ListEncoder(),
                # 'FastRP_embedding': ListEncoder(),
            }
        )
        data['sotu'].x = sotu_x #torch.arange(0, len(sotu_mapping))
        data['sotu'].node_id = torch.arange(len(sotu_mapping))

        mappings['sotu'] = sotu_mapping

    # if 'tissue_nodes.csv' in node_file_paths:
    #     tissue_x, tissue_mapping = load_node_tensor(
    #         filename=f'{dir_name}/tissue_nodes.csv',
    #         index_col='appId',
    #         encoders={
    #             # 'centroidEncoded': IdentityEncoder(
    #             #   dtype=torch.long, is_tensor=True),
    #             'features': ListEncoder(),
    #             # 'FastRP_embedding': ListEncoder(),
    #         }
    #     )
    #     data['tissue'].x = tissue_x # torch.arange(0, len(tissue_mapping))
    #     mappings['tissue'] = tissue_mapping

    if 'sotu_has_host_stat_edges.csv' in rel_file_paths:
        edge_index, edge_label = load_edge_tensor(
            filename=f'{dir_name}/sotu_has_host_stat_edges.csv',
            src_index_col='sourceAppId',
            src_mapping=sotu_mapping,
            dst_index_col='targetAppId',
            dst_mapping=taxon_mapping,
            # encoders={
            #     'weight': IdentityEncoder(dtype=torch.float, is_tensor=True),
            #     'weight': BinaryEncoder(dtype=torch.long),
            # },
        )
        # edge_label = torch.div(edge_label, 100)
        data['sotu', 'has_host', 'taxon'].edge_index = edge_index
        data['sotu', 'has_host', 'taxon'].edge_label = edge_label

    if 'taxon_has_parent_edges.csv' in rel_file_paths:
        edge_index, edge_label = load_edge_tensor(
            filename=f'{dir_name}/taxon_has_parent_edges.csv',
            src_index_col='sourceAppId',
            src_mapping=taxon_mapping,
            dst_index_col='targetAppId',
            dst_mapping=taxon_mapping,
            encoders={
                'weight': IdentityEncoder(dtype=torch.float, is_tensor=True)
            },
        )
        data['taxon', 'has_parent', 'taxon'].edge_index = edge_index
        data['taxon', 'has_parent', 'taxon'].edge_label = edge_label

    # if 'tissue_has_parent_edges.csv' in rel_file_paths:
    #     edge_index, edge_label = load_edge_tensor(
    #         filename=f'{dir_name}/tissue_has_parent_edges.csv',
    #         src_index_col='sourceAppId',
    #         src_mapping=tissue_mapping,
    #         dst_index_col='targetAppId',
    #         dst_mapping=tissue_mapping,
    #         encoders={
    #             'weight': IdentityEncoder(dtype=torch.float, is_tensor=True)
    #         },
    #     )
    #     data['tissue', 'has_parent', 'tissue'].edge_index = edge_index
    #     data['tissue', 'has_parent', 'tissue'].edge_label = edge_label

    if 'sotu_sequence_alignment_edges.csv' in rel_file_paths:
        edge_index, edge_label = load_edge_tensor(
            filename=f'{dir_name}/sotu_sequence_alignment_edges.csv',
            src_index_col='sourceAppId',
            src_mapping=sotu_mapping,
            dst_index_col='targetAppId',
            dst_mapping=sotu_mapping,
            encoders={
                'weight': IdentityEncoder(dtype=torch.float, is_tensor=True)
            },
        )
        data['sotu', 'sequence_alignment', 'sotu'].edge_index = edge_index
        data['sotu', 'sequence_alignment', 'sotu'].edge_label = edge_label

    if 'sotu_has_inferred_taxon_edges.csv' in rel_file_paths:
        edge_index, edge_label = load_edge_tensor(
            filename=f'{dir_name}/sotu_has_inferred_taxon_edges.csv',
            src_index_col='sourceAppId',
            src_mapping=sotu_mapping,
            dst_index_col='targetAppId',
            dst_mapping=taxon_mapping,
            encoders={
                'weight': IdentityEncoder(dtype=torch.float, is_tensor=True)
            },
        )
        data['sotu', 'has_inferred_taxon', 'taxon'].edge_index = edge_index
        data['sotu', 'has_inferred_taxon', 'taxon'].edge_label = edge_label

    node_types, edge_types = data.metadata()
    if not ('taxon', 'rev_has_host', 'sotu') in edge_types:
        data = T.ToUndirected()(data)
        # Remove "reverse" label. (redundant if using link loader)
        del data['taxon', 'rev_has_host', 'sotu'].edge_label
        # del data['taxon', 'rev_has_host_binary', 'sotu'].edge_label
    return data, mappings


def split_data(data):
    num_test = (1 - MODEL_CFG['TRAIN_FRACTION']) * MODEL_CFG['TEST_FRACTION']
    num_val = 1 - MODEL_CFG['TRAIN_FRACTION'] - num_test
    # labels = data[('sotu', 'has_host', 'taxon')]['edge_label']
    # print(labels)
    # print(torch.min(labels))
    # print(torch.max(labels))

    transform = T.RandomLinkSplit(
        # Link-level split train (80%), validate (10%), and test edges (10%)
        num_val=num_val,
        num_test=num_test,
        # Of training edges, use 70% for message passing (edge_index)
        # and 30% for supervision (edge_label_index)
        disjoint_train_ratio=0.3,
        # Generate fixed negative edges for evaluation with a ratio of 2-1.
        # Negative edges during training will be generated on-the-fly.
        neg_sampling_ratio=MODEL_CFG['NEGATIVE_SAMPLING_RATIO'],
        add_negative_train_samples=False,
        edge_types=('sotu', 'has_host', 'taxon'),
        rev_edge_types=('taxon', 'rev_has_host', 'sotu'),
    )
    train_data, val_data, test_data = transform(data)
    return train_data, val_data, test_data


def get_train_loader(train_data, batch_size=2048):
    # Define mini-batch loaders
    edge_label_index = train_data[(
        'sotu', 'has_host', 'taxon')].edge_label_index

    train_loader = LinkNeighborLoader(
        data=train_data,
        # In the first hop, we sample at most 100 neighbors.
        # In the second hop, we sample at most 50 neighbors.
        num_neighbors=[100, 50],
        neg_sampling_ratio=MODEL_CFG['NEGATIVE_SAMPLING_RATIO'],
        # neg_sampling='binary',
        # let 'binary' setting handle this
        edge_label=train_data[('sotu', 'has_host', 'taxon')].edge_label,
        edge_label_index=(('sotu', 'has_host', 'taxon'),
                          edge_label_index),
        batch_size=batch_size,
        shuffle=True,
        # num_workers=4,
    )
    return train_loader


def get_val_loader(val_data, batch_size=2048):
    # Define the validation seed edges:
    edge_label_index = val_data['sotu', 'has_host', 'taxon'].edge_label_index
    edge_label = val_data['sotu', 'has_host', 'taxon'].edge_label

    val_loader = LinkNeighborLoader(
        data=val_data,
        num_neighbors=[100, 50],
        edge_label_index=(('sotu', 'has_host', 'taxon'),
                          edge_label_index),
        edge_label=edge_label,
        batch_size=batch_size,
        shuffle=False,
        # num_workers=4,
    )
    return val_loader


def get_model(data, state_dict_path=None):
    model = Model(
        num_sotus=data['sotu'].num_nodes,
        num_taxons=data['taxon'].num_nodes,
        metadata=data.metadata(),
        hidden_channels=256,
        out_channels=128,
    )

    if state_dict_path:
        model.load_state_dict(torch.load(state_dict_path))
    
    return model


class EarlyStopper:
    def __init__(self, patience=1, min_delta=0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.min_validation_loss = np.inf

    def early_stop(self, validation_loss):
        if validation_loss < self.min_validation_loss:
            self.min_validation_loss = validation_loss
            self.counter = 0
        elif validation_loss > (self.min_validation_loss + self.min_delta):
            self.counter += 1
            if self.counter >= self.patience:
                return True
        return False


def train(model, train_loader, optimizer, device):
    model.train()
    total_loss = total_examples = 0
    for batch in train_loader:
        optimizer.zero_grad()
        batch = batch.to(device)

        pred = model(batch)
        target = batch['sotu', 'has_host', 'taxon'].edge_label.float()
        loss = F.binary_cross_entropy_with_logits(pred, target)

        loss.backward()
        optimizer.step()

        total_loss += float(loss) * pred.numel()
        total_examples += pred.numel()

    return total_loss / total_examples


@torch.no_grad()
def test(model, loader, device):
    model.eval()

    preds, targets = [], []
    for batch in loader:
        batch = batch.to(device)

        pred = model(batch)
        target = batch['sotu', 'has_host', 'taxon'].edge_label

        preds.append(pred)
        targets.append(target)

    pred = torch.cat(preds, dim=0).numpy()
    target = torch.cat(targets, dim=0).numpy()

    # accuracy = accuracy_score(target, pred)
    # print(f"Accuracy: {accuracy:.4f}")

    # auc_roc = roc_auc_score(target, pred)
    # print(f"Validation AUC-ROC: {auc_roc:.4f}")

    auc_pr = average_precision_score(target, pred)
    # print(f"Validation AUC-PR: {auc_pr:.4f}")
    return auc_pr


def update_stats(training_stats, epoch_stats):
    if training_stats is None:
        training_stats = {}
        for key in epoch_stats.keys():
            training_stats[key] = []
    for key, val in epoch_stats.items():
        training_stats[key].append(val)
    return training_stats


def train_and_eval_loop(model, train_loader, val_loader, test_loader):
    early_stopper = EarlyStopper(patience=3, min_delta=10)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: '{device}'")
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    training_stats = None

    for epoch in range(1, MODEL_CFG['MAX_EPOCHS']):
        train_loss = train(model, train_loader, optimizer, device)
        train_acc = test(model, train_loader, device)
        val_acc = test(model, val_loader, device)
        test_acc = test(model, test_loader, device)
        epoch_stats = {
            'epoch': epoch,
            'train_loss': train_loss,
            'train_acc': train_acc,
            'val_acc': val_acc,
            'test_acc': test_acc,
        }
        training_stats = update_stats(training_stats, epoch_stats)
        if epoch % 10 == 0:
            print(f"Epoch: {epoch:03d}")
            print(f"Train loss: {train_loss:.4f}")
            print(f"Test accuracy: {train_acc:.4f}")
            print(f"Validation accuracy: {val_acc:.4f}")
            print(f"Validation accuracy: {test_acc:.4f}")

        if epoch > MODEL_CFG['MIN_EPOCHS'] \
                and early_stopper.early_stop(val_acc):
            break
    return training_stats


def convert_pyg_to_nx(data):
    return to_networkx(data.to_homogeneous())


def run_exhaustive_lp_predictions(
    prediction_fn=None,
    model_cfg=MODEL_CFG,
    dataset_cfg=DATASET_CFG,
    file_path='',
    run_uid='',
    threshold=0.5,
):
    # https://github.com/pyg-team/pytorch_geometric/discussions/6792
    dir_name = f"{DIR_CFG['DATASETS_DIR']}{model_cfg['SAMPLING_RATIO']}/"

    if prediction_fn is None:
        raise ValueError("prediction_fn must be specified")

    # raise NotImplementedError

    # Read sotus into dask df
    df_sotu = read_ddf_from_disk(dir_name + 'sotu_nodes.csv')

    # Read taxons into dask df
    df_taxon = read_ddf_from_disk(dir_name + 'taxon_nodes.csv')

    # Nested loop over sotus to taxons
    # TODO use series if performance is bad
    outs = []
    for sotu_row in df_sotu[['appId', 'nodeId']].iterrows():
        for taxon_row in df_taxon['appId', 'nodeId'].iterrows():
            pred = prediction_fn(sotu_row['appId'], taxon_row['appId'])
            if pred > threshold:
                outs.append({
                    'sourceNodeId': sotu_row['appId'],
                })
    # write preds to column
    df = pd.DataFrame(outs)
    df.to_csv(file_path, index=False)



def save_model(
    run_uid,
    model,
    model_cfg=MODEL_CFG,
):
    results_dir = f"{DIR_CFG['RESULTS_DIR']}"\
        + f"/{model_cfg['SAMPLING_RATIO']}/{run_uid}/"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir, exist_ok=True)
    torch.save(model.state_dict(), results_dir + 'model_weights')



