import argparse

from workflows import (
    sra_to_sql,
    sql_to_graph,
    graph_to_projection,
)


def main(args):
    if args.workflow == 'sra_to_sql':
        print('Running workflow: SRA -> SQL')
        sra_to_sql.run()

    if args.workflow == 'sql_to_graph':
        print('Running workflow: SQL -> Neo4j ')
        sql_to_graph.run()

    if args.workflow == 'graph_to_projection':
        print('Running workflow: Neo4j -> graph projection')
        graph_to_projection.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ETL jobs")
    parser.add_argument(
        "-w",
        "--workflow",
        type=str,
        help="Specify workflow. Valid args: sql_to_graph, graph_to_projection",
    )
    args = parser.parse_args()
    print(args)
    main(args)
