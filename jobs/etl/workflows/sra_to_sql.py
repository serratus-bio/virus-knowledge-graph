import os
from concurrent.futures import (
    ProcessPoolExecutor,
    as_completed,
)

from queries import (
    logan_queries,
    sra_queries,
    owl_queries,
)


USE_MULTIPROCESSING = True


def process_handler(args):
    (
        partition,
        index,
        onto_matcher,
        onto_tokenizer,
        onto_map,
        onto_map_inverse,
        onto_nlp,
    ) = args

    fname = f"/mnt/graphdata/ncbi-data/extracted_data/biosample_disease_{index}.csv"
    if os.path.exists(fname):
        print(f"Skipping partition {index} as file {fname} already exists")
        return fname

    matches_dict = sra_queries.match_ontology_terms(
        partition, onto_matcher, onto_tokenizer, onto_nlp
    )
    fname = sra_queries.write_to_disc(matches_dict, onto_map, onto_map_inverse, index)
    print(f"Wrote to {fname}")
    return fname


def run():
    biosamples_df = sra_queries.get_biosamples_df()
    print(f"Number of partitions: {biosamples_df.npartitions}")

    onto_terms, onto_map, onto_map_inverse = owl_queries.get_disease_to_ontology()
    onto_matcher, onto_tokenizer, onto_nlp = owl_queries.get_disease_ontology_matcher(
        onto_terms
    )
    args = [
        (
            partition,
            index,
            onto_matcher,
            onto_tokenizer,
            onto_map,
            onto_map_inverse,
            onto_nlp,
        )
        for index, partition in enumerate(biosamples_df.to_delayed())
    ]

    cpu_count = os.cpu_count()
    max_workers = min(cpu_count - 3, len(args))
    print(f"Number of CPUs: {cpu_count}, Max workers: {max_workers}")

    results = []

    if USE_MULTIPROCESSING:
        with ProcessPoolExecutor(max_workers) as executor:
            futures = [executor.submit(process_handler, arg) for arg in args]
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    print(f"Finished processing partition {result}")
                except Exception as e:
                    print(f"Error: {e}")
    else:
        for arg in args:
            result = process_handler(arg)
            results.append(result)

    print(f"Finished processing {len(results)} partitions")
    sra_queries.get_biosample_disease_df()
    logan_queries.write_biosample_disease()
