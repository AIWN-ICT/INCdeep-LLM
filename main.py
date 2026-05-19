<<<<<<< HEAD
from __future__ import annotations

"""Unified CLI entry for INCdeep-LLM.

Examples:
  python main.py train --result-dir ./result --model-dir ./models/checkpoints
  python main.py test --model-dir ./models/examples/best_by_avg_source_send
"""

import argparse

import test
import train


def build_parser():
    """Create the top-level CLI parser.

    Returns:
        argparse.ArgumentParser: Parser with `train` and `test` subcommands.
    """
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="INCdeep-LLM command-line interface.",
        epilog=(
            "Quick examples:\n"
            "  python main.py train\n"
            "  python main.py train --model-dir ./models/checkpoints --result-dir ./result\n"
            "  python main.py test --model-dir ./models/examples/best_by_avg_source_send\n\n"
            "Tip: run 'python main.py <command> --help' for command-specific options."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        title="commands",
        description="Available workflows",
        metavar="{train,test}",
    )

    train_parser = subparsers.add_parser(
        "train",
        help="Train DQN agents from scratch",
        description="Run training loop with periodic evaluation and best-model selection.",
    )
    train_parser.set_defaults(_target="train")

    test_parser = subparsers.add_parser(
        "test",
        help="Evaluate using saved best checkpoints",
        description="Run standalone evaluation using pretrained source/relay models.",
    )
    test_parser.set_defaults(_target="test")

    return parser


def main():
    """Dispatch to training or testing entrypoint based on CLI command.

    Returns:
        None
    """
    parser = build_parser()
    args, remaining = parser.parse_known_args()

    if args.command == "train":
        train.main(remaining)
    elif args.command == "test":
        test.main(remaining)
    else:
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
=======
from __future__ import annotations

"""Unified CLI entry for INCdeep-LLM.

Examples:
  python main.py train --result-dir ./result --model-dir ./models/checkpoints
  python main.py test --model-dir ./models/examples/best_by_avg_source_send
"""

import argparse

import test
import train


def build_parser():
    """Create the top-level CLI parser.

    Returns:
        argparse.ArgumentParser: Parser with `train` and `test` subcommands.
    """
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="INCdeep-LLM command-line interface.",
        epilog=(
            "Quick examples:\n"
            "  python main.py train\n"
            "  python main.py train --model-dir ./models/checkpoints --result-dir ./result\n"
            "  python main.py test --model-dir ./models/examples/best_by_avg_source_send\n\n"
            "Tip: run 'python main.py <command> --help' for command-specific options."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        title="commands",
        description="Available workflows",
        metavar="{train,test}",
    )

    train_parser = subparsers.add_parser(
        "train",
        help="Train DQN agents from scratch",
        description="Run training loop with periodic evaluation and best-model selection.",
    )
    train_parser.set_defaults(_target="train")

    test_parser = subparsers.add_parser(
        "test",
        help="Evaluate using saved best checkpoints",
        description="Run standalone evaluation using pretrained source/relay models.",
    )
    test_parser.set_defaults(_target="test")

    return parser


def main():
    """Dispatch to training or testing entrypoint based on CLI command.

    Returns:
        None
    """
    parser = build_parser()
    args, remaining = parser.parse_known_args()

    if args.command == "train":
        train.main(remaining)
    elif args.command == "test":
        test.main(remaining)
    else:
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
>>>>>>> 7d2f6d8c28f3c5b7e47d00807eec56d14f052984
