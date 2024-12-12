import requests
import os
import ast

from datasources.ncbi import download_and_extract_tax_dump, parse_tax_dump

import pandas as pd
import dask.dataframe as dd

NCBI_DATA_PATH = "/mnt/graphdata/ncbi-data"

def remap_sra_taxon(df_sra, taxon_nodes, merged_nodes):
    sra_taxon = []
    patch_tax_id = {"1633896": "1723709", "0": "1"}

    def get_mapped_tax_id(tax_id):
        str_tax_id = str(row["tax_id"])
        if str_tax_id in taxon_nodes:
            return str_tax_id
        if str_tax_id in merged_nodes:
            return merged_nodes[str_tax_id]
        if str_tax_id in patch_tax_id:
            return patch_tax_id[str_tax_id]
        raise Exception("Missing tax_id, requires manual search and patch", tax_id)

    for index, row in df_sra.iterrows():
        tax_id = get_mapped_tax_id(row["tax_id"])
        sra_taxon.append({"run_id": row["run_id"], "tax_id": tax_id})

    df = pd.DataFrame(sra_taxon)
    df.to_csv("sra_taxon_edges.csv", columns=["run_id", "tax_id"], index=False)
    return pd.DataFrame(sra_taxon)


def get_taxon_nodes():
    download_and_extract_tax_dump()
    response = parse_tax_dump()
    return pd.DataFrame(response["taxon_nodes"])


def get_sra_taxon_edges(df_sra):
    download_and_extract_tax_dump()
    response = parse_tax_dump()
    return remap_sra_taxon(df_sra, response["taxon_nodes"], response["merged_nodes"])


def search_tax_id_by_name(df_taxon, taxon_name, alt_taxon_names=[]):
    ranks = [
        'species',
        'genus',
        'family',
        'order',
        # 'phylum',
        # 'kingdom',
    ]
    for rank in ranks:
        df_taxon.reset_index(inplace=True)
        df_taxon.set_index(f'tax_{rank}', inplace=True)
        taxon = df_taxon[df_taxon.index == taxon_name]
        if not taxon.empty:
            return taxon['tax_id'].values.tolist()
    
    for alt_name_obj in alt_taxon_names:
        alt_name = alt_name_obj['name']
        for rank in ranks:
            df_taxon.reset_index(inplace=True)
            df_taxon.set_index(f'tax_{rank}', inplace=True)
            taxon = df_taxon[df_taxon.index == alt_name]
            if not taxon.empty:
                return taxon['tax_id'].values.tolist()

    return None



def get_taxon_bsl_attribute(df_taxon):
    df_taxon = df_taxon.compute()

    if os.path.exists(f"{NCBI_DATA_PATH}/taxon_bsl_attribute.csv"):
        df = pd.read_csv(f"{NCBI_DATA_PATH}/taxon_bsl_attribute.csv")
        df = df.dropna(subset=['tax_ids'])
        df['tax_ids'] = df['tax_ids'].apply(lambda x: ast.literal_eval(x))

        exploded_rows = []
        for _, row in df.iterrows():
            for tax_id in row['tax_ids']:
                exploded_rows.append({
                    'tax_id': tax_id,
                    'HumanRiskGroup': row['HumanRiskGroup'],
                    'AnimalRiskGroup': row['AnimalRiskGroup'],
                })

        df = pd.DataFrame(exploded_rows)
        return dd.from_pandas(df, npartitions=10)

    url = "https://health.canada.ca/en/epathogen/search"
    
    agent_types = {
        'virus': '729010001',
        'toxin': '729010005',
        'protein': '729010008',
        'prion': '729010004',
        'parasite': '729010002',
        'panel': '729010009',
        'other': '729010010',
        'nucleic acid': '729010007',
        'fungus': '729010003',
        'cell line': '729010006',
        'bacteria': '729010000',
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-CA,en-US;q=0.7,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Referer": "https://health.canada.ca/en/epathogen",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Priority": "u=0, i",
    }

    existing_rows = 0
    if os.path.exists(f"{NCBI_DATA_PATH}/taxon_bsl_attribute.csv"):
        existing_rows = len(pd.read_csv(f"{NCBI_DATA_PATH}/taxon_bsl_attribute.csv"))
    else:
        df_headers = pd.DataFrame([], columns=[
            "name",
            "type",
            "HumanRiskGroup",
            "AnimalRiskGroup",
            "SecuritySensitiveBiologicalAgent",
            "TerrestrialAnimalPathogenUnderCFIAAuthority",
            "ContainmentLevel",
            "ConsiderationsForContainment",
            "altName",
            'tax_ids',
        ])
        df_headers.to_csv(f"{NCBI_DATA_PATH}/taxon_bsl_attribute.csv", index=False)

    processed_rows = 0
    for agent_id in agent_types.values():

        print(f"Processing agent type: {agent_id}")
        params = {
            "term": "",
            "agentType[]": agent_id,
            "terrestrialAnimalPathogenUnderCFIAAuthority": "",
            "securitySensitiveBiologicalAgent": "",
            "lang": "en",
            "format": "json",
        }
        response = requests.post(url, headers=headers, params=params)
        response.raise_for_status()
        results = response.json()
        for result_id in results['results']:
            processed_rows += 1
            if processed_rows <= existing_rows:
                continue
            
            print(f"Processing result")
            row = results['results'][result_id]
            tax_ids = search_tax_id_by_name(df_taxon, row['name'], row['altName'])
            row = {
                "name": row["name"],
                "type": row["type"],
                "HumanRiskGroup": row["HumanRiskGroup"],
                "AnimalRiskGroup": row["AnimalRiskGroup"],
                "SecuritySensitiveBiologicalAgent": row["SecuritySensitiveBiologicalAgent"],
                "TerrestrialAnimalPathogenUnderCFIAAuthority": row["TerrestrialAnimalPathogenUnderCFIAAuthority"],
                "ContainmentLevel": row["ContainmentLevel"],
                "ConsiderationsForContainment": row["ConsiderationsForContainment"],
                "altName": [
                    alt_name["name"] for alt_name in row["altName"]
                ],
                'tax_ids': tax_ids,
            }
            # write row to file
            df = pd.DataFrame([row])
            df.to_csv(f"{NCBI_DATA_PATH}/taxon_bsl_attribute.csv", index=False, mode='a', header=False)

    return dd.read_csv(f"{NCBI_DATA_PATH}/taxon_bsl_attribute.csv")
