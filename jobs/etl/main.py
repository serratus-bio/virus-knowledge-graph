from queries import serratus_queries
from queries import ncbi_queries
from queries import graph_queries
import argparse


def main(args):
    graph_queries.add_constraints()

    if args.type == 'all' or args.type == 'sra':
        df_sra = serratus_queries.get_sra_df()
        graph_queries.add_sra_nodes(df_sra)
        graph_queries.add_sotu_labels(df_sra)

    if args.type == 'all' or args.type == 'palmprint':
        df_palmprint = serratus_queries.get_palmprint_df()
        graph_queries.add_palmprint_nodes(df_palmprint)
        graph_queries.add_palmprint_sotu_edges()
        df_palmprint_msa = serratus_queries.get_palmprint_msa_df()
        graph_queries.add_palmprint_msa_edges(df_palmprint_msa)
    
    if args.type == 'all' or args.type == 'taxon':
        df_taxon = serratus_queries.get_taxon_df()
        graph_queries.add_taxon_nodes(df_taxon)
        graph_queries.add_taxon_edges(df_taxon)

    if args.type == 'all' or args.type == 'edges':
        df_sra_palmprint = serratus_queries.get_sra_palmprint_df()
        graph_queries.add_sra_palmprint_edges(df_sra_palmprint)

        df_sra_taxon = serratus_queries.get_sra_taxon_df()
        graph_queries.add_sra_taxon_edges(df_sra_taxon)

        df_palmprint_taxon_edges = serratus_queries.get_palmprint_taxon_edges_df()
        graph_queries.add_palmprint_taxon_edges(df_palmprint_taxon_edges)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ETL jobs")
    parser.add_argument(
        "-t",
        "--type",
        type=str,
        help="Run subset of full ETL. Valid args: all, sra, palmprint, taxon"
    )
    args = parser.parse_args()
    main(args)
