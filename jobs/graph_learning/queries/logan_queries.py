import os

from datasources.psql import (
    get_logan_read_connection,
    get_logan_write_connection,
)

import pandas as pd
import requests


def get_sotu_to_run(data_dir):
    if os.path.exists(f'{data_dir}/sotu_to_run.csv'):
        sotu_to_run = pd.read_csv(f'{data_dir}/sotu_to_run.csv')
        return sotu_to_run
    conn = get_logan_read_connection()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT sotu, run as run FROM palm_virome')
    rows = cur.fetchall()
    sotu_to_run = pd.DataFrame(rows, columns=['sotu', 'run'])
    sotu_to_run.to_csv(f'{data_dir}/sotu_to_run.csv', index=False)
    return sotu_to_run


def write_community_labels(filename):
    conn = get_logan_write_connection()
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS public.virome_community CASCADE')
    cursor.execute('''
        CREATE TABLE public.virome_community (
            run VARCHAR,
            community_id VARCHAR,
            PRIMARY KEY (run, community_id)
        )
    ''')
    conn.commit()

    copy_sql = """
        COPY public.virome_community (run, community_id)
        FROM stdin WITH CSV HEADER
        DELIMITER as ','
    """
    with open(filename, 'r') as f:
        try:
            cursor.copy_expert(sql=copy_sql, file=f)
            conn.commit()
        except Exception as error:
            print("Error: %s" % error)
            conn.rollback()
            cursor.close()
            return error

    cursor.execute('''
        CREATE INDEX virome_community_run_idx
        ON public.virome_community (run)
    ''')
    conn.commit()

    cursor.execute('''
        CREATE INDEX virome_community_id_idx
        ON public.virome_community (community_id)
    ''')
    conn.commit()

    cursor.execute('''
        GRANT SELECT ON public.virome_community TO public_reader
    ''')
    conn.commit()

    cursor.execute('''
        GRANT SELECT ON public.virome_community TO open_virome
    ''')
    conn.commit()

    cursor.execute('''
        DROP MATERIALIZED VIEW IF EXISTS public.ov_counts_virome_community
    ''')

    cursor.execute('''
        CREATE MATERIALIZED VIEW public.ov_counts_virome_community AS
        SELECT 
            a.name, COUNT(*) as count, ov.has_virus AS virus_only
        FROM  (
                   SELECT run as acc, community_id as name
                   FROM public.virome_community
            ) as a
            JOIN (
                    SELECT ov_identifiers.run_id AS acc, 
                    ov_identifiers.has_virus
                    FROM ov_identifiers
            ) as ov 
            ON a.acc = ov.acc
        GROUP BY a.name, ov.has_virus
        ORDER BY (count(*)) DESC
        WITH DATA
    ''')
    conn.commit()

    cursor.execute('''
        GRANT SELECT ON public.ov_counts_virome_community TO public_reader
    ''')
    conn.commit()

    cursor.execute('''
        GRANT SELECT ON public.ov_counts_virome_community TO open_virome
    ''')
    conn.commit()

    conn.close()
    return True


def get_mwas_results(bioprojects, virus_families, k=5):
    url = 'https://zrdbegawce.execute-api.us-east-1.amazonaws.com/prod/mwas'
    headers = {
        'Accept': '*/*',
        'Referer': 'https://openvirome.com/',
        'content-type': 'application/json',
        'Origin': 'https://openvirome.com',
        'Connection': 'keep-alive',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
    }
    payload = {
        "idColumn": "bioproject",
        "ids": bioprojects[0:500],
        "idRanges": [],
        "virusFamilies": virus_families, 
        "pageStart": 0,
        "pageEnd": 100,
    }

    keep_columns = [
        'bioproject',
        'family',
        'metadata_field',
        'metadata_value',
        'p_value',
        'fold_change',
        'taxSpecies',
        'num_true',
        'num_false',
    ]
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  
        response_json = response.json()
        response_json = sorted(response_json, key=lambda x: float(x['p_value']))
        response_json = response_json[:k]
        response_json = [{k: v for k, v in d.items() if k in keep_columns} for d in response_json]
        return response_json
    except Exception as e:
        print(e)
        return []
    