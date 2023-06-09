import ast

from queries import utils
from config.config import DIR_CFG

import torch
import pandas as pd


def get_features_from_file(
    file_name,
    dir_name=DIR_CFG['FEATURE_STORE_DIR'],
    select_columns=[],
    index_cols=[],
):
    df = utils.read_ddf_from_disk(dir_name + file_name)
    if select_columns:
        df = df[select_columns]
    if len(index_cols) > 0:
        df.set_index(index_cols)
    return df


def get_all_node_features(dir_name=DIR_CFG['FEATURE_STORE_DIR']):
    node_file_paths = [
        dir_name + 'palmprint_nodes.csv',
        dir_name + 'taxon_nodes.csv',
    ]
    nodes = utils.merge_files_to_df(
        node_file_paths,
        select_columns=['nodeId', 'labels',
                        'features', 'degree', 'degreeWeighted'],
    )
    nodes = utils.deserialize_df(nodes)
    nodes.set_index('nodeId')
    return nodes


def get_all_relationship_features(
        dir_name=DIR_CFG['FEATURE_STORE_DIR'],
):

    relationship_file_paths = [
        dir_name + 'has_sotu_edges.csv',
        dir_name + 'has_parent_edges.csv',
        dir_name + 'has_host_edges.csv',
    ]
    relationships = utils.merge_files_to_df(
        relationship_file_paths,
        select_columns=['sourceNodeId', 'targetNodeId',
                        'relationshipType', 'weight'],
    )
    relationships = utils.deserialize_df(relationships)
    # relationships.set_index(['sourceNodeId', 'targetNodeId'])
    return relationships


class IdentityEncoder(object):
    # The 'IdentityEncoder' takes the raw column values and converts them to
    # PyTorch tensors.
    def __init__(self, dtype=None, is_list=False):
        self.dtype = dtype
        self.is_list = is_list

    def __call__(self, df):
        if self.is_list:
            return torch.stack([torch.tensor(el) for el in df.values])
        return torch.from_numpy(df.values).to(self.dtype)


class ListEncoder(object):
    def __init__(self, sep=','):
        self.sep = sep

    def __call__(self, df):
        eval_df = df.apply(
            lambda x: [val for val in ast.literal_eval(x)])
        return torch.stack([torch.tensor(el) for el in eval_df.values])


class LabelEncoder(object):
    # The 'LabelEncoder' splits the raw column strings by 'sep' and converts
    # individual elements to categorical labels.
    def __init__(self, sep=','):
        self.sep = sep

    def __call__(self, df):
        genres = set(g for col in df.values for g in col.split(self.sep))
        mapping = {genre: i for i, genre in enumerate(genres)}

        x = torch.zeros(len(df), len(mapping))
        for i, col in enumerate(df.values):
            for genre in col.split(self.sep):
                x[i, mapping[genre]] = 1
        return x


class RandomValueEncoder(object):
    def __init__(self, dim=1):
        self.dim = dim

    def __call__(self, df):
        return torch.rand(len(df), self.dim)


def load_node_tensor(filename, index_col, encoders=None, **kwargs):
    df = pd.read_csv(filename, index_col=index_col, header=0)
    # Define node mapping
    mapping = {index: i for i, index in enumerate(df.index.unique())}
    # Define node features
    x = None
    if encoders is not None:
        xs = [encoder(df[col]) for col, encoder in encoders.items()]
        x = torch.cat(xs, dim=-1)
        x = x.float()

    return x, mapping


def load_edge_tensor(filename, src_index_col, src_mapping,
                     dst_index_col, dst_mapping, encoders=None, **kwargs):
    # Execute the cypher query and retrieve data from Neo4j
    df = pd.read_csv(filename, header=0)

    # Define edge index
    src = [src_mapping[index] for index in df[src_index_col]]
    dst = [dst_mapping[index] for index in df[dst_index_col]]
    edge_index = torch.tensor([src, dst])
    # Define edge features
    edge_attr = None
    if encoders is not None:
        edge_attrs = [encoder(df[col]) for col, encoder in encoders.items()]
        edge_attr = torch.cat(edge_attrs, dim=-1)

    return edge_index, edge_attr
