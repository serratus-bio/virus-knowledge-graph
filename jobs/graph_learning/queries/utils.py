import ast
import os

import pandas as pd
import dask.dataframe as dd

from config.base import (
    DIR_CFG,
    MODEL_CFG,
)


def store_run_artifact(run_uid, obj, filename):
    print("Storing artifact", filename)
    results_dir = f"{DIR_CFG['RESULTS_DIR']}"\
        + f"/{MODEL_CFG['SAMPLING_RATIO']}/{run_uid}/"

    if not os.path.exists(results_dir):
        os.makedirs(results_dir, exist_ok=True)

    if isinstance(obj, pd.DataFrame) or isinstance(obj, pd.Series):
        obj.to_csv(results_dir + filename + '.csv', index=False)
    else:
        with open(results_dir + filename + '.txt', 'w') as f:
            f.write(obj.__repr__())


def df_to_ddf(df):
    return dd.from_pandas(df, chunksize=1000)


def read_ddf_from_disk(cache_file_path=''):
    try:
        df = dd.read_csv(cache_file_path, blocksize="1MB", dtype='string')
        print('Reading local cached file', cache_file_path)
        return df
    except BaseException:
        print('No local cache file found', cache_file_path)
        return None


def read_df_from_disk(file_path=''):
    try:
        df = pd.read_csv(file_path)
        print('Reading local file: ', file_path)
        return df
    except BaseException:
        print('No local file found: ', file_path)
        return pd.DataFrame()


def merge_files_to_df(file_paths, select_columns=[]):
    if not file_paths:
        return pd.DataFrame()

    return pd.concat([
        read_df_from_disk(file_path)[select_columns]
        for file_path
        in file_paths
    ]).drop_duplicates()


def merge_files_to_ddf(file_paths, select_columns=[]):
    if not file_paths:
        return dd.DataFrame()

    return dd.concat([
        read_ddf_from_disk(file_path)[select_columns]
        for file_path
        in file_paths
    ]).drop_duplicates()


def deserialize_df(df):
    if 'labels' in df:
        df['labels'] = df['labels'].apply(lambda x: ast.literal_eval(x))
    if 'features' in df:
        df['features'] = df['features'].apply(
            lambda x: [int(val) for val in ast.literal_eval(x)])
    return df


def write_ddf_to_disk(ddf, file_path=''):
    ddf.to_csv(file_path, index=False, single_file=True)
