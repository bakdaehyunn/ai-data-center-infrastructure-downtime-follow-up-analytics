from __future__ import annotations

import argparse
from pathlib import Path

from app.db import SessionLocal
from app.pipeline.runner import run_raw_ingestion_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run procurement data pipeline tasks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run raw ingestion and quality checks.")
    run_parser.add_argument(
        "--sample-dir",
        type=Path,
        default=Path("generated/sample_data"),
        help="Directory containing source-like sample JSON files.",
    )
    run_parser.add_argument(
        "--generate-sample",
        action="store_true",
        help="Generate deterministic sample data before loading raw records.",
    )
    run_parser.add_argument("--seed", type=int, default=20260523)

    args = parser.parse_args()

    if args.command == "run":
        with SessionLocal() as session:
            result = run_raw_ingestion_pipeline(
                session=session,
                sample_dir=args.sample_dir,
                generate_sample=args.generate_sample,
                seed=args.seed,
            )
        print(
            "pipeline_run_id={run_id} status={status} rows_extracted={extracted} "
            "rows_loaded={loaded} rows_rejected={rejected} failed_checks={failed_checks} "
            "core_records_loaded={core_loaded} core_records_skipped={core_skipped} "
            "analytics_records_loaded={analytics_loaded}".format(
                run_id=result.pipeline_run_id,
                status=result.status,
                extracted=result.rows_extracted,
                loaded=result.rows_loaded,
                rejected=result.rows_rejected,
                failed_checks=result.quality_failed_checks,
                core_loaded=result.core_records_loaded,
                core_skipped=result.core_records_skipped,
                analytics_loaded=result.analytics_records_loaded,
            )
        )


if __name__ == "__main__":
    main()
