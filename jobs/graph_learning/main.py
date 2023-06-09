import argparse

from workflows import (
    make_datasets,
    link_prediction_gds,
    link_prediction_pyg,
    enrich_features,
)


def main(args):
    if args.workflow == 'make_datasets':
        print('Running dataset creation workflow')
        make_datasets.run(args)

    if args.workflow == 'link_prediction_gds':
        print('Running GDS link prediction workflow')
        link_prediction_gds.run(args)

    if args.workflow == 'link_prediction_pyg':
        print('Running Pytorch Geometric link prediction workflow')
        link_prediction_pyg.run(args)

    if args.workflow == 'enrich_features':
        print('Running feature enrichment workflow')
        enrich_features.run(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ML jobs")
    parser.add_argument(
        "-w",
        "--workflow",
        type=str,
        help="Specify workflow to run.",
    )
    parser.add_argument(
        "-t",
        "--task",
        type=str,
        nargs='?',
        const='all',
        help="Specify single task. Defaults to full workflow.",
    )
    args = parser.parse_args()
    print(args)
    main(args)
