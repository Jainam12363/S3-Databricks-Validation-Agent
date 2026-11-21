
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


def convert_value(value, expected_type, column_config):
    """
    Convert a value according to its expected type.

    Returns:
        (normalized_value, invalid_value)

    invalid_value is None when conversion succeeds or the original
    value is empty.
    """

    if value is None or (
        isinstance(value, str) and not value.strip()
    ):
        return None, None

    expected_type = expected_type.lower()

    try:
        if expected_type in ("integer", "int", "long"):
            if isinstance(value, bool):
                raise ValueError("Boolean is not an integer value.")
            return int(value), None

        if expected_type == "decimal":
            return Decimal(str(value).strip()), None

        if expected_type == "float":
            return float(value), None

        if expected_type == "string":
            return str(value).strip(), None

        if expected_type == "date":
            if isinstance(value, datetime):
                return value.date(), None

            if isinstance(value, date):
                return value, None

            date_format = column_config.get("format", "%Y-%m-%d")
            return datetime.strptime(
                str(value).strip(),
                date_format
            ).date(), None

        if expected_type == "datetime":
            if isinstance(value, datetime):
                return value, None

            date_format = column_config.get(
                "format",
                "%Y-%m-%d %H:%M:%S"
            )
            return datetime.strptime(
                str(value).strip(),
                date_format
            ), None

        if expected_type in ("boolean", "bool"):
            if isinstance(value, bool):
                return value, None

            normalized_value = str(value).strip().lower()

            if normalized_value in ("true", "1", "yes", "y"):
                return True, None

            if normalized_value in ("false", "0", "no", "n"):
                return False, None

            raise ValueError("Invalid boolean value.")

        raise ValueError(
            f"Unsupported expected type: {expected_type}"
        )

    except (ValueError, TypeError, InvalidOperation, OverflowError):
        return None, str(value)


def normalize_records(records, validation_config):
    """
    Normalize records using the expected types defined
    in the validation rules configuration.
    """

    columns = validation_config["columns"]
    normalized_records = []

    for record in records:
        normalized = {}
        validation_errors = {}

        # Process every field present in the original record.
        for column, value in record.items():

            if column not in columns:
                # Preserve unconfigured fields without conversion.
                normalized[column] = value
                continue

            column_config = columns[column]
            expected_type = column_config["expected_type"]

            normalized_value, invalid_value = convert_value(
                value,
                expected_type,
                column_config
            )

            normalized[column] = normalized_value

            if invalid_value is not None:
                validation_errors[column] = invalid_value

        # Store invalid original values separately so that
        # the validation engine can report them.
        normalized["_validation_errors"] = validation_errors

        normalized_records.append(normalized)

    return normalized_records
