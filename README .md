# S3-to-Databricks Validation & Reconciliation Agent

An AI-assisted data validation application that compares source data in **AWS S3** with target data in **Databricks**. A deterministic Python validation engine identifies discrepancies and generates JSON and HTML reports. A Groq-powered agent lets users run validations and ask questions about the results through an interactive terminal.

## 1. Project objectives

- Read source records from an AWS S3 CSV object.
- Read target records from a Databricks table.
- Normalize values using configurable column types.
- Compare source and target records using deterministic Python checks.
- Generate JSON and HTML reconciliation reports.
- Accept a configured request or a complete dynamic validation request.
- Provide a conversational terminal interface powered by Groq function calling.

**The Python validation engine is the source of truth.** The LLM invokes Python tools and explains returned results; it does not calculate or decide validation outcomes.

## 2. Scope

The implemented live comparison is **AWS S3 source → Databricks target**. The configured example validates `customers`. The generalized validation logic was also exercised with a separate mock `orders` dataset.

This project does not currently implement S3-to-S3 or Databricks-to-Databricks comparison, a web UI, REST API, production deployment, migration orchestration, or automated remediation.

## 3. Architecture

```text
User
 |
 v
Interactive terminal (src/main.py)
 |
 v
Groq AI agent (src/agent/validation_agent.py)
 |
 +-- run_validation
 +-- get_validation_summary
 +-- get_customer_findings
 +-- get_findings_by_severity
 |
 v
Validation service (src/validation_service.py)
 |
 +-----------------------+
 |                       |
 v                       v
AWS S3                Databricks
s3_reader.py          databricks_reader.py
 |                       |
 +-----------+-----------+
             |
             v
     Data preprocessing
     data_preprocessor.py
             |
             v
     Deterministic checks
     validation_engine.py
             |
             v
     JSON and HTML reports
     report_generator.py
             |
             v
        reports/
```

## 4. Technology stack

- Python
- AWS S3 and Boto3
- Databricks SQL Connector
- Groq API and official Python SDK
- `openai/gpt-oss-20b` model
- `python-dotenv`
- JSON configuration
- JSON and HTML reports

## 5. Project structure

```text
S3_Databricks_Validation_Agent/
|
|-- config/
|   |-- validation_request.json
|   |-- validation_rules.json
|
|-- data/
|   |-- expected/
|   |-- source/
|   |-- target/
|
|-- reports/
|
|-- src/
|   |-- __init__.py
|   |-- main.py
|   |-- s3_reader.py
|   |-- databricks_reader.py
|   |-- data_preprocessor.py
|   |-- validation_engine.py
|   |-- report_generator.py
|   |-- validation_service.py
|   |-- request_validator.py
|   |
|   |-- agent/
|       |-- __init__.py
|       |-- agent_tools.py
|       |-- tool_definitions.py
|       |-- agent_instructions.py
|       |-- validation_agent.py
|
|-- .env
|-- .gitignore
|-- requirements.txt
|-- README.md
```

`data/` contains local reference/demo data. The configured live validation reads from S3 and Databricks. Generated reports are saved in `reports/`.

## 6. Prerequisites

Before running the application, ensure that you have:

1. Python installed.
2. AWS access to the S3 bucket and source object.
3. AWS credentials with permission to read the configured S3 object.
4. A Databricks workspace, SQL warehouse, and target table.
5. Databricks credentials with permission to query the target table.
6. A Groq API key.
7. Network access to the required services.

## 7. Installation

Open PowerShell in the project root.

Create and activate a virtual environment if one does not already exist:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Current `requirements.txt`:

```text
boto3
databricks-sql-connector
python-dotenv
groq
```

## 8. Environment configuration

Create or update `.env` in the project root. It must contain the credentials and connection settings read by the existing S3 reader, Databricks reader, and Groq agent.

Typical settings may look like:

```dotenv
# AWS
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=your_aws_region

# Databricks
DATABRICKS_SERVER_HOSTNAME=your_workspace_hostname
DATABRICKS_HTTP_PATH=your_warehouse_http_path
DATABRICKS_ACCESS_TOKEN=your_databricks_token

# Groq
GROQ_API_KEY=your_groq_api_key
```

**Important:** The exact environment-variable names are determined by the code in `src/s3_reader.py` and `src/databricks_reader.py`. Keep `.env` aligned with those files. The names above are common examples; do not replace working project-specific names without checking the code.

Never share or commit `.env`. The project `.gitignore` excludes it.

## 9. Validation configuration

### Validation request

The default request is stored in `config/validation_request.json`. It identifies the validation ID, dataset name, S3 source bucket and object key, Databricks catalog/schema/table, and validation-rules file.

Example structure:

