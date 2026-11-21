
import re
from pathlib import Path


# --------------------------------------------------
# Validation patterns
# --------------------------------------------------

IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
VALIDATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


# --------------------------------------------------
# Helper: Validate required fields
# --------------------------------------------------

def require_fields(data, required_fields, section_name):

    if not isinstance(data, dict):
        raise ValueError(
            f"'{section_name}' must be a JSON object."
        )

    missing_fields = [
        field for field in required_fields
        if field not in data
    ]

    if missing_fields:
        raise ValueError(
            f"Missing fields in '{section_name}': "
            f"{', '.join(missing_fields)}"
        )


# --------------------------------------------------
# Helper: Validate non-empty strings
# --------------------------------------------------

def require_non_empty_string(value, field_name):

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"'{field_name}' must be a non-empty string."
        )

    return value.strip()


# --------------------------------------------------
# Main request validation
# --------------------------------------------------

def validate_validation_request(request, project_root):

    """
    Validate an incoming S3-to-Databricks validation request.

    Checks:
    - Required request fields
    - Validation ID and dataset name
    - Supported source and target types
    - Source and target configuration
    - Databricks identifiers
    - Validation rules file location and existence

    Returns a normalized copy of the request.
    """

    # 1. Check top-level request structure.

    require_fields(
        request,
        [
            "validation_id",
            "dataset_name",
            "source",
            "target",
            "validation_rules"
        ],
        "request"
    )

    validated_request = request.copy()

    # 2. Validate validation ID.

    validation_id = require_non_empty_string(
        request["validation_id"],
        "validation_id"
    )

    if not VALIDATION_ID_PATTERN.fullmatch(validation_id):
        raise ValueError(
            "'validation_id' can contain only letters, "
            "numbers, underscores, and hyphens."
        )

    validated_request["validation_id"] = validation_id

    # 3. Validate dataset name.

    dataset_name = require_non_empty_string(
        request["dataset_name"],
        "dataset_name"
    )

    if not VALIDATION_ID_PATTERN.fullmatch(dataset_name):
        raise ValueError(
            "'dataset_name' contains invalid characters."
        )

    validated_request["dataset_name"] = dataset_name

    # 4. Validate source configuration.

    source = request["source"]

    require_fields(
        source,
        ["type", "bucket", "object_key"],
        "source"
    )

    source_type = require_non_empty_string(
        source["type"],
        "source.type"
    ).lower()

    if source_type != "s3":
        raise ValueError(
            "Unsupported source type. Currently supported: S3."
        )

    validated_source = source.copy()
    validated_source["type"] = source_type

    validated_source["bucket"] = require_non_empty_string(
        source["bucket"],
        "source.bucket"
    )

    validated_source["object_key"] = require_non_empty_string(
        source["object_key"],
        "source.object_key"
    )

    validated_request["source"] = validated_source

    # 5. Validate target configuration.

    target = request["target"]

    require_fields(
        target,
        ["type", "catalog", "schema", "table"],
        "target"
    )

    target_type = require_non_empty_string(
        target["type"],
        "target.type"
    ).lower()

    if target_type != "databricks":
        raise ValueError(
            "Unsupported target type. Currently supported: Databricks."
        )

    validated_target = target.copy()
    validated_target["type"] = target_type

    for field in ["catalog", "schema", "table"]:

        identifier = require_non_empty_string(
            target[field],
            f"target.{field}"
        )

        if not IDENTIFIER_PATTERN.fullmatch(identifier):
            raise ValueError(
                f"Invalid Databricks identifier: {field}."
            )

        validated_target[field] = identifier

    validated_request["target"] = validated_target

    # 6. Validate the validation-rules file path.

    rules_path = require_non_empty_string(
        request["validation_rules"],
        "validation_rules"
    )

    rules_path = Path(rules_path)

    if rules_path.is_absolute():
        raise ValueError(
            "'validation_rules' must be a relative project path."
        )

    project_root = Path(project_root).resolve()
    resolved_rules_path = (project_root / rules_path).resolve()

    # Prevent paths from escaping the project directory.
    if not resolved_rules_path.is_relative_to(project_root):
        raise ValueError(
            "'validation_rules' must point inside the project directory."
        )

    if resolved_rules_path.suffix.lower() != ".json":
        raise ValueError(
            "'validation_rules' must reference a JSON file."
        )

    if not resolved_rules_path.is_file():
        raise FileNotFoundError(
            f"Validation rules file not found: {rules_path}"
        )

    validated_request["validation_rules"] = str(rules_path)

    return validated_request
