from queries import serratus_queries
from queries import ncbi_queries
from queries import graph_queries


def main():
    print("Extracting from datasources")
    df_sra = serratus_queries.get_sra_df()
    df_palmprint = serratus_queries.get_palmprint_df()
    df_sra_palmprint = serratus_queries.get_sra_palmprint_df()
    df_palmprint_msa = serratus_queries.get_palmprint_msa_df()
    df_taxon = ncbi_queries.get_taxon_nodes()
    df_sra_taxon = serratus_queries.get_sra_taxon_df()

    print("Transforming")
    df_sra_taxon = ncbi_queries.transform_sra_taxon(df_sra_taxon)

    print("Loading into graph")
    graph_queries.add_constraints()
    graph_queries.add_sra_nodes(df_sra)
    graph_queries.add_palmprint_nodes(df_palmprint)
    graph_queries.add_sotu_labels(df_sra)
    graph_queries.add_palmprint_msa_edges(df_palmprint_msa)
    graph_queries.add_palmprint_sotu_edges()
    graph_queries.add_sra_palmprint_edges(df_sra_palmprint)
    graph_queries.add_taxon_nodes(df_taxon)
    graph_queries.add_taxon_edges(df_taxon)
    graph_queries.add_taxon_edges(df_taxon)


if __name__ == "__main__":
    main()
