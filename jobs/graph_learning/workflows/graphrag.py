import json
import os
from concurrent.futures import (
    ProcessPoolExecutor,
    as_completed,
)

from queries import (
    gds_queries,
    logan_queries,
    oai_queries,
)
from config.base import DIR_CFG

import pandas as pd


USE_MULTIPROCESSING = True


def process_handler(community, run_str):
    print(f"Processing community {community}")
    sra_data = gds_queries.get_sra_data(run_str)
    geo_attr_values = gds_queries.get_top_nested(sra_data['geoAttributeValues'], 10)
    geo_biomes = gds_queries.get_top_nested(sra_data['geoBiomeNames'], 10)
    bioproject_ids = sra_data['bioproject'][0]
    bioproject_titles = sra_data['bioProjectTitles'][0]
    bioproject_desc = sra_data['bioProjectDescriptions'][0]
    stat_host_counts = gds_queries.get_stat_host_counts(run_str)
    host_label_counts = gds_queries.get_host_label_counts(run_str)
    disease_counts = gds_queries.get_disease_counts(run_str)
    tissue_counts = gds_queries.get_tissue_counts(run_str)
    sotu_species_counts = gds_queries.get_sotu_species_counts(run_str)
    sotu_family_counts = gds_queries.get_sotu_family_counts(run_str)

    community_summary_str = oai_queries.get_community_summary(
        geo_attr_values,
        geo_biomes,
        bioproject_ids,
        bioproject_titles,
        bioproject_desc,
        stat_host_counts,
        host_label_counts,
        disease_counts,
        tissue_counts,
        sotu_species_counts,
        sotu_family_counts,
    )
    community_summary_str, community_summary = oai_queries.try_parse_json_object(community_summary_str)
    community_summary['community'] = community
    sotu_families = gds_queries.get_sotu_family_counts(run_str, limit=100)
    sotu_families = sotu_families['family'].tolist()
    top_mwas_results = logan_queries.get_mwas_results(bioproject_ids, sotu_families)
    community_summary['mwas'] = top_mwas_results
    return community_summary


def run():
    data_dir = DIR_CFG['GRAPHRAG_DIR']

    print("Creating full heterogenous projection")
    projection_name = "heterogenous_projection"
    projection = gds_queries.create_heterogenous_projection(projection_name)

    print("Creating Leiden communities")
    communities = gds_queries.create_leiden_communities(projection_name, edge_weight_property="weight")

    print("Get run to community mapping")
    run_to_community_df = gds_queries.get_run_to_community_df(communities, data_dir)

    print("Write communities to Logan db")
    filename = f"{data_dir}/run_to_community.csv"
    logan_queries.write_community_labels(filename)

    print("Processing community summaries")
    run_to_community_df = pd.read_csv(filename)
    run_to_community_df = run_to_community_df.set_index('run')
    palm_virome_runs = logan_queries.get_sotu_to_run(data_dir)
    run_to_community_df = run_to_community_df[run_to_community_df.index.isin(palm_virome_runs['run'])]
    unique_communities = run_to_community_df['community_id'].value_counts().index.unique()

    existing_summaries = []
    if os.path.exists(f"{data_dir}/virome_community_summaries.json"):
        with open(f'{data_dir}/virome_community_summaries.json', 'r') as f:
            community_summaries = json.load(f)
            community_summaries = pd.DataFrame(community_summaries)
            existing_summaries = community_summaries['community'].unique()
            existing_summaries = [int(community) for community in existing_summaries]

    unique_communities = [community for community in unique_communities if community not in existing_summaries]
    print(f"Processing {len(unique_communities)} communities")

    results = []

    if USE_MULTIPROCESSING:
        max_workers = 10
        with ProcessPoolExecutor(max_workers) as executor:
            futures = []
            for community in unique_communities:
                run_list = run_to_community_df[run_to_community_df['community_id'] == community].index
                run_str = ','.join([f"'{run}'" for run in run_list])
                future = executor.submit(process_handler, community, run_str)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"Error: {e}")
    else:
        for community in unique_communities:
            try:
                run_list = run_to_community_df[run_to_community_df['community_id'] == community].index
                run_str = ','.join([f"'{run}'" for run in run_list])
                result = process_handler(community, run_str)
                results.append(result)
            except Exception as e:
                print(f"Error: {e}")



    print('Writing results to disk')
    columns = ['community', 'title', 'label', 'summary', 'findings', 'mwas']
    community_summaries = pd.DataFrame(results, columns=columns)
    community_summaries = community_summaries.dropna()

    community_summaries = community_summaries.to_dict(orient='records')

    # merge with existing summaries if running multiple times
    # if os.path.exists(f"{data_dir}/virome_community_summaries.json"):
    #     with open(f'{data_dir}/virome_community_summaries.json', 'r') as f:
    #         existing_summaries = json.load(f)            
    #         existing_summaries.extend(community_summaries)
    #         community_summaries = existing_summaries

    with open(f'{data_dir}/virome_community_summaries.json', 'w') as f:
        json.dump(community_summaries, f, indent=4)

    print(f"Finished processing {len(results)}/{len(unique_communities)} communities")
