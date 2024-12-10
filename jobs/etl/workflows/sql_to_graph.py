from queries import (
    serratus_queries,
    logan_queries,
    sra_queries,
    graph_queries,
    owl_queries,
)


def run():
    graph_queries.add_constraints()

    print("Processing SRA runs")
    df_sra = serratus_queries.get_sra_df()
    graph_queries.add_sra_nodes(df_sra)

    print("Processing BioProjects")
    df_bioproject = logan_queries.get_bioproject_df()
    graph_queries.add_bioproject_nodes(df_bioproject)

    print("Processing Palmprints")
    df_palmprint = serratus_queries.get_palmprint_df()
    graph_queries.add_palmprint_nodes(df_palmprint)
    graph_queries.add_sotu_labels()
    df_palmprint_sotu = serratus_queries.get_palmprint_sotu_df()
    graph_queries.add_palmprint_sotu_edges(df_palmprint_sotu)
    df_palmprint_msa = serratus_queries.get_palmprint_msa_df()
    graph_queries.add_palmprint_msa_edges(df_palmprint_msa)

    print("Processing Taxons")
    df_taxon = serratus_queries.get_taxon_df()
    graph_queries.add_taxon_nodes(df_taxon)
    graph_queries.add_taxon_edges(df_taxon)

    print("Processing Tissues")
    df_tissue_nodes = owl_queries.get_tissue_nodes_df()
    graph_queries.add_tissue_nodes(df_tissue_nodes)
    df_tissue_edges = owl_queries.get_tissue_edges_df()
    graph_queries.add_tissue_edges(df_tissue_edges)
    df_sra_tissue = serratus_queries.get_sra_tissue_df()
    graph_queries.add_sra_tissue_edges(df_sra_tissue)

    print('Processing Diseases')
    df_disease_nodes = owl_queries.get_disease_nodes_df()
    graph_queries.add_disease_nodes(df_disease_nodes)
    df_disease_edges = owl_queries.get_disease_edges_df()
    graph_queries.add_disease_edges(df_disease_edges)
    df_sra_disease = sra_queries.get_biosample_disease_df()
    graph_queries.add_sra_disease_edges(df_sra_disease)

    print('Processing heterogenous edges')
    df_sra_palmprint = serratus_queries.get_sra_palmprint_df()
    graph_queries.add_sra_palmprint_edges(df_sra_palmprint)
    graph_queries.add_sra_has_sotu_edges()

    df_sra_taxon = serratus_queries.get_sra_has_host_metadata_df()
    graph_queries.add_sra_has_host_metadata_edges(df_sra_taxon)

    df_sra_taxon = serratus_queries.get_sra_has_host_stat_df()
    graph_queries.add_sra_has_host_stat_edges(df_sra_taxon)

    df_palmprint_taxon_edges = serratus_queries.get_palmprint_taxon_edges_df()
    graph_queries.add_palmprint_taxon_edges(df_palmprint_taxon_edges)

    print("Set BioSample attribute")
    df_biosample = logan_queries.get_biosample_df()
    graph_queries.add_biosample_attribute(df_biosample)

    print("Set BioSample sex attribute")
    df_biosample_sex = logan_queries.get_biosample_sex_df()
    graph_queries.add_biosample_sex_attribute(df_biosample_sex)

    print("Set BioSample geo attribute")
    df_biosample_geo = logan_queries.get_biosample_geo_df()
    graph_queries.add_biosample_geo_attribute(df_biosample_geo)

    print("Set default edge weight")
    graph_queries.set_default_edge_weight()

    print("Set OpenVirome label")
    df_palm_virome_sotu = logan_queries.get_palm_virome_sotu_df()
    df_palm_virome_run = logan_queries.get_palm_virome_run_df()
    df_palm_virome_bioproject = logan_queries.get_palm_virome_bioproject_df()

    graph_queries.add_open_virome_labels(df_palm_virome_sotu, df_palm_virome_run, df_palm_virome_bioproject)
