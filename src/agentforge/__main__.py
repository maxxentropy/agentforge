"""Allow running as `python -m agentforge`."""

import sys

from agentforge.cli.main import cli


def main():
    """Main entry point with exception handling."""
    try:
        cli()
    except KeyboardInterrupt:
        print("\nOperation cancelled.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
