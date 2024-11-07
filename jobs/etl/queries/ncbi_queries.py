import pandas as pd
from datasources.ncbi import download_and_extract_tax_dump, parse_tax_dump


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
