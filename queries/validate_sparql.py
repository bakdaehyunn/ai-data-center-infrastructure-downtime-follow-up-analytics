from pathlib import Path

from rdflib.plugins.sparql.processor import prepareQuery


def main() -> None:
    query_paths = sorted(Path("queries").glob("**/*.rq"))
    if not query_paths:
        raise SystemExit("No SPARQL query files found under queries")

    for path in query_paths:
        prepareQuery(path.read_text(encoding="utf-8"))
        print(f"parsed: {path}")


if __name__ == "__main__":
    main()
