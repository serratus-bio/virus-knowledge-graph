import torch
from torch_geometric.nn import SAGEConv, to_hetero
import torch.nn.functional as F


class GNN(torch.nn.Module):
    def __init__(self, hidden_channels):
        super().__init__()
        self.conv1 = SAGEConv(hidden_channels, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, hidden_channels)

    def forward(self, x, edge_index):
        x = F.relu(self.conv1(x, edge_index))
        x = self.conv2(x, edge_index)
        return x


# Classifier applies the dot-product between source and destination
# node embeddings to derive edge-level predictions:
class Classifier(torch.nn.Module):
    def forward(self, x_palmprint, x_taxon, edge_label_index):
        # Convert node embeddings to edge-level representations:
        edge_feat_palmprint = x_palmprint[edge_label_index[0]]
        edge_feat_taxon = x_taxon[edge_label_index[1]]
        # Apply dot-product to get a prediction per supervision edge:
        return (edge_feat_palmprint * edge_feat_taxon).sum(dim=-1)


class Model(torch.nn.Module):
    def __init__(self, num_features, hidden_channels,
                 data, use_embeddings=True):
        super().__init__()
        self.use_embeddings = use_embeddings
        self.taxon_lin = torch.nn.Linear(
            num_features["taxon"], hidden_channels, dtype=torch.float)
        self.palmprint_lin = torch.nn.Linear(
            num_features["palmprint"], hidden_channels, dtype=torch.float)
        # If dataset does not come with rich features
        # we can learn two embedding matrices for palmprint and taxon
        self.palmprint_emb = torch.nn.Embedding(
            data["palmprint"].num_nodes,
            hidden_channels,
        ) if use_embeddings else None
        self.taxon_emb = torch.nn.Embedding(
            data["taxon"].num_nodes,
            hidden_channels,
        ) if use_embeddings else None
        # Instantiate homogeneous GNN:
        self.gnn = GNN(hidden_channels)
        # Convert GNN model into a heterogeneous variant:
        self.gnn = to_hetero(self.gnn, metadata=data.metadata())
        self.classifier = Classifier()

    def forward(self, data):  # x_dict, edge_index_dict, edge_label_index
        if self.use_embeddings:
            x_dict = {
                "palmprint": self.palmprint_emb(data["palmprint"].n_id),
                "taxon": self.taxon_lin(data["taxon"].x)
                + self.taxon_emb(data["taxon"].n_id),
            }
        else:
            x_dict = {
                "palmprint": self.palmprint_lin(data["palmprint"].x),
                "taxon": self.taxon_lin(data["taxon"].x),
            }
        x_dict = self.gnn(x_dict, data.edge_index_dict)
        pred = self.classifier(
            x_dict["palmprint"],
            x_dict["taxon"],
            data['palmprint', 'has_host', 'taxon'].edge_label_index,
        )
        return pred
