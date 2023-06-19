from queries.feature_queries import (
    IdentityEncoder,
    ListEncoder,
    load_edge_tensor,
    load_node_tensor,
)
from models.models import Model
from config.base import (
    DIR_CFG,
    MODEL_CFG,
    DATASET_CFG,
)

import torch
from torch_geometric.data import HeteroData
from torch_geometric.loader import LinkNeighborLoader
from torch_geometric import seed_everything
import torch_geometric.transforms as T
import torch.nn.functional as F
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    accuracy_score
)
import numpy as np

seed_everything(MODEL_CFG['RANDOM_SEED'])


def create_pyg_graph(
    sampling_rate=MODEL_CFG['SAMPLING_RATIO'],
    dataset_cfg=DATASET_CFG,
):
    data = HeteroData()
    dir_name = f"{DIR_CFG['DATASETS_DIR']}{sampling_rate}"
    node_file_paths = list(
        map(
            (lambda cfg: cfg['FILE_NAME']),
            dataset_cfg['NODE_META']
        )
    )
    rel_file_paths = list(
        map(
            (lambda cfg: cfg['FILE_NAME']),
            dataset_cfg['REL_META']
        )
    )

    if 'taxon_nodes.csv' in node_file_paths:
        taxon_x, taxon_mapping = load_node_tensor(
            filename=f'{dir_name}/taxon_nodes.csv',
            index_col='appId',
            encoders={
                # 'rankEncoded': IdentityEncoder(
                #   dtype=torch.long, is_tensor=True),
                'features': ListEncoder(),
            }
        )
        data['taxon'].x = taxon_x

    if 'sotu_nodes.csv' in node_file_paths:
        sotu_x, sotu_mapping = load_node_tensor(
            filename=f'{dir_name}/sotu_nodes.csv',
            index_col='appId',
            encoders={
                # 'centroidEncoded': IdentityEncoder(
                #   dtype=torch.long, is_tensor=True),
                'features': ListEncoder(),
            }
        )
        data['palmprint'].x = sotu_x

    if 'sotu_has_host_edges.csv' in rel_file_paths:
        has_host_edge_index, has_host_edge_label = load_edge_tensor(
            filename=f'{dir_name}/sotu_has_host_edges.csv',
            src_index_col='sourceAppId',
            src_mapping=sotu_mapping,
            dst_index_col='targetAppId',
            dst_mapping=taxon_mapping,
            encoders={
                'weight': IdentityEncoder(dtype=torch.long, is_tensor=True)
            },
        )
        data['palmprint', 'has_host', 'taxon'].edge_index = has_host_edge_index
        data['palmprint', 'has_host', 'taxon'].edge_label = has_host_edge_label

    if 'has_parent_edges.csv' in rel_file_paths:
        has_parent_edge_index, has_parent_edge_label = load_edge_tensor(
            filename=f'{dir_name}/has_parent_edges.csv',
            src_index_col='sourceAppId',
            src_mapping=taxon_mapping,
            dst_index_col='targetAppId',
            dst_mapping=taxon_mapping,
            encoders={
                'weight': IdentityEncoder(dtype=torch.long, is_tensor=True)
            },
        )
        data['taxon', 'has_parent', 'taxon'].edge_index = has_parent_edge_index
        data['taxon', 'has_parent', 'taxon'].edge_label = has_parent_edge_label

    if 'sotu_sequence_alignment_edges.csv' in rel_file_paths:
        has_parent_edge_index, has_parent_edge_label = load_edge_tensor(
            filename=f'{dir_name}/sotu_sequence_alignment_edges.csv',
            src_index_col='sourceAppId',
            src_mapping=sotu_mapping,
            dst_index_col='targetAppId',
            dst_mapping=sotu_mapping,
            encoders={
                'weight': IdentityEncoder(dtype=torch.long, is_tensor=True)
            },
        )
        data['taxon', 'has_parent', 'taxon'].edge_index = has_parent_edge_index
        data['taxon', 'has_parent', 'taxon'].edge_label = has_parent_edge_label

    node_types, edge_types = data.metadata()
    if not ('taxon', 'rev_has_host', 'palmprint') in edge_types:
        data = T.ToUndirected()(data)
        # Remove "reverse" label. (redundant if using link loader)
        del data['taxon', 'rev_has_host', 'palmprint'].edge_label
    return data


def split_data(data):
    num_test = (1 - MODEL_CFG['TRAIN_FRACTION']) * MODEL_CFG['TEST_FRACTION']
    num_val = 1 - MODEL_CFG['TRAIN_FRACTION'] - num_test
    transform = T.RandomLinkSplit(
        # Link-level split train (80%), validate (10%), and test edges (10%)
        num_val=num_val,
        num_test=num_test,

        # Of training edges, use 70% for message passing (edge_label_index)
        # and 30% for supervision (edge_index)
        disjoint_train_ratio=0.3,

        # Generate fixed negative edges for evaluation with a ratio of 2-1.
        # Negative edges during training will be generated on-the-fly.
        neg_sampling_ratio=MODEL_CFG['NEGATIVE_SAMPLING_RATIO'],
        add_negative_train_samples=True,

        edge_types=('palmprint', 'has_host', 'taxon'),
        rev_edge_types=('taxon', 'rev_has_host', 'palmprint'),
    )
    train_data, val_data, test_data = transform(data)
    return train_data, val_data, test_data


