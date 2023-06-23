import torch
from torch_geometric.nn import SAGEConv


class TaxonEncoder(torch.nn.Module):
    def __init__(self, hidden_channels, out_channels):
        super().__init__()
        self.conv1 = SAGEConv(-1, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, hidden_channels)
        self.lin = torch.nn.Linear(hidden_channels, out_channels)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index).relu()
        return self.lin(x)


class SOTUEncoder(torch.nn.Module):
    def __init__(self, hidden_channels, out_channels):
        super().__init__()
        self.conv1 = SAGEConv((-1, -1), hidden_channels)
        self.conv2 = SAGEConv((-1, -1), hidden_channels)
        self.conv3 = SAGEConv((-1, -1), hidden_channels)
        self.lin = torch.nn.Linear(hidden_channels, out_channels)

    def forward(self, x_dict, edge_index_dict):
        taxon_x = self.conv1(
            x_dict['taxon'],
            edge_index_dict[('taxon', 'has_parent', 'taxon')],
        ).relu()

        sotu_x = self.conv2(
            (x_dict['taxon'], x_dict['sotu']),
            edge_index_dict[('taxon', 'rev_has_host', 'sotu')],
        ).relu()

        sotu_x = self.conv3(
            (taxon_x, sotu_x),
            edge_index_dict[('taxon', 'rev_has_host', 'sotu')],
        ).relu()

        return self.lin(sotu_x)


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
    def __init__(self, num_sotus, num_taxons, hidden_channels, out_channels):
        super().__init__()
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.sotu_emb = torch.nn.Embedding(
            num_sotus, hidden_channels, device=device)
        self.taxon_emb = torch.nn.Embedding(
            num_taxons, hidden_channels, device=device)
        self.sotu_encoder = SOTUEncoder(hidden_channels, out_channels)
        self.taxon_encoder = TaxonEncoder(hidden_channels, out_channels)
        self.decoder = EdgeDecoder(out_channels)

    # x_dict, edge_index_dict, edge_label_index

    def forward(self, x_dict, edge_index_dict, edge_label_index):
        z_dict = {}
        print(x_dict['sotu'])
        x_dict['sotu'] = self.sotu_emb(x_dict['sotu'].long())
        x_dict['taxon'] = self.taxon_emb(x_dict['taxon'].long())
        z_dict['sotu'] = self.sotu_encoder(x_dict, edge_index_dict)
        z_dict['taxon'] = self.taxon_encoder(
            x_dict['taxon'],
            edge_index_dict[('taxon', 'has_parent', 'taxon')],
        )

        return self.decoder(z_dict['sotu'], z_dict['taxon'], edge_label_index)