```json
{
  "validation_id": "CUSTOMERS_VALIDATION_001",
  "dataset_name": "customers",
  "source": {
    "type": "s3",
    "bucket": "your-s3-bucket",
    "object_key": "source/customers_source.csv"
  },
  "target": {
    "type": "databricks",
    "catalog": "workspace",
    "schema": "default",
    "table": "customers_target"
  },
  "validation_rules": "config/validation_rules.json"
}
```

Use the actual bucket, object key, catalog, schema, and table configured in your environment. The example is illustrative; verify it against your current request file.

### Validation rules

The default rules are in `config/validation_rules.json`. They specify the dataset name, primary key, each column's expected type and nullability, and which checks are enabled.

The current customer rules use `customer_id` as the primary key. The configured columns include integer, string, decimal, and date types, and are marked non-nullable.

## 10. Validation checks

The checks are controlled by `validation_rules.json`.

| Check | Purpose |
|---|---|
| Record count | Compares total source and target record counts. |
| Missing records | Finds source records absent from the target. |
| Extra records | Finds target records absent from the source. |
| Duplicate records | Identifies duplicate primary-key records. |
| Null values | Detects null or empty values in non-nullable columns. |
| Data type validation | Checks values against configured expected data types. |
| Column value comparison | Compares configured column values for corresponding records. |

The preprocessor supports integer, decimal, float, string, date, datetime, and boolean conversions. A single invalid value may produce findings in multiple categories, such as a null/type issue and a column comparison mismatch.

## 11. Run the application

From the project root, activate the virtual environment and run:

```powershell
python -m src.main
```

The application starts an interactive terminal session:

```text
=======================================================
       DATA VALIDATION & RECONCILIATION AGENT
=======================================================

LLM Provider : Groq
Model        : openai/gpt-oss-20b
Source       : AWS S3
Target       : Databricks

Agent initialized successfully.
Enter your questions below.
Type 'exit' or 'quit' to stop the agent.

You:
```

Enter requests and follow-up questions in the same session. Type `exit` or `quit` to stop.

## 12. Available agent tools

| Tool | Purpose |
|---|---|
| `run_validation` | Runs the configured validation or a complete dynamic validation request. |
| `get_validation_summary` | Retrieves the latest validation summary. |
| `get_customer_findings` | Retrieves findings associated with a customer ID. |
| `get_findings_by_severity` | Filters findings by LOW, MEDIUM, HIGH, or CRITICAL severity. |

The agent must not invent connection details or validation rules. A different dataset requires a complete validation request. If that configuration is missing, the agent asks for it rather than silently validating the configured dataset.

## 13. Example manager demonstration

Run the application:

```powershell
python -m src.main
```

Then try:

```text
You: Run a fresh validation of the customers dataset.
You: What is the overall validation status?
You: Show me all critical findings.
You: What issues were found for customer 103?
You: Explain why the validation failed.
```

The first request triggers validation. The follow-up questions retrieve and explain information from the generated report through the agent's Python tools.

## 14. Generated reports

Each validation run generates:

- A JSON results file for structured findings.
- An HTML report for human-readable inspection.

Both are saved in `reports/`, with filenames based on the validation ID. Open the HTML report in a browser to inspect the reconciliation results.

Example:

```text
reports/
|-- CUSTOMERS_VALIDATION_001_results.json
|-- CUSTOMERS_VALIDATION_001_report.html
```

## 15. Demo data and verified behaviour

The customer demo data contains intentional discrepancies. A previously verified run retrieved 10 source records and 11 target records and reported 10 findings.

The generalized validation logic was also exercised using mock `orders` records to verify handling of a different schema and data types. This was a local mock-data test; it does not mean a live orders dataset was configured in S3 and Databricks.

## 16. Limitations

- The supported live comparison is AWS S3 source to Databricks target.
- The deterministic Python engine determines discrepancies and validation status.
- The Groq agent requires a valid API key and network connectivity.
- AWS and Databricks credentials must be configured and authorized.
- This is a standalone learning/demo application, not a production deployment.
- No UI, REST API, migration orchestration, or automated remediation is included.
- Severity levels are the project's demo classifications.
- Duplicate primary-key records are compared by occurrence order for column comparisons. If duplicate records have different contents and ordering, a one-to-one match may be ambiguous.

## 17. Security

- Keep `.env` local and never commit credentials.
- Use appropriately scoped AWS and Databricks credentials.
- Do not include API keys, access tokens, or passwords in reports or screenshots.
- `.gitignore` excludes `.env`, `.venv/`, `__pycache__/`, and compiled Python files.

---

**Project:** S3-to-Databricks Validation & Reconciliation Agent  
**LLM provider:** Groq  
**Model:** `openai/gpt-oss-20b`
