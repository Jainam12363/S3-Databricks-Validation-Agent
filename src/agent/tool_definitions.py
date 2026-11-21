
TOOLS = [

    # Tool 1: Run validation
    
    {
        "type": "function",
        "function": {
            "name": "run_validation",
            "description": (
                "Execute data validation between an AWS S3 source "
                "dataset and a Databricks target dataset. "
                "Use the existing configured validation request when "
                "the user requests the configured dataset. "
                "For a different dataset, require a complete validation_request. "
                "Never invent bucket names, object keys, table names, "
                "or validation rules."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "validation_request": {
                        "type": ["object", "null"],
                        "description": (
                            "Optional complete dynamic validation configuration. "
                            "Use null when the user requests the configured dataset. "
                            "For a different dataset, provide its complete configuration."
                        ),
                        "properties": {
                            "validation_id": {
                                "type": "string"
                            },
                            "dataset_name": {
                                "type": "string"
                            },
                            "source": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["s3"]
                                    },
                                    "bucket": {
                                        "type": "string"
                                    },
                                    "object_key": {
                                        "type": "string"
                                    }
                                },
                                "required": ["type", "bucket", "object_key"]
                            },
                            "target": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["databricks"]
                                    },
                                    "catalog": {
                                        "type": "string"
                                    },
                                    "schema": {
                                        "type": "string"
                                    },
                                    "table": {
                                        "type": "string"
                                    }
                                },
                                "required": ["type", "catalog", "schema", "table"]
                            },
                            "validation_rules": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "validation_id",
                            "dataset_name",
                            "source",
                            "target",
                            "validation_rules"
                        ]
                    }
                },
                "required": []
            }
        }
    },


    # Tool 2: Get validation summary
    {
        "type": "function",
        "function": {
            "name": "get_validation_summary",
            "description": (
                "Retrieve the summary of the latest completed "
                "validation, including overall status, total checks, "
                "passed checks, failed checks, total findings, "
                "and severity counts."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },

    # Tool 3: Get customer-specific findings
    {
        "type": "function",
        "function": {
            "name": "get_customer_findings",
            "description": (
                "Retrieve all validation findings associated with "
                "a specific customer ID. Use this when the user asks "
                "about data issues for an individual customer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "The customer ID to investigate."
                    }
                },
                "required": ["customer_id"]
            }
        }
    },

    # Tool 4: Get findings by severity
    {
        "type": "function",
        "function": {
            "name": "get_findings_by_severity",
            "description": (
                "Retrieve all validation findings belonging to a "
                "specific severity level. Supported severity levels "
                "are LOW, MEDIUM, HIGH, and CRITICAL."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "severity": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                        "description": "The severity level to filter by."
                    }
                },
                "required": ["severity"]
            }
        }
    }

]