def get_train_loader(train_data):
    # Define mini-batch loaders
    edge_label_index = train_data[(
        'palmprint', 'has_host', 'taxon')].edge_label_index
    edge_label = train_data[('palmprint', 'has_host', 'taxon')].edge_label

    train_loader = LinkNeighborLoader(
        data=train_data,
        # In the first hop, we sample at most 20 neighbors.
        # In the second hop, we sample at most 10 neighbors.
        num_neighbors=[20, 10],
        neg_sampling_ratio=MODEL_CFG['NEGATIVE_SAMPLING_RATIO'],
        edge_label_index=(('palmprint', 'has_host', 'taxon'),
                          edge_label_index),
        edge_label=edge_label,
        batch_size=128,
        shuffle=True,
    )
    return train_loader


def get_model(data):
    model = Model(
        num_features=data.num_node_features,
        hidden_channels=128,
        use_embeddings=True,
        data=data,
    )
    return model


def update_stats(epoch, loss, total_examples, ):
    pass


def train(model, train_loader, model_cfg=MODEL_CFG):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: '{device}'")
    model = model.to(device)
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=model_cfg['LR'])
    stats = {}

    for epoch in range(1, model_cfg['MAX_EPOCHS']):
        total_loss = total_examples = 0
        for sampled_data in train_loader:
            optimizer.zero_grad()
            sampled_data.to(device)
            pred = model(sampled_data)
            ground_truth = sampled_data[
                "palmprint", "has_host", "taxon"].edge_label.float()
            loss = F.binary_cross_entropy_with_logits(pred, ground_truth)
            loss.backward()
            optimizer.step()
            total_loss += float(loss) * pred.numel()
            total_examples += pred.numel()
        if epoch % 10 == 0:
            print(
                f"Epoch: {epoch:03d}, Loss: {total_loss / total_examples:.4f}")
    return loss.data.numpy()


def get_val_loader(val_data):
    # Define the validation seed edges:
    edge_label_index = val_data['palmprint',
                                'has_host', 'taxon'].edge_label_index
    edge_label = val_data['palmprint', 'has_host', 'taxon'].edge_label

    val_loader = LinkNeighborLoader(
        data=val_data,
        num_neighbors=[20, 10],
        edge_label_index=(('palmprint', 'has_host', 'taxon'),
                          edge_label_index),
        edge_label=edge_label,
        batch_size=3 * 128,
        shuffle=False,
    )
    return val_loader


def eval(model, val_loader):
    preds = []
    ground_truths = []
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.eval()

    for sampled_data in val_loader:
        with torch.no_grad():
            sampled_data.to(device)
            outs = model(sampled_data)
            preds.append(outs.clamp(min=0, max=1))
            ground_truths.append(
                sampled_data['palmprint', 'has_host', 'taxon'].edge_label)

    pred = torch.cat(preds, dim=0).cpu().numpy()
    ground_truth = torch.cat(ground_truths, dim=0).cpu().numpy()
    auc = roc_auc_score(ground_truth, pred)
    print(f"Validation AUC-ROC: {auc:.4f}")
    average_precision = average_precision_score(ground_truth, pred)
    print(f"Validation AUC-PR: {average_precision:.4f}")
    accuracy = accuracy_score(ground_truth, pred)
    print(f"Accuracy: {accuracy:.4f}")
    return auc


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


def train_one_epoch(model, train_loader, optimizer, device):
    model.train()
    total_loss = total_examples = 0
    for sampled_data in train_loader:
        optimizer.zero_grad()
        sampled_data.to(device)
        pred = model(sampled_data)
        ground_truth = sampled_data[
            "palmprint", "has_host", "taxon"].edge_label.float()
        loss = F.binary_cross_entropy_with_logits(pred, ground_truth)
        loss.backward()
        optimizer.step()
        total_loss += float(loss) * pred.numel()
        total_examples += pred.numel()
    return loss.data.numpy()


def validate_one_epoch(model, loader, device):
    model.eval()
    preds = []
    ground_truths = []

    for sampled_data in loader:
        with torch.no_grad():
            sampled_data.to(device)
            out = model(sampled_data)
            preds.append(out.clamp(min=0, max=1))
            ground_truths.append(
                sampled_data['palmprint', 'has_host', 'taxon'].edge_label)

    pred = torch.cat(preds, dim=0).cpu().numpy()
    ground_truth = torch.cat(ground_truths, dim=0).cpu().numpy()

    accuracy = accuracy_score(ground_truth, pred)
    # print(f"Accuracy: {accuracy:.4f}")

    # auc_roc = roc_auc_score(ground_truth, pred)
    # print(f"Validation AUC-ROC: {auc_roc:.4f}")

    # auc_pr = average_precision_score(ground_truth, pred)
    # print(f"Validation AUC-PR: {auc_pr:.4f}")
    return accuracy


def update_stats(training_stats, epoch_stats):
    if training_stats is None:
        training_stats = {}
        for key in epoch_stats.keys():
            training_stats[key] = []
    for key, val in epoch_stats.items():
        training_stats[key].append(val)
    return training_stats


def train_and_eval_loop(model, train_loader, val_loader):
    early_stopper = EarlyStopper(patience=3, min_delta=10)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    training_stats = None

    for epoch in range(1, MODEL_CFG['MAX_EPOCHS']):
        train_loss = train_one_epoch(model, train_loader, optimizer, device)
        print("train_loss: ", train_loss)

        train_acc = validate_one_epoch(model, train_loader, device)
        print("train_acc: ", train_acc)

        val_acc = validate_one_epoch(model, val_loader, device)
        print("val_acc: ", val_acc)

        epoch_stats = {'train_acc': train_acc,
                       'val_acc': val_acc, 'epoch': epoch}
        training_stats = update_stats(training_stats, epoch_stats)
        print("training_stats: ", training_stats)

        if epoch > MODEL_CFG['MIN_EPOCHS'] \
                and early_stopper.early_stop(val_acc):
            break
    return training_stats
