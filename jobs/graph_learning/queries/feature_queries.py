import ast

from queries import utils
from config import DIR_CFG

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


def get_all_node_features(
        dir_name=DIR_CFG['FEATURE_STORE_DIR'],
        enriched_features=False,
):
    node_file_paths = [
        dir_name + 'palmprint_nodes.csv',
        dir_name + 'taxon_nodes.csv',
    ]
    if enriched_features:
        select_columns = ['nodeId', 'labels', 'features',
                          'degree', 'degreeWeighted']
    else:
        select_columns = ['nodeId', 'labels', 'features']

    nodes = utils.merge_files_to_df(
        node_file_paths,
        select_columns=select_columns,
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
    def __init__(self, dtype=None, is_list=False, is_tensor=False):
        self.dtype = dtype
        self.is_list = is_list
        self.is_tensor = is_tensor

    def __call__(self, df):
        if self.is_tensor:
            if self.is_list:
                return torch.stack([torch.tensor(el) for el in df.values])
            return torch.from_numpy(df.values).to(self.dtype)
        else:
            return df


class ListEncoder(object):
    def __init__(self, sep=',', is_tensor=False):
        self.sep = sep
        self.is_tensor = is_tensor

    def __call__(self, df):
        eval_df = df.apply(
            lambda x: [val for val in ast.literal_eval(x)])
        return torch.stack([torch.tensor(el) for el in eval_df.values])


class LabelEncoder(object):
    # The 'LabelEncoder' splits the raw column strings by 'sep' and converts
    # individual elements to categorical labels.
    def __init__(self, sep=',', is_tensor=False):
        self.sep = sep
        self.is_tensor = is_tensor

    def __call__(self, df):
        if self.is_tensor:
            labels = set(
                label for col in df.values for label in col.split(self.sep))
            mapping = {label: i for i, label in enumerate(labels)}
            x = torch.zeros(len(df), len(mapping))
            for i, col in enumerate(df.values):
                for label in col.split(self.sep):
                    x[i, mapping[label]] = 1
            return x
        else:
            labels = df[df.columns[0]].unique()
            mapping = {label: i for i, label in enumerate(labels)}
            return df.replace(mapping)


class RandomValueEncoder(object):
    def __init__(self, dim=1, is_tensor=False):
        self.dim = dim
        self.is_tensor = is_tensor

    def __call__(self, df):
        return torch.rand(len(df), self.dim)


class MinMaxNormalizeEncoder(object):
    def __init__(self, dim=1, is_tensor=False):
        self.dim = dim
        self.is_tensor = is_tensor

    def __call__(self, df):
        if self.is_tensor:
            raise NotImplementedError
        else:
            series = df[df.columns[0]]
            max_ft = series.max()
            min_ft = series.min()
            if min_ft == max_ft:
                return df
            df[df.columns[0]] = (series - min_ft) / (max_ft - min_ft)
            return df


def encode_features(
        filename,
        dir_name=DIR_CFG['FEATURE_STORE_DIR'],
        encoders=None,
        write_to_disk=False
):
    file_path = dir_name + filename
    df = pd.read_csv(file_path, header=0)

    if encoders is not None:
        encoded_cols = pd.concat([
            encoder(df[[col]])
            for col, encoder
            in encoders.items()
        ])
        encoded_cols = encoded_cols.add_suffix('Encoded')
        df[encoded_cols.columns.values] = encoded_cols
        # df = pd.concat([df, encoded_cols], axis=1)

    if write_to_disk:
        df.to_csv(file_path, index=False)

    return df


def encode_node_properties():
    encode_features(
        filename='taxon_nodes.csv',
        write_to_disk=True,
        encoders={
            'rank': LabelEncoder(is_tensor=False),
        }
    )
    encode_features(
        filename='palmprint_nodes.csv',
        write_to_disk=True,
        encoders={
            'centroid': LabelEncoder(is_tensor=False),
        }
    )


def encode_relationship_properties():
    # TODO: use mean normalization to account for high variance in read counts
    df = encode_features(
        filename='has_host_edges.csv',
        write_to_disk=False,
        encoders={
            'count': MinMaxNormalizeEncoder(
                is_tensor=False),
        }
    )
    df.columns = ['weight' if x ==
                  'countEncoded' else x for x in df.columns]
    df.to_csv(DIR_CFG['FEATURE_STORE_DIR'] +
              'has_host_edges.csv', index=False)


def load_node_tensor(filename, index_col, encoders=None):
    df = pd.read_csv(filename, index_col=index_col, header=0)
    mapping = {index: i for i, index in enumerate(df.index.unique())}
    x = None
    if encoders is not None:
        xs = [encoder(df[col]) for col, encoder in encoders.items()]
        x = torch.cat(xs, dim=-1)
        x = x.float()

    return x, mapping


def load_edge_tensor(filename, src_index_col, src_mapping,
                     dst_index_col, dst_mapping, encoders=None):
    df = pd.read_csv(filename, header=0)
    src = [src_mapping[index] for index in df[src_index_col]]
    dst = [dst_mapping[index] for index in df[dst_index_col]]
    edge_index = torch.tensor([src, dst])
    edge_attr = None
    if encoders is not None:
        edge_attrs = [encoder(df[col]) for col, encoder in encoders.items()]
        edge_attr = torch.cat(edge_attrs, dim=-1)

    return edge_index, edge_attr


# to support heterogenous nodes in GDS, use vectorized "feature" column
def vectorize_features(
    filename,
    dir_name=DIR_CFG['FEATURE_STORE_DIR'],
    write_to_disk=False,
    select_columns=[],
):
    df = pd.read_csv(dir_name + filename, header=0)
    if select_columns:
        feature_columns = df[select_columns]
        df['features'] = feature_columns.apply(list, axis=1)

    if write_to_disk:
        df.to_csv(dir_name + filename, index=False)

    return df


def vectorize_node_properties():
    vectorize_features(
        filename='taxon_nodes.csv',
        write_to_disk=True,
        select_columns=['rankEncoded']
    )
    vectorize_features(
        filename='palmprint_nodes.csv',
        write_to_disk=True,
        select_columns=['centroidEncoded']
    )
