import argparse

from workflows import (
    make_datasets,
    link_prediction_gds,
    link_prediction_pyg,
    link_prediction_nx,
    graphrag,
)


def main(args):
    if args.workflow == 'make_datasets':
        print('Running dataset creation workflow')
        make_datasets.run()

    if args.workflow == 'link_prediction_gds':
        print('Running GDS link prediction workflow')
        link_prediction_gds.run()

    if args.workflow == 'link_prediction_pyg':
        print('Running Pytorch Geometric link prediction workflow')
        link_prediction_pyg.run()

    if args.workflow == 'link_prediction_nx':
        print('Running NetworkX traditional link prediction workflow')
        link_prediction_nx.run()

    if args.workflow == 'graphrag':
        print('Running GraphRAG workflow')
        graphrag.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ML jobs")
    parser.add_argument(
        "-w",
        "--workflow",
        type=str,
        help="Specify workflow to run.",
    )
    args = parser.parse_args()
    print(args)
    main(args)
