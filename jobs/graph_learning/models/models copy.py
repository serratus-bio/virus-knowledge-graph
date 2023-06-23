import torch
from torch_geometric.nn import SAGEConv, to_hetero


class GNNEncoder(torch.nn.Module):
    def __init__(self, hidden_channels, out_channels):
        super().__init__()
        # SAGEConv(hidden_channels, hidden_channels)
        self.conv1 = SAGEConv(-1, hidden_channels)
        # SAGEConv(hidden_channels, hidden_channels)
        self.conv2 = SAGEConv(-1, hidden_channels)
        self.lin = torch.nn.Linear(hidden_channels, out_channels)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index).relu()
        return self.lin(x)


class TaxonGNNEncoder(torch.nn.Module):
    def __init__(self, hidden_channels, out_channels):
        super().__init__()
        # SAGEConv(hidden_channels, hidden_channels)
        self.conv1 = SAGEConv((-1, -1), hidden_channels)
        # SAGEConv(hidden_channels, hidden_channels)
        self.conv2 = SAGEConv((-1, -1), hidden_channels)
        self.lin = torch.nn.Linear(hidden_channels, out_channels)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index).relu()
        return self.lin(x)


# Classifier applies the dot-product between source and destination
# node embeddings to derive edge-level predictions:
class Classifier(torch.nn.Module):
    def forward(self, x_sotu, x_taxon, edge_label_index):
        # Convert node embeddings to edge-level representations:
        edge_feat_sotu = x_sotu[edge_label_index[0]]
        edge_feat_taxon = x_taxon[edge_label_index[1]]
        # Apply dot-product to get a prediction per supervision edge:
        return (edge_feat_sotu * edge_feat_taxon).sum(dim=-1)


class EdgeDecoder(torch.nn.Module):
    def __init__(self, hidden_channels):
        super().__init__()
        self.lin1 = torch.nn.Linear(2 * hidden_channels, hidden_channels)
        self.lin2 = torch.nn.Linear(hidden_channels, 1)

    def forward(self, z_dict, edge_label_index):
        row, col = edge_label_index
        z = torch.cat([z_dict['sotu'][row], z_dict['taxon'][col]], dim=-1)

        z = self.lin1(z).relu()
        z = self.lin2(z)
        return z.view(-1)


class Model(torch.nn.Module):
    def __init__(self, hidden_channels, metadata):
        super().__init__()

        # Instantiate homogeneous GNN:
        self.encoder = GNNEncoder(hidden_channels, hidden_channels)
        # Convert GNN model into a heterogeneous variant:
        self.encoder = to_hetero(
            self.encoder, metadata=metadata, aggr='sum')
        # self.decoder = Classifier(hidden_channels)
        self.decoder = EdgeDecoder(hidden_channels)

    # x_dict, edge_index_dict, edge_label_index
    def forward(self, x_dict, edge_index_dict, edge_label_index):
        z_dict = self.encoder(x_dict, edge_index_dict)
        return self.decoder(
            z_dict,
            edge_label_index,
        )
