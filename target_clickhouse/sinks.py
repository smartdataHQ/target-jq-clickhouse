"""clickhouse target sink class, which handles writing streams."""

from __future__ import annotations

import uuid
from logging import Logger
from typing import Any, Iterable

import jsonschema.exceptions as jsonschema_exceptions
import pandas as pd
import requests
import simplejson as json
import sqlalchemy
from pendulum import now
from singer_sdk.helpers._compat import (
    date_fromisoformat,
    datetime_fromisoformat,
    time_fromisoformat,
)
from singer_sdk.helpers._typing import (
    DatetimeErrorTreatmentEnum,
    get_datelike_property_type,
    handle_invalid_timestamp_in_record,
)
from singer_sdk.sinks import SQLSink
from sqlalchemy.sql.expression import bindparam

import jq
from target_clickhouse.semantic_events_jq import semantic_events_jq_expression
from target_clickhouse.connectors import ClickhouseConnector
from target_clickhouse.utils.ch_df_utils import flatten_nested_fields, remove_all_empty_columns, \
    replace_none_where_needed
from target_clickhouse.utils.json_utils import json_serialize
from target_clickhouse.utils.persistence import get_clickhouse_connection

from cxs.core.schema.semantic_event import SemanticEvent


class ClickhouseSink(SQLSink):
    """clickhouse target sink class."""

    connector_class = ClickhouseConnector

    @property
    def full_table_name(self) -> str:
        """Return the fully qualified table name.

        Returns
            The fully qualified table name.

        """
        # Use the config table name if set.
        _table_name = self.config.get("table_name")

        if _table_name is not None:
            return _table_name

        return self.connector.get_fully_qualified_name(
            table_name=self.table_name,
            schema_name=self.schema_name,
            db_name=self.database_name,
        )

    @property
    def datetime_error_treatment(self) -> DatetimeErrorTreatmentEnum:
        """Return a treatment to use for datetime parse errors: ERROR. MAX, or NULL."""
        return DatetimeErrorTreatmentEnum.NULL

    def bulk_insert_records(
        self,
        full_table_name: str,
        schema: dict,
        records: Iterable[dict[str, Any]],
    ) -> int | None:
        """Bulk insert records to an existing destination table.

        The default implementation uses a generic SQLAlchemy bulk insert operation.
        This method may optionally be overridden by developers in order to provide
        faster, native bulk uploads.

        Args:
            full_table_name: the target table name.
            schema: the JSON schema for the new table, to be used when inferring column
                names.
            records: the input records.

        Returns:
            True if table exists, False if not, None if unsure or undetectable.

        """
        df = pd.DataFrame(records)
        df_json = df.to_json(orient="records")

        # Usage
        df_json_serialized = json_serialize(df_json)
        records_serializable = json.loads(df_json_serialized)

        jq_expression = semantic_events_jq_expression()

        records_transformed = jq.compile(jq_expression).input_value(records_serializable).all()
        self.logger.info("records_transformed")

        client = get_clickhouse_connection(
            host=self.config.get("host"),
            port=self.config.get("port"),
            username=self.config.get("username"),
            password=self.config.get("password"),
            database=self.config.get("database")
        )

        metadata, items = flatten_nested_fields(client=client, items=records_transformed[0])

        df = pd.DataFrame(items)
        df["entity_gid"] = df["entity_gid"].apply(lambda x: uuid.uuid5(uuid.NAMESPACE_URL, str(x)))
        df["event_gid"] = df["event_gid"].apply(lambda x: uuid.uuid5(uuid.NAMESPACE_URL, str(x)))

        df = remove_all_empty_columns(dataframe=df)
        df = replace_none_where_needed(metadata=metadata, dataframe=df)
        rows = client.insert_df(df=df, table=f"{self.config.get('database')}.{self.config.get('table_name')}")
        written_rows = int(rows.summary["written_rows"])
        return written_rows

    def activate_version(self, new_version: int) -> None:
        """Bump the active version of the target table.

        Args:
            new_version: The version number to activate.

        """
        # There's nothing to do if the table doesn't exist yet
        # (which it won't the first time the stream is processed)
        if not self.connector.table_exists(self.full_table_name):
            return

        deleted_at = now()

        if not self.connector.column_exists(
            full_table_name=self.full_table_name,
            column_name=self.version_column_name,
        ):
            print(self.version_column_name)

        if not self.connector.column_exists(
            full_table_name=self.full_table_name,
            column_name=self.soft_delete_column_name,
        ):
            self.connector.prepare_column(
                self.full_table_name,
                self.soft_delete_column_name,
                sql_type=sqlalchemy.types.DateTime(),
            )

        query = sqlalchemy.text(
            f"SELECT 1"
        )
        query = query.bindparams(
            bindparam("deletedate", value=deleted_at, type_=sqlalchemy.types.DateTime),
            bindparam("version", value=new_version, type_=sqlalchemy.types.Integer),
        )
        with self.connector._connect() as conn, conn.begin():  # noqa: SLF001
            conn.execute(query)

    def _validate_and_parse(self, record: dict) -> dict:
        """Pre-validate and repair records for string type mismatches, then validate.

        Args:
            record: Individual record in the stream.

        Returns:
            Validated record.

        """
        # Pre-validate and correct string type mismatches.
        record = pre_validate_for_string_type(record, self.schema, self.logger)

        try:
            self._validator.validate(record)
            self._parse_timestamps_in_record(
                record=record,
                schema=self.schema,
                treatment=self.datetime_error_treatment,
            )
        except jsonschema_exceptions.ValidationError as e:
            if self.logger:
                self.logger.exception(f"Record failed validation: {record}")
            raise e  # : RERAISES

        return record

    def _parse_timestamps_in_record(
        self,
        record: dict,
        schema: dict,
        treatment: DatetimeErrorTreatmentEnum,
    ) -> None:
        """Parse strings to datetime.datetime values, repairing or erroring on failure.

        Attempts to parse every field that is of type date/datetime/time. If its value
        is out of range, repair logic will be driven by the `treatment` input arg:
        MAX, NULL, or ERROR.

        Args:
            record: Individual record in the stream.
            schema: TODO
            treatment: TODO

        """
        for key, value in record.items():
            if key not in schema["properties"]:
                self.logger.warning("No schema for record field '%s'", key)
                continue
            datelike_type = get_datelike_property_type(schema["properties"][key])
            if datelike_type:
                date_val = value
                try:
                    if value is not None:
                        if datelike_type == "time":
                            date_val = time_fromisoformat(date_val)
                        elif datelike_type == "date":
                            # Trim time value from date fields.
                            if "T" in date_val:
                                # Split on T and get the first part.
                                date_val = date_val.split("T")[0]
                                self.logger.warning(
                                    "Trimmed time value from date field '%s': %s",
                                    key,
                                    date_val,
                                )
                            date_val = date_fromisoformat(date_val)
                        else:
                            date_val = datetime_fromisoformat(date_val)
                except ValueError as ex:
                    date_val = handle_invalid_timestamp_in_record(
                        record,
                        [key],
                        date_val,
                        datelike_type,
                        ex,
                        treatment,
                        self.logger,
                    )
                record[key] = date_val


