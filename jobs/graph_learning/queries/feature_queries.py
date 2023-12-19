import ast

from queries import utils
from config.base import DIR_CFG, DATASET_CFG

import torch
import pandas as pd


# Ordinal encoding of taxonomy rank hierarchy. See table S3:
# https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7408187/#sup1
TAXON_RANK_LABELS = {
    'no rank': 0,
    'environmental samples': 0,
    'unclassified sequences': 0,
    'unclassified': 0,
    'incertae sedis': 0,
    'clade': 0,
    'superkingdom': 1,
    'kingdom': 2,
    'subkingdom': 3,
    'superphylum': 4,
    'superdivision': 4,
    'phylum': 5,
    'division': 5,
    'subphylum': 6,
    'subdivision': 6,
    'infraphylum': 7,
    'infradivision': 7,
    'superclass': 8,
    'class': 9,
    'subclass': 10,
    'infraclass': 11,
    'cohort': 12,
    'subcohort': 13,
    'superorder': 14,
    'order': 15,
    'suborder': 16,
    'infraorder': 17,
    'parvorder': 18,
    'superfamily': 19,
    'family': 20,
    'subfamily': 21,
    'tribe': 22,
    'subtribe': 23,
    'genus': 24,
    'subgenus': 25,
    'section': 26,
    'subsection': 27,
    'series': 28,
    'subseries': 29,
    'species group': 30,
    'species subgroup': 31,
    'species': 32,
    'forma specialis': 33,
    'special form': 33,
    'subspecies': 34,
    'varietas': 35,
    'morph': 35,
    'form': 35,
    'subvariety': 36,
    'forma': 37,
    'serogroup': 38,
    'pathogroup': 38,
    'serotype': 39,
    'biotype': 39,
    'genotype': 39,
    'strain': 40,
    'isolate': 41,
}


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
        dataset_cfg=DATASET_CFG,
        select_columns=['nodeId', 'labels', 'features']
):
    if not dataset_cfg:
        raise ValueError("Must provide dataset_cfg")

    node_file_paths = list(
        map(
            (lambda cfg: dir_name + cfg['FILE_NAME']),
            dataset_cfg['NODE_TYPES']
        )
    )
    nodes = utils.merge_files_to_df(
        node_file_paths,
        select_columns=select_columns,
    )
    nodes = utils.deserialize_df(nodes)
    nodes.set_index('nodeId')
    return nodes


def get_node_mapping(dataset_cfg=DATASET_CFG):
    return get_all_node_features(dataset_cfg=dataset_cfg,
                                 select_columns=['nodeId', 'appId'])


def get_all_relationship_features(
        dir_name=DIR_CFG['FEATURE_STORE_DIR'],
        dataset_cfg=None,
):
    if not dataset_cfg:
        raise ValueError("Must provide dataset_cfg")

    relationship_file_paths = list(
        map(
            (lambda cfg: dir_name + cfg['FILE_NAME']),
            dataset_cfg['REL_TYPES']
        )
    )
    relationships = utils.merge_files_to_df(
        relationship_file_paths,
        select_columns=['sourceNodeId', 'targetNodeId',
                        'relationshipType', 'weight'],
    )
    return relationships


def init_nodes_with_embeddings(df_nodes, embedding_type):
    dir_name = DIR_CFG['EMBEDDINGS_DIR']
    df_emb = dd.Dataframe()

    df_nodes = df_nodes.merge(

    )


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
        dir_name=DIR_CFG['QUERY_CACHE_DIR'],
        encoders=None,
        write_to_disk=False
):
    file_path = dir_name + filename
    df = pd.read_csv(file_path, header=0, index_col=False)

    if encoders is not None:
        encoded_cols = pd.concat([
            encoder(df[[col]])
            for col, encoder
            in encoders.items()
        ], axis=1)
        encoded_cols = encoded_cols.add_suffix('Encoded')
        df[encoded_cols.columns.values] = encoded_cols

    if write_to_disk:
        df.to_csv(file_path, index=False)

    return df


def encode_node_properties(dataset_cfg=DATASET_CFG):
    # TODO: consider moving encoder mappings to config file
    node_file_paths = list(
        map(
            (lambda cfg: cfg['FILE_NAME']),
            dataset_cfg['NODE_TYPES']
        )
    )

    if 'taxon_nodes.csv' in node_file_paths:
        encode_features(
            filename='taxon_nodes.csv',
            write_to_disk=True,
            encoders={
                'rank': LabelEncoder(
                    is_tensor=False, mapping=TAXON_RANK_LABELS),
                'hasParentDegree': IdentityEncoder(is_tensor=False),
            }
        )

    if 'sotu_nodes.csv' in node_file_paths:
        encode_features(
            filename='sotu_nodes.csv',
            write_to_disk=True,
            encoders={
                'numPalmprints': IdentityEncoder(is_tensor=False),
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

    if 'tissue_nodes.csv' in node_file_paths:
        encode_features(
            filename='tissue_nodes.csv',
            write_to_disk=True,
            encoders={
                'hasParentDegree': IdentityEncoder(is_tensor=False),
            }
        )


def encode_relationship_properties():
    # TODO: decide on better encoding for weight, cur using avg pidentity
    # account for both avg percent identity and high variance read counts
    raise NotImplementedError


# this is needed to support heterogenous nodes in GDS
def vectorize_features(
    filename,
    dir_name=DIR_CFG['QUERY_CACHE_DIR'],
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
            dataset_cfg['NODE_TYPES'],
        )
    )
    if 'taxon_nodes.csv' in node_file_paths:
        vectorize_features(
            filename='taxon_nodes.csv',
            select_columns=['hasParentDegreeEncoded'],
            write_to_disk=True,
        )

    if 'sotu_nodes.csv' in node_file_paths:
        vectorize_features(
            filename='sotu_nodes.csv',
            select_columns=['numPalmprintsEncoded'],
            write_to_disk=True,
        )

    if 'palmprint_nodes.csv' in node_file_paths:
        vectorize_features(
            filename='palmprint_nodes.csv',
            select_columns=['centroidEncoded'],
            write_to_disk=True,
        )

    if 'tissue_nodes.csv' in node_file_paths:
        vectorize_features(
            filename='tissue_nodes.csv',
            select_columns=['hasParentDegreeEncoded'],
            write_to_disk=True,
        )
