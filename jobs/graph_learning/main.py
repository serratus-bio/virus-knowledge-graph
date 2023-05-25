import argparse

from workflows import link_prediction, query


def main(args):
    if args.workflow == 'link_prediction':
        print('Running link prediction workflow')
        link_prediction.run(args)

    if args.workflow == 'query':
        print('Running query workflow')
        query.run(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ML jobs")
    parser.add_argument(
        "-w",
        "--workflow",
        type=str,
        help="Specify workflow. Valid args: link_prediction, query",
    )
    parser.add_argument(
        "-t",
        "--task",
        type=str,
        nargs='?',
        const='all',
        help="Specify single task, defaults to full workflow",
    )
    args = parser.parse_args()
    main(args)
