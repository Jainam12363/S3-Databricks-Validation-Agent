
import os
import re

from dotenv import load_dotenv
from databricks import sql


load_dotenv()


def read_target_data(catalog, schema, table):
    # Validate SQL identifiers before using them in the query.
    for identifier in [catalog, schema, table]:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identifier):
            raise ValueError(f"Invalid Databricks identifier: {identifier}")

    server_hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME")
    http_path = os.getenv("DATABRICKS_HTTP_PATH")
    access_token = os.getenv("DATABRICKS_TOKEN")

    if not all([server_hostname, http_path, access_token]):
        raise ValueError("Missing Databricks configuration in .env file.")

    table_name = f"`{catalog}`.`{schema}`.`{table}`"

    with sql.connect(
        server_hostname=server_hostname,
        http_path=http_path,
        access_token=access_token
    ) as connection:

        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name}")

            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()

            records = [
                dict(zip(columns, row))
                for row in rows
            ]

            return records
