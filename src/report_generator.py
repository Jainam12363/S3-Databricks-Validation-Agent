
from collections import Counter
from html import escape


def classify_severity(check, issue):
    """Assign severity to an individual validation finding."""

    if check == "primary_key":
        return "CRITICAL"

    if check == "data_type_validation":
        return "HIGH"

    if check == "null_values":
        return "HIGH"

    if check == "column_value_comparison":
        return "MEDIUM"

    if check == "record_count":
        return "HIGH"

    return "LOW"


def build_report_summary(results):
    total_checks = len(results)
    passed_checks = 0
    failed_checks = 0

    findings = []
    category_counts = Counter()
    severity_counts = Counter()

    for result in results:
        check = result["check"]
        issues = []

        if check == "record_count":
            passed = result["passed"]

            if not passed:
                issues.append({
                    "category": "record_count",
                    "description": (
                        f"Source has {result['source_count']} records; "
                        f"target has {result['target_count']} records."
                    )
                })

        elif check == "primary_key":
            primary_key = result.get("primary_key", "primary_key")

            for category in [
                "missing_records",
                "extra_records",
                "source_duplicates",
                "target_duplicates"
            ]:
                for record_key in result.get(category, []):
                    issue = {
                        "category": category,
                        "record_key": record_key,
                        "primary_key": primary_key,
                        "description": (
                            f"{category.replace('_', ' ').title()}: "
                            f"{primary_key} = {record_key}"
                        )
                    }

                    # Backward compatibility for existing
                    # customer-specific agent functionality.
                    if primary_key == "customer_id":
                        issue["customer_id"] = record_key

                    issues.append(issue)

            passed = len(issues) == 0

        else:
            raw_issues = result.get("issues", [])
            passed = len(raw_issues) == 0

            for raw_issue in raw_issues:
                issue = {
                    "category": check,
                    **raw_issue
                }

                record_key = raw_issue.get("record_key")
                primary_key = raw_issue.get("primary_key")
                column = raw_issue.get("column")

                # Preserve the old customer_id field where applicable.
                if primary_key == "customer_id":
                    issue["customer_id"] = record_key

                if record_key is not None and primary_key:
                    record_description = (
                        f"{primary_key} = {record_key}"
                    )
                else:
                    record_description = "Record"

                issue["description"] = (
                    f"{check.replace('_', ' ').title()}: "
                    f"{record_description} - {column}"
                )

                issues.append(issue)

        if passed:
            passed_checks += 1
        else:
            failed_checks += 1

        for issue in issues:
            category = issue["category"]
            severity = classify_severity(check, issue)

            issue["severity"] = severity
            findings.append(issue)

            category_counts[category] += 1
            severity_counts[severity] += 1

    return {
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "total_findings": len(findings),
        "category_counts": dict(category_counts),
        "severity_counts": dict(severity_counts),
        "findings": findings,
        "overall_status": (
            "PASSED" if failed_checks == 0 else "FAILED"
        )
    }


def generate_html_report(
    summary,
    results,
    output_path,
    dataset_name="Dataset"
):
    """Generate a readable HTML reconciliation report."""

    severity_rows = ""

    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        count = summary["severity_counts"].get(severity, 0)

        severity_rows += (
            f"<tr><td>{escape(severity)}</td>"
            f"<td>{count}</td></tr>"
        )

    finding_rows = ""

    for finding in summary["findings"]:
        record_key = finding.get(
            "record_key",
            finding.get("customer_id", "-")
        )

        finding_rows += f"""
        <tr>
            <td>{escape(str(finding.get('severity', '')))}</td>
            <td>{escape(str(finding.get('category', '')))}</td>
            <td>{escape(str(record_key))}</td>
            <td>{escape(str(finding.get('column', '-')))}</td>
            <td>{escape(str(finding.get('source_value', '-')))}</td>
            <td>{escape(str(finding.get('target_value', '-')))}</td>
            <td>{escape(str(finding.get('description', '')))}</td>
        </tr>
        """

    category_rows = ""

    for category, count in summary["category_counts"].items():
        category_rows += (
            f"<tr><td>{escape(category)}</td>"
            f"<td>{count}</td></tr>"
        )

    record_count = next(
        (r for r in results if r["check"] == "record_count"),
        {}
    )

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Data Reconciliation Report</title>

        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 35px;
                background: #f4f6f9;
                color: #222;
            }}

            h1, h2 {{
                color: #24344d;
            }}

            .cards {{
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                margin: 20px 0;
            }}

            .card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                min-width: 140px;
                box-shadow: 0 2px 5px #ddd;
            }}

            .number {{
                font-size: 28px;
                font-weight: bold;
            }}

            .failed {{
                color: #c62828;
            }}

            .passed {{
                color: #218838;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
                margin-bottom: 30px;
            }}

            th, td {{
                padding: 11px;
                border: 1px solid #ddd;
                text-align: left;
                overflow-wrap: anywhere;
            }}

            th {{
                background: #24344d;
                color: white;
            }}

            tr:nth-child(even) {{
                background: #f1f3f5;
            }}

            .status {{
                font-weight: bold;
                color: #c62828;
            }}
        </style>
    </head>

    <body>
        <h1>Data Reconciliation Report</h1>

        <p>Dataset: {escape(str(dataset_name))}</p>

        <p>
            Overall Status:
            <span class="status">
                {escape(summary['overall_status'])}
            </span>
        </p>

        <h2>Execution Summary</h2>

        <p>
            Source records:
            {record_count.get('source_count', 'N/A')}
        </p>

        <p>
            Target records:
            {record_count.get('target_count', 'N/A')}
        </p>

        <div class="cards">
            <div class="card">
                Total Checks
                <div class="number">
                    {summary['total_checks']}
                </div>
            </div>

            <div class="card">
                Passed
                <div class="number passed">
                    {summary['passed_checks']}
                </div>
            </div>

            <div class="card">
                Failed
                <div class="number failed">
                    {summary['failed_checks']}
                </div>
            </div>

            <div class="card">
                Findings
                <div class="number">
                    {summary['total_findings']}
                </div>
            </div>
        </div>

        <h2>Findings by Category</h2>

        <table>
            <tr>
                <th>Category</th>
                <th>Count</th>
            </tr>
            {category_rows}
        </table>

        <h2>Findings by Severity</h2>

        <table>
            <tr>
                <th>Severity</th>
                <th>Count</th>
            </tr>
            {severity_rows}
        </table>

        <h2>Detailed Findings</h2>

        <table>
            <tr>
                <th>Severity</th>
                <th>Category</th>
                <th>Record Key</th>
                <th>Column</th>
                <th>Source Value</th>
                <th>Target Value</th>
                <th>Description</th>
            </tr>

            {finding_rows}
        </table>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(html)
