import torch
from torch_geometric.nn import SAGEConv, to_hetero, GATConv
import torch.nn.functional as F


class GNN(torch.nn.Module):
    def __init__(self, hidden_channels, out_channels):
        super().__init__()
        # self.conv1 = SAGEConv((-1, -1), hidden_channels)
        # self.conv2 = SAGEConv((-1, -1), out_channels)
        self.conv1 = GATConv((-1, -1), hidden_channels, add_self_loops=False)
        self.conv2 = GATConv((-1, -1), out_channels, add_self_loops=False)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index)
        return x


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
    def __init__(self, num_sotus, num_taxons, metadata, hidden_channels, out_channels):
        super().__init__()
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.sotu_lin = torch.nn.Linear(1, hidden_channels)
        self.taxon_lin = torch.nn.Linear(1, hidden_channels)
        
        self.sotu_emb = torch.nn.Embedding(
            num_sotus, hidden_channels, device=device)
        self.taxon_emb = torch.nn.Embedding(
            num_taxons, hidden_channels, device=device)

        self.decoder = EdgeDecoder(out_channels)

        self.gnn = GNN(hidden_channels, out_channels)
        self.gnn = to_hetero(self.gnn, metadata=metadata)

    def forward(self, data, return_embeddings=False):
        # x_dict = data['x_dict']
        edge_index_dict = data.edge_index_dict

        x_dict = {
          "sotu": self.sotu_lin(data.x_dict["sotu"]) + self.sotu_emb(data["sotu"].node_id.long()),
          "taxon": self.taxon_lin(data.x_dict["taxon"]) + self.taxon_emb(data["taxon"].node_id.long()),
        }

        z_dict = self.gnn(x_dict, edge_index_dict)
        
        if return_embeddings:
            return x_dict

        edge_label_index = data['sotu', 'has_host', 'taxon'].edge_label_index

        return self.decoder(z_dict, edge_label_index)
