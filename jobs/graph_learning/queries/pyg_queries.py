from queries.feature_queries import (
    ListEncoder,
    IdentityEncoder,
    load_edge_tensor,
    load_node_tensor,
)
from models.models import Model

import torch
from torch_geometric.data import HeteroData
from torch_geometric.loader import LinkNeighborLoader
import torch_geometric.transforms as T
import torch.nn.functional as F
from sklearn.metrics import roc_auc_score


def create_pyg_graph():
    sampling_rate = 0.08
    graph_name = 'palmprint-host-dataset'
    dir_name = f'./data/datasets/{graph_name}_{sampling_rate}'

    taxon_x, taxon_mapping = load_node_tensor(
        filename=f'{dir_name}/taxon_nodes.csv',
        index_col='nodeId',
        encoders={
            # 'rank': LabelEncoder(),
            'features': ListEncoder()
        }
    )
    palmprint_x, palmprint_mapping = load_node_tensor(
        filename=f'{dir_name}/palmprint_nodes.csv',
        index_col='nodeId',
        encoders={
            'features': ListEncoder()
        }
    )

    has_host_edge_index, has_host_edge_label = load_edge_tensor(
        filename=f'{dir_name}/has_host_edges.csv',
        src_index_col='sourceNodeId',
        src_mapping=palmprint_mapping,
        dst_index_col='targetNodeId',
        dst_mapping=taxon_mapping,
        # encoders={
        #     'weight': IdentityEncoder(dtype=torch.long)
        # },
    )

    has_parent_edge_index, has_parent_edge_label = load_edge_tensor(
        filename=f'{dir_name}/has_parent_edges.csv',
        src_index_col='sourceNodeId',
        src_mapping=taxon_mapping,
        dst_index_col='targetNodeId',
        dst_mapping=taxon_mapping,
        encoders={
            'weight': IdentityEncoder(dtype=torch.long)
        },
    )

    has_sotu_edge_index, has_sotu_edge_label = load_edge_tensor(
        filename=f'{dir_name}/has_sotu_edges.csv',
        src_index_col='sourceNodeId',
        src_mapping=palmprint_mapping,
        dst_index_col='targetNodeId',
        dst_mapping=palmprint_mapping,
        encoders={
            'weight': IdentityEncoder(dtype=torch.long)
        },
    )
    data = HeteroData()
    data['palmprint'].x = palmprint_x
    data['taxon'].x = taxon_x
    data['palmprint', 'has_host', 'taxon'].edge_index = has_host_edge_index
    data['palmprint', 'has_host', 'taxon'].edge_label = has_host_edge_label
    data['palmprint', 'has_sotu', 'palmprint'].edge_index = has_sotu_edge_index
    data['palmprint', 'has_sotu', 'palmprint'].edge_label = has_sotu_edge_label
    data['taxon', 'has_parent', 'taxon'].edge_index = has_parent_edge_index
    data['taxon', 'has_parent', 'taxon'].edge_label = has_parent_edge_label

    node_types, edge_types = data.metadata()
    print(data)
    print(f'Node types: {node_types}')
    print(f'Number of nodes: {data.num_nodes}')
    print(f'Dimension of node features: {data.num_node_features}')
    print(f'Edge types: {edge_types}')
    print(f'Number of edges: {data.num_edges}')
    print(f'Dimension of edge features: {data.num_edge_features}')
    print(f'Graph has isolated nodes: {data.has_isolated_nodes()}')
    print(f'Graph has self loops: {data.has_self_loops()}')
    print(f'Graph is undirected: {data.is_undirected()}')

    if not ('taxon', 'rev_has_host', 'palmprint') in edge_types:
        # not ('taxon', 'rev_has_parent', 'taxon') in edge_types:
        # not ('palmprint', 'rev_has_sotu', 'palmprint') in edge_types:
        data = T.ToUndirected()(data)
        # Remove "reverse" label.
        del data['taxon', 'rev_has_host', 'palmprint'].edge_label
        # del data['taxon', 'rev_has_parent', 'taxon'].edge_label
        # del data['palmprint', 'rev_has_sotu', 'palmprint'].edge_label

    node_types, edge_types = data.metadata()
    print(f'Edge types: {edge_types}')
    print(f'Graph is undirected: {data.is_undirected()}')
    return data


def split_data(data):
    transform = T.RandomLinkSplit(
        # Link-level split train (80%), validate (10%), and test edges (10%)
        num_val=0.1,
        num_test=0.1,

        # Of training edges, use 70% for message passing 30% for supervision
        disjoint_train_ratio=0.3,

        # Generate fixed negative edges for evaluation with a ratio of 2-1.
        # Negative edges during training will be generated on-the-fly.
        neg_sampling_ratio=2.0,
        add_negative_train_samples=False,

        edge_types=('palmprint', 'has_host', 'taxon'),
        rev_edge_types=('taxon', 'rev_has_host', 'palmprint'),
    )
    train_data, val_data, test_data = transform(data)

    print(f'Train graphs: {train_data}')
    print(f'Validation graphs: {val_data}')
    print(f'Test graphs: {test_data}')
    return train_data, val_data, test_data


def get_train_loader(train_data):
    # Define mini-batch loaders
    edge_label_index = train_data[(
        'palmprint', 'has_host', 'taxon')].edge_label_index
    edge_label = train_data[('palmprint', 'has_host', 'taxon')].edge_label

    train_loader = LinkNeighborLoader(
        data=train_data,
        num_neighbors=[20, 10],
        neg_sampling_ratio=2.0,
        edge_label_index=(('palmprint', 'has_host', 'taxon'),
                          edge_label_index),
        edge_label=edge_label,
        batch_size=128,
        shuffle=True,
    )
    # Inspect a sample:
    sampled_data = next(iter(train_loader))
    print("Sampled training mini-batch:")
    print("===================")
    print(sampled_data)
    assert sampled_data[('palmprint', 'has_host', 'taxon')
                        ].edge_label_index.size(1) == 3 * 128
    return train_loader


def get_model(data):

    model = Model(
        num_features=data.num_node_features,
        hidden_channels=64,
        use_embeddings=True,
        data=data,
    )
    print(model)
    return model


def train(model, train_loader):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: '{device}'")
    print(len(train_loader))
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    for epoch in range(1, 2):
        print(epoch)
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
        if epoch % 5 == 0:
            print(
                f"Epoch: {epoch:03d}, Loss: {total_loss / total_examples:.4f}")


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

    sampled_data = next(iter(val_loader))

    print("Sampled validation mini-batch:")
    print("===================")
    print(sampled_data)
    assert sampled_data['palmprint', 'has_host',
                        'taxon'].edge_label_index.size(1) == 3 * 128
    assert sampled_data[
        'palmprint', 'has_host', 'taxon'].edge_label.min() >= 0
    assert sampled_data[
        'palmprint', 'has_host', 'taxon'].edge_label.max() <= 1
    return val_loader


def eval(model, val_loader):
    preds = []
    ground_truths = []
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    for sampled_data in val_loader:
        with torch.no_grad():
            sampled_data.to(device)
            preds.append(model(sampled_data))
            ground_truths.append(
                sampled_data['palmprint', 'has_host', 'taxon'].edge_label)

    pred = torch.cat(preds, dim=0).cpu().numpy()
    ground_truth = torch.cat(ground_truths, dim=0).cpu().numpy()
    print(ground_truth)
    print(pred)
    auc = roc_auc_score(ground_truth, pred)
    print(f"Validation AUC: {auc:.4f}")
    return auc
