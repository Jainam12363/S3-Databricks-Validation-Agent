
import json
from pathlib import Path

from src.s3_reader import read_source_data
from src.databricks_reader import read_target_data
from src.data_preprocessor import normalize_records
from src.validation_engine import run_validation
from src.report_generator import (
    build_report_summary,
    generate_html_report
)
from src.request_validator import validate_validation_request


PROJECT_ROOT = Path(__file__).resolve().parent.parent


# --------------------------------------------------
# Load and validate incoming requests
# --------------------------------------------------

def load_validation_request(request_input):
    """
    Accept either:
    1. A JSON file path.
    2. A Python dictionary containing a validation request.

    Validate the request before returning it.
    """

    if isinstance(request_input, dict):
        request = request_input.copy()

    elif isinstance(request_input, (str, Path)):
        request_path = Path(request_input)

        if not request_path.is_absolute():
            request_path = PROJECT_ROOT / request_path

        request_path = request_path.resolve()

        if not request_path.is_relative_to(PROJECT_ROOT):
            raise ValueError(
                "Request file must be located inside the project directory."
            )

        if not request_path.is_file():
            raise FileNotFoundError(
                f"Validation request file not found: {request_path}"
            )

        with open(request_path, "r", encoding="utf-8") as file:
            request = json.load(file)

    else:
        raise TypeError(
            "Request must be a JSON file path or a Python dictionary."
        )

    return validate_validation_request(
        request,
        PROJECT_ROOT
    )


# --------------------------------------------------
# Execute validation
# --------------------------------------------------

def execute_validation(request_input):

    # 1. Load and validate the request.
    request = load_validation_request(request_input)

    validation_id = request["validation_id"]
    dataset_name = request["dataset_name"]

    print(f"\nValidation ID: {validation_id}")
    print(f"Dataset: {dataset_name}")

    # 2. Load validation rules.
    rules_path = PROJECT_ROOT / request["validation_rules"]

    with open(rules_path, "r", encoding="utf-8") as file:
        validation_config = json.load(file)

    # 3. Read source data from S3.
    source_config = request["source"]

    print("\nReading source data from AWS S3...")

    source_records = read_source_data(
        bucket_name=source_config["bucket"],
        object_key=source_config["object_key"]
    )

    print(f"Retrieved {len(source_records)} source records.")

    # 4. Read target data from Databricks.
    target_config = request["target"]

    print("\nReading target data from Databricks...")

    target_records = read_target_data(
        catalog=target_config["catalog"],
        schema=target_config["schema"],
        table=target_config["table"]
    )

    print(f"Retrieved {len(target_records)} target records.")

    # 5. Normalize both datasets using the validation rules.
    print("\nNormalizing datasets...")

    source_records = normalize_records(
        source_records,
        validation_config
    )

    target_records = normalize_records(
        target_records,
        validation_config
    )

    # 6. Execute deterministic validation.
    print("\nExecuting validation checks...")

    results = run_validation(
        source_records,
        target_records,
        validation_config
    )

    # 7. Generate summary.
    summary = build_report_summary(results)

    # 8. Generate reports.
    report_dir = PROJECT_ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    json_report_path = (
        report_dir / f"{validation_id}_results.json"
    )

    html_report_path = (
        report_dir / f"{validation_id}_report.html"
    )

    report_data = {
        "validation_id": validation_id,
        "dataset_name": dataset_name,
        "summary": summary,
        "validation_results": results
    }

    with open(json_report_path, "w", encoding="utf-8") as file:
        json.dump(report_data, file, indent=4, default=str)

    generate_html_report(
        summary,
        results,
        html_report_path,
        dataset_name
    )

    # 9. Display final summary.
    print("\n========== VALIDATION SUMMARY ==========")

    print(f"Overall Status : {summary['overall_status']}")
    print(f"Total Checks   : {summary['total_checks']}")
    print(f"Passed Checks  : {summary['passed_checks']}")
    print(f"Failed Checks  : {summary['failed_checks']}")
    print(f"Total Findings : {summary['total_findings']}")

    print("\nGenerated Reports:")
    print(f"JSON: {json_report_path}")
    print(f"HTML: {html_report_path}")

    return report_data
