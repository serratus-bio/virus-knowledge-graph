from queries import serratus_queries
from queries import graph_queries


def run(args):
    graph_queries.add_constraints()

    if args.task == 'all' or args.task == 'sra':
        print('Processing SRA')
        df_sra = serratus_queries.get_sra_df()
        graph_queries.add_sra_nodes(df_sra)

    if args.task == 'all' or args.task == 'palmprint':
        print('Processing Palmprints')
        df_palmprint = serratus_queries.get_palmprint_df()
        graph_queries.add_palmprint_nodes(df_palmprint)
        graph_queries.add_sotu_labels()
        graph_queries.add_palmprint_sotu_edges()

        df_palmprint_msa = serratus_queries.get_palmprint_msa_df()
        graph_queries.add_palmprint_msa_edges(df_palmprint_msa)

    if args.task == 'all' or args.task == 'taxon':
        print('Processing Taxons')
        df_taxon = serratus_queries.get_taxon_df()
        graph_queries.add_taxon_nodes(df_taxon)
        graph_queries.add_taxon_edges(df_taxon)

    if args.task == 'all' or args.task == 'edges':
        print('Processing heterogenous edges')
        df_sra_palmprint = serratus_queries.get_sra_palmprint_df()
        graph_queries.add_sra_palmprint_edges(df_sra_palmprint)

        df_sra_taxon = serratus_queries.get_sra_taxon_df()
        graph_queries.add_sra_taxon_edges(df_sra_taxon)

        df_palmprint_taxon_edges = \
            serratus_queries.get_palmprint_taxon_edges_df()
        graph_queries.add_palmprint_taxon_edges(df_palmprint_taxon_edges)
