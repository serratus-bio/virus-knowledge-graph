import ast

from queries import utils
from config.base import DIR_CFG, DATASET_CFG
from config.encoders import TAXON_RANK_LABELS

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
        dataset_cfg=None,
):
    if not dataset_cfg:
        raise ValueError("Must provide dataset_cfg")

    node_file_paths = list(
        map(
            (lambda cfg: dir_name + cfg['FILE_NAME']),
            dataset_cfg['NODE_META']
        )
    )
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
        dataset_cfg=None,
):
    if not dataset_cfg:
        raise ValueError("Must provide dataset_cfg")

    relationship_file_paths = list(
        map(
            (lambda cfg: dir_name + cfg['FILE_NAME']),
            dataset_cfg['REL_META']
        )
    )
    relationships = utils.merge_files_to_df(
        relationship_file_paths,
        select_columns=['sourceNodeId', 'targetNodeId',
                        'relationshipType', 'weight'],
    )
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
            x = torch.from_numpy(df.values).to(self.dtype)
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
    def __init__(self, sep=',', is_tensor=False, mapping=None):
        self.sep = sep
        self.is_tensor = is_tensor
        self.mapping = mapping

    def __call__(self, df):
        mapping = self.mapping
        if self.is_tensor:
            if not mapping:
                labels = set(
                    label for col in df.values
                    for label in col.split(self.sep)
                )
                mapping = {label: i for i, label in enumerate(labels)}
            x = torch.zeros(len(df), len(mapping))
            for i, col in enumerate(df.values):
                for label in col.split(self.sep):
                    x[i, mapping[label]] = 1
            return x
        if not mapping:
            labels = df[df.columns[0]].unique()
            mapping = {label: i for i, label in enumerate(labels)}
        return df.replace(mapping)


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

    if write_to_disk:
        df.to_csv(file_path, index=False)

    return df


def encode_node_properties(dataset_cfg=DATASET_CFG):
    # TODO: consider moving encoder mappings to config file (?)
    node_file_paths = list(
        map(
            (lambda cfg: cfg['FILE_NAME']),
            dataset_cfg['NODE_META']
        )
    )
    if 'taxon_nodes.csv' in node_file_paths:
        encode_features(
            filename='taxon_nodes.csv',
            write_to_disk=True,
            encoders={
                'rank': LabelEncoder(
                    is_tensor=False, mapping=TAXON_RANK_LABELS),
            }
        )

    if 'sotu_nodes.csv' in node_file_paths:
        encode_features(
            filename='sotu_nodes.csv',
            write_to_disk=True,
            encoders={
                'centroid': LabelEncoder(is_tensor=False),
            }
        )

    if 'palmprint_nodes.csv' in node_file_paths:
        encode_features(
            filename='palmprint_nodes.csv',
            write_to_disk=True,
            encoders={
                'centroid': LabelEncoder(is_tensor=False),
            }
        )


def encode_relationship_properties():
    # TODO: decide on better encoding for weight, cur using avg pidentity
    # account for both avg percent identity and high variance read counts
    raise NotImplementedError


# this is needed to support heterogenous nodes in GDS
def vectorize_features(
    filename,
    dir_name=DIR_CFG['FEATURE_STORE_DIR'],
    select_columns=[],
    write_to_disk=False,
):
    df = pd.read_csv(dir_name + filename, header=0)
    if select_columns:
        feature_columns = df[select_columns]
        df['features'] = feature_columns.apply(list, axis=1)

    if write_to_disk:
        df.to_csv(dir_name + filename, index=False)

    return df


def vectorize_node_properties(dataset_cfg=DATASET_CFG):
    node_file_paths = list(
        map(
            (lambda cfg: cfg['FILE_NAME']),
            dataset_cfg['NODE_META'],
        )
    )
    if 'taxon_nodes.csv' in node_file_paths:
        vectorize_features(
            filename='taxon_nodes.csv',
            select_columns=['rankEncoded'],
            write_to_disk=True,
        )

    if 'sotu_nodes.csv' in node_file_paths:
        vectorize_features(
            filename='sotu_nodes.csv',
            select_columns=['centroidEncoded'],
            write_to_disk=True,
        )

    if 'palmprint_nodes.csv' in node_file_paths:
        vectorize_features(
            filename='palmprint_nodes.csv',
            select_columns=['centroidEncoded'],
            write_to_disk=True,
        )
