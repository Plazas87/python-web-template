import argparse
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        result = subprocess.run(["alembic", "current"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            sys.exit(1)
        print(result.stdout)
        return

    subprocess.run(["alembic", "upgrade", "head"], check=True)


if __name__ == "__main__":
    main()
