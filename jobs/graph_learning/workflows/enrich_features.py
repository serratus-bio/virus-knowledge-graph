from queries import gds_queries


def run(args):
    print('Creating full projection')
    G_full = gds_queries.create_projection_from_dataset(sampling_ratio=1)
    print(G_full)

    print('Mutating projection with new features')
    # gds_queries.mutate_degree_property(G_full)

    print('Writing new properties to feature store')
    gds_queries.export_projection(G_full, destination='features')
