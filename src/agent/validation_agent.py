
import os
import re
import json

from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from src.agent.agent_tools import (
    run_validation,
    get_validation_summary,
    get_customer_findings,
    get_findings_by_severity
)

from src.agent.tool_definitions import TOOLS
from src.agent.agent_instructions import SYSTEM_PROMPT


# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

GROQ_MODEL = "openai/gpt-oss-20b"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUEST_PATH = PROJECT_ROOT / "config" / "validation_request.json"

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing from the .env file.")

client = Groq(api_key=api_key)


# --------------------------------------------------
# Available Python functions
# --------------------------------------------------

AVAILABLE_FUNCTIONS = {
    "run_validation": run_validation,
    "get_validation_summary": get_validation_summary,
    "get_customer_findings": get_customer_findings,
    "get_findings_by_severity": get_findings_by_severity
}


# --------------------------------------------------
# Dataset configuration safeguard
# --------------------------------------------------

def get_configured_dataset():
    """Return the dataset name from the configured request."""

    with open(REQUEST_PATH, "r", encoding="utf-8") as file:
        request = json.load(file)

    return request["dataset_name"]


def get_requested_dataset(user_message):
    """
    Extract a dataset name from phrases such as:
    'Run validation for the orders dataset'.
    """

    patterns = [
        r"\b([a-zA-Z0-9_-]+)\s+dataset\b",
        r"\bdataset\s+(?:named\s+)?([a-zA-Z0-9_-]+)\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, user_message, re.IGNORECASE)

        if match:
            return match.group(1).lower()

    return None


def check_dataset_configuration(user_message):
    """
    Prevent the configured dataset from being validated
    when the user explicitly requests a different dataset
    without supplying its configuration.
    """

    requested_dataset = get_requested_dataset(user_message)

    if requested_dataset is None:
        return None

    configured_dataset = get_configured_dataset().lower()

    if requested_dataset == configured_dataset:
        return None

    return (
        f"You requested validation for the '{requested_dataset}' dataset, "
        f"but the currently configured request is for the "
        f"'{configured_dataset}' dataset.\n\n"
        "Please provide the complete validation configuration for "
        "the requested dataset, including:\n"
        "- Validation ID\n"
        "- Dataset name\n"
        "- S3 bucket and object key\n"
        "- Databricks catalog, schema, and table\n"
        "- Validation rules file path\n\n"
        "No validation was executed."
    )


# --------------------------------------------------
# Execute a requested Python function
# --------------------------------------------------

def execute_tool(tool_call):

    function_name = tool_call.function.name

    if function_name not in AVAILABLE_FUNCTIONS:
        raise ValueError(f"Unknown tool requested: {function_name}")

    function_to_call = AVAILABLE_FUNCTIONS[function_name]

    function_arguments = json.loads(
        tool_call.function.arguments or "{}"
    )

    if not isinstance(function_arguments, dict):
        raise ValueError("Tool arguments must be a JSON object.")

    result = function_to_call(**function_arguments)

    return json.dumps(result, default=str)


# --------------------------------------------------
# Main agent conversation function
# --------------------------------------------------

def run_agent(user_message, conversation_history=None):

    if conversation_history is None:
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]
    else:
        messages = conversation_history.copy()

    messages.append({
        "role": "user",
        "content": user_message
    })

    # Check whether the user requested a different dataset
    # without providing its configuration.
    configuration_error = check_dataset_configuration(user_message)

    if configuration_error:

        messages.append({
            "role": "assistant",
            "content": configuration_error
        })

        return configuration_error, messages

    max_tool_rounds = 5

    for _ in range(max_tool_rounds + 1):

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_completion_tokens=2048,
            reasoning_effort="low",
            include_reasoning=False
        )

        assistant_message = response.choices[0].message

        # Check whether Groq requested any tools.
        if not assistant_message.tool_calls:

            final_answer = assistant_message.content or (
                "I could not generate a response."
            )

            messages.append({
                "role": "assistant",
                "content": final_answer
            })

            return final_answer, messages

        # Add the assistant's tool-call message to history.
        messages.append(
            assistant_message.model_dump(exclude_none=True)
        )

        # Execute every requested tool.
        for tool_call in assistant_message.tool_calls:

            try:
                tool_result = execute_tool(tool_call)

            except Exception as error:
                tool_result = json.dumps({
                    "status": "error",
                    "message": str(error)
                })

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "content": tool_result
            })

    raise RuntimeError(
        "Maximum tool execution rounds reached. "
        "Please try a simpler request."
    )
