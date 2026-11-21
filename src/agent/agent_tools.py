
import json
from pathlib import Path

from src.validation_service import execute_validation


# --------------------------------------------------
# Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUEST_PATH = PROJECT_ROOT / "config" / "validation_request.json"
REPORTS_DIR = PROJECT_ROOT / "reports"


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def load_latest_report():
    """
    Load the most recently generated validation JSON report.
    """

    if not REPORTS_DIR.exists():
        raise FileNotFoundError("Reports directory does not exist.")

    report_files = list(REPORTS_DIR.glob("*_results.json"))

    if not report_files:
        raise FileNotFoundError(
            "No validation reports found. Run validation first."
        )

    latest_report = max(
        report_files,
        key=lambda file: file.stat().st_mtime
    )

    with open(latest_report, "r", encoding="utf-8") as file:
        return json.load(file)



def extract_findings(report):
    """
    Extract individual findings from the validation report.
    """

    # Findings are currently stored inside summary.
    findings = report.get("summary", {}).get("findings", [])

    # Fallback in case findings are stored under validation_results.
    if not findings:
        findings = report.get("validation_results", [])

    return findings



# --------------------------------------------------
# Tool 1: Run validation
# --------------------------------------------------


def run_validation(validation_request=None):
    """
    Execute validation using either:
    1. The existing configured request file.
    2. A dynamically supplied validation request.
    """

    if validation_request is None:
        request_input = REQUEST_PATH
    else:
        request_input = validation_request

    report = execute_validation(request_input)

    return {
        "status": "success",
        "validation_id": report["validation_id"],
        "dataset_name": report["dataset_name"],
        "summary": report["summary"],
        "message": "Validation completed successfully."
    }



# --------------------------------------------------
# Tool 2: Get validation summary
# --------------------------------------------------

def get_validation_summary():
    """
    Retrieve the summary from the latest validation report.
    """

    report = load_latest_report()

    return {
        "validation_id": report["validation_id"],
        "dataset_name": report["dataset_name"],
        "summary": report["summary"]
    }


# --------------------------------------------------
# Tool 3: Get findings for a customer
# --------------------------------------------------

def get_customer_findings(customer_id: int):
    """
    Retrieve validation findings associated with a customer ID.
    """

    report = load_latest_report()
    findings = extract_findings(report)

    customer_findings = []

    for finding in findings:

        finding_customer_id = finding.get("customer_id")

        if finding_customer_id is None:
            finding_customer_id = finding.get("record_id")

        if finding_customer_id is None:
            finding_customer_id = finding.get("primary_key")

        if finding_customer_id is not None:
            if str(finding_customer_id) == str(customer_id):
                customer_findings.append(finding)

    return {
        "customer_id": customer_id,
        "total_findings": len(customer_findings),
        "findings": customer_findings
    }


# --------------------------------------------------
# Tool 4: Get findings by severity
# --------------------------------------------------

def get_findings_by_severity(severity: str):
    """
    Retrieve validation findings filtered by severity.

    Supported values: LOW, MEDIUM, HIGH, CRITICAL.
    """

    severity = severity.upper()

    allowed_severities = [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    ]

    if severity not in allowed_severities:
        raise ValueError(
            f"Invalid severity. Choose from: {allowed_severities}"
        )

    report = load_latest_report()
    findings = extract_findings(report)

    filtered_findings = [
        finding
        for finding in findings
        if str(finding.get("severity", "")).upper() == severity
    ]

    return {
        "severity": severity,
        "total_findings": len(filtered_findings),
        "findings": filtered_findings
    }