def pre_validate_for_string_type(
    record: dict,
    schema: dict,
    logger: Logger | None = None,
) -> dict:
    """Pre-validate record for string type mismatches and correct them.

    Args:
        record: Individual record in the stream.
        schema: JSON schema for the stream.
        logger: Logger to use for logging.

    Returns:
        Record with corrected string type mismatches.

    """
    if schema is None:
        if logger:
            logger.debug("Schema is None, skipping pre-validation.")
        return record

    for key, value in record.items():
        # Checking if the schema expects a string for this key.
        key_properties = schema.get("properties", {}).get(key, {})
        expected_type = key_properties.get("type")
        if expected_type is None:
            continue
        if not isinstance(expected_type, list):
            expected_type = [expected_type]

        if "null" in expected_type and value is None:
            continue

        if "object" in expected_type and isinstance(value, dict):
            pre_validate_for_string_type(
                value,
                schema.get("properties", {}).get(key),
                logger,
            )
        elif "array" in expected_type and isinstance(value, list):
            items_schema = key_properties.get("items")
            for i, item in enumerate(value):
                if "object" in items_schema["type"] and isinstance(item, dict):
                    value[i] = pre_validate_for_string_type(
                        item,
                        key_properties.get("items"),
                        logger,
                    )
        elif "string" in expected_type and not isinstance(value, str):
            # Convert the value to string if it's not already a string.
            record[key] = (
                json.dumps(record[key])
                if isinstance(value, (dict, list))
                else str(value)
            )
            if logger:
                logger.debug(
                    f"Converted field {key} to string: {record[key]}",
                )

    return record
