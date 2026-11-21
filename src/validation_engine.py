
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from collections import defaultdict

def validate_record_count(source, target):
    return {
        "check": "record_count",
        "source_count": len(source),
        "target_count": len(target),
        "passed": len(source) == len(target)
    }


def validate_primary_keys(source, target, primary_key):
    source_ids = [r.get(primary_key) for r in source]
    target_ids = [r.get(primary_key) for r in target]

    source_counts = Counter(source_ids)
    target_counts = Counter(target_ids)

    source_set = set(source_ids)
    target_set = set(target_ids)

    return {
        "check": "primary_key",
        "primary_key": primary_key,
        "missing_records": sorted(
            source_set - target_set,
            key=str
        ),
        "extra_records": sorted(
            target_set - source_set,
            key=str
        ),
        "source_duplicates": sorted(
            [key for key, count in source_counts.items() if count > 1],
            key=str
        ),
        "target_duplicates": sorted(
            [key for key, count in target_counts.items() if count > 1],
            key=str
        )
    }


def validate_null_values(records, columns, primary_key):
    issues = []

    for record in records:
        for column in columns:
            value = record.get(column)

            if value is None or (
                isinstance(value, str) and not value.strip()
            ):
                issues.append({
                    "record_key": record.get(primary_key),
                    "primary_key": primary_key,
                    "column": column,
                    "issue": "NULL_OR_EMPTY"
                })

    return {
        "check": "null_values",
        "issues": issues
    }


def validate_data_types(records, columns, primary_key):
    issues = []

    expected_python_types = {
        "integer": int,
        "int": int,
        "long": int,
        "decimal": Decimal,
        "float": float,
        "string": str,
        "date": date,
        "datetime": datetime,
        "boolean": bool,
        "bool": bool
    }

    for record in records:
        record_key = record.get(primary_key)

        invalid_values = record.get("_validation_errors", {})

        for column, definition in columns.items():
            expected_type = definition["expected_type"].lower()
            value = record.get(column)

            # Conversion failures are recorded by the preprocessor.
            if column in invalid_values:
                issues.append({
                    "record_key": record_key,
                    "primary_key": primary_key,
                    "column": column,
                    "invalid_value": invalid_values[column]
                })
                continue

            # Empty values are handled by null validation.
            if value is None:
                continue

            python_type = expected_python_types.get(expected_type)

            if python_type is None:
                raise ValueError(
                    f"Unsupported expected type '{expected_type}' "
                    f"for column '{column}'."
                )

            # bool is a subclass of int in Python, so check it
            # separately to avoid accepting booleans as integers.
            if expected_type in ("integer", "int", "long"):
                valid = isinstance(value, int) and not isinstance(value, bool)

            elif expected_type == "date":
                valid = isinstance(value, date) and not isinstance(
                    value, datetime
                )

            else:
                valid = isinstance(value, python_type)

            if not valid:
                issues.append({
                    "record_key": record_key,
                    "primary_key": primary_key,
                    "column": column,
                    "invalid_value": str(value)
                })

    return {
        "check": "data_type_validation",
        "issues": issues
    }




def validate_column_values(source, target, primary_key, columns):
    """
    Compare source and target records without losing duplicate
    primary-key occurrences.

    Records with the same primary key are compared occurrence
    by occurrence. Duplicate-count discrepancies are handled
    separately by validate_primary_keys().
    """

    source_groups = defaultdict(list)
    target_groups = defaultdict(list)

    # Group source records by primary key.
    for record in source:
        source_groups[record.get(primary_key)].append(record)

    # Group target records by primary key.
    for record in target:
        target_groups[record.get(primary_key)].append(record)

    common_keys = (
        source_groups.keys() & target_groups.keys()
    )

    issues = []

    for record_key in sorted(common_keys, key=str):

        source_records = source_groups[record_key]
        target_records = target_groups[record_key]

        # Compare corresponding occurrences.
        # Extra occurrences are already detected by primary-key validation.
        matching_count = min(
            len(source_records),
            len(target_records)
        )

        for index in range(matching_count):

            source_record = source_records[index]
            target_record = target_records[index]

            for column in columns:

                source_value = source_record.get(column)
                target_value = target_record.get(column)

                if source_value != target_value:
                    issues.append({
                        "record_key": record_key,
                        "primary_key": primary_key,
                        "column": column,
                        "source_value": str(source_value),
                        "target_value": str(target_value),
                        "occurrence": index + 1
                    })

    return {
        "check": "column_value_comparison",
        "issues": issues
    }



def run_validation(source, target, config):

    primary_key = config["primary_key"]
    columns = config["columns"]

    results = []
    checks = config["validation_checks"]

    if checks.get("record_count"):
        results.append(
            validate_record_count(source, target)
        )

    if (
        checks.get("missing_records")
        or checks.get("extra_records")
        or checks.get("duplicate_records")
    ):
        key_result = validate_primary_keys(
            source,
            target,
            primary_key
        )

        if not checks.get("missing_records"):
            key_result["missing_records"] = []

        if not checks.get("extra_records"):
            key_result["extra_records"] = []

        if not checks.get("duplicate_records"):
            key_result["target_duplicates"] = []
            key_result["source_duplicates"] = []

        results.append(key_result)

    if checks.get("null_values"):
        mandatory_columns = [
            name
            for name, definition in columns.items()
            if not definition["nullable"]
        ]

        results.append(
            validate_null_values(
                target,
                mandatory_columns,
                primary_key
            )
        )

    if checks.get("data_type_validation"):
        results.append(
            validate_data_types(
                target,
                columns,
                primary_key
            )
        )

    if checks.get("column_value_comparison"):
        results.append(
            validate_column_values(
                source,
                target,
                primary_key,
                columns.keys()
            )
        )

    return results
