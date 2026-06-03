from __future__ import annotations

import argparse
from pathlib import Path

from app.db import SessionLocal
from app.pipeline.runner import run_ingestion_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AI data center infrastructure follow-up pipeline.")
    parser.add_argument("command", choices=["run"])
    parser.add_argument(
        "--sample-dir",
        type=Path,
        default=Path("generated/sample_data"),
        help="Directory containing raw JSON sample data.",
    )
    parser.add_argument(
        "--generate-sample",
        action="store_true",
        help="Generate deterministic AI data center infrastructure sample data before running the pipeline.",
    )
    parser.add_argument("--seed", type=int, default=20260523)
    args = parser.parse_args()

    with SessionLocal() as session:
        result = run_ingestion_pipeline(
            session=session,
            sample_dir=args.sample_dir,
            generate_sample=args.generate_sample,
            seed=args.seed,
        )

    print(
        "Pipeline completed: "
        f"run_id={result.pipeline_run_id} "
        f"status={result.status} "
        f"rows_loaded={result.rows_loaded} "
        f"quality_failed_checks={result.quality_failed_checks}"
    )


if __name__ == "__main__":
    main()
