"""Enable ``python3 -m crest`` to launch the CLI from the project root."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
