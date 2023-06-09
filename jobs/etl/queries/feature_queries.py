import os

import numpy as np
import pandas as pd


FEATURE_STORE_DIR = '/mnt/graphdata/features/'


def write_to_feature_store(df, file_name=''):
    if not os.path.exists(FEATURE_STORE_DIR):
        os.makedirs(FEATURE_STORE_DIR)
    feature_file_path = FEATURE_STORE_DIR + file_name
    df.to_csv(feature_file_path, index=False)


def bool_encode(df_col):
    return df_col.astype(int)


def one_hot_encode(df_col):
    categories = set(col for col in df_col)
    mapping = {category: i for i, category in enumerate(categories)}
    x = pd.DataFrame(np.zeros((len(df_col), len(mapping))))
    for i, col in enumerate(df_col):
        x[i, mapping[col]] = 1
    return x


def label_encode(df_col):
    categories = set(col for col in df_col)
    mapping = {category: i for i, category in enumerate(categories)}
    return df_col.replace(mapping)


def ordinal_encode(df_data, col_name, order):
    mapping = {}
    for i, val in enumerate(order):
        mapping[val] = i + 1
    return df_data[col_name].replace(mapping)


def vectorize_features(df, encoders={}):
    # apply encoder to selected columns and merge into single column of lists
    encoded_column = pd.concat([encoders[col](df[col])
                               for col in encoders.keys()], axis=1)
    encoded_column = encoded_column.apply(list, axis=1)
    return encoded_column


def min_max_normalize_features(df_col):
    max_ft = df_col.max()
    min_ft = df_col.min()
    if min_ft == max_ft:
        return df_col
    return (df_col - min_ft) / (max_ft - min_ft)


def encode_palmprint_fts(query_results):
    df = pd.DataFrame([dict(record) for record in query_results])
    df = pd.DataFrame().assign(
        nodeId=df['id'],
        appId=df['palmId'],
        labels=df['labels'],
        centroid=df['centroid'],
        features=vectorize_features(df, {'centroid': bool_encode}),
    )
    return df


def encode_taxon_fts(query_results):
    df = pd.DataFrame([dict(record) for record in query_results])
    # TODO: use ordinal encoding to capture hierarchy in ranks
    # Supplementary Table S3:
    # https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7408187/#sup1
    return pd.DataFrame().assign(
        nodeId=df['id'],
        appId=df['taxId'],
        labels=df['labels'],
        rank=df['rank'],
        features=vectorize_features(df, {'rank': label_encode}),
    )


def encode_edges(query_results):
    df = pd.DataFrame([dict(record) for record in query_results])
    return pd.DataFrame().assign(
        sourceNodeId=df['sourceNodeId'],
        targetNodeId=df['targetNodeId'],
        sourceAppId=df['sourceAppId'],
        targetAppId=df['targetAppId'],
        relationshipType=df['relationshipType'],
        weight=min_max_normalize_features(df['weight']),
        weightUnscaled=df['weight'],
    )
