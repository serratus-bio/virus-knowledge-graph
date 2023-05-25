import os
import ast

import numpy as np
import pandas as pd


FEATURE_STORE_DIR = './data/features/'


def write_to_feature_store(df, file_name=''):
    if not os.path.exists(FEATURE_STORE_DIR):
        os.makedirs(FEATURE_STORE_DIR)
    feature_file_path = FEATURE_STORE_DIR + file_name
    df.to_csv(feature_file_path)


def one_hot_encode(df_data, feature):
    categories = set(col for col in df_data[feature])
    mapping = {category: i for i, category in enumerate(categories)}
    x = pd.DataFrame(np.zeros((len(df_data), len(mapping))))
    for i, col in enumerate(df_data[feature]):
        x[i, mapping[col]] = 1
    return x


def label_encode(df_data, feature):
    categories = set(col for col in df_data[feature])
    mapping = {category: i for i, category in enumerate(categories)}
    return df_data[feature].replace(mapping)


def ordinal_encode(df_data, feature, feature_rank):
    mapping = {}
    for i, feature_value in enumerate(feature_rank):
        mapping[feature_value] = i + 1
    return df_data[feature].replace(mapping)


def encode_palmprint_fts(query_results):
    df = pd.DataFrame([dict(record) for record in query_results])
    df = pd.DataFrame().assign(
        nodeId=df['id'],
        labels=df['labels'],
        # features=df.iloc[:, 2:].apply(list, axis=1),
        # centroid=df['centroid'].astype(int),
    )
    return df


def encode_taxon_fts(query_results):
    df = pd.DataFrame([dict(record) for record in query_results])
    # TODO: use ordinal encoding to capture hierarchy in ranks (even though some are non-hierachal)
    # Supplementary Table S3:
    # https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7408187/#sup1
    return pd.DataFrame().assign(
        nodeId=df['id'],
        labels=df['labels'],
        # rank=label_encode(df, 'rank'),
        # features=df.iloc[:, 2:].apply(list, axis=1),
    )


def encode_edges(query_results):
    df = pd.DataFrame([dict(record) for record in query_results])
    return pd.DataFrame().assign(
        sourceNodeId=df['sourceNodeId'],
        targetNodeId=df['targetNodeId'],
        relationshipType=df['relationshipType'],
        weight=df['weight'],
    )
