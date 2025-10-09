import enum
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from clickhouse_connect.driver.exceptions import ClickHouseError
from pydantic import BaseModel

from cxs.core.persistance.clickhouse import ch_client

logger = logging.getLogger(__name__)

import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from clickhouse_connect.driver.exceptions import ClickHouseError
from cxs.core.persistance.clickhouse import ch_client

logger = logging.getLogger(__name__)

class ColumnType(enum.Enum):
    simple = "Simple"
    array = "Array"
    map = "Map"
    nested = "Nested"

class ValueType(enum.Enum):
    simple = "String"
    array = "Number"
    map = "Date"
    nested = "UUID"

class ColumnProfile(BaseModel):
    min_value: Optional[Union[datetime, float]] = None # only for date and numeric types
    max_value: Optional[Union[datetime, float]] = None # only for date and numeric types
    avg_value: Optional[float] = None # only for numeric types
    unique_keys: Optional[List[str]] = None # only for map types
    values: Optional[List[Any]] = None # only for map types
    has_values: bool = False # indicates if the column has values or nor

class ColumnDetails(BaseModel):
    name: str
    type: ColumnType
    value_type: ValueType
    required: bool
    key_type: Optional[ValueType] = None
    value_type: Optional[ValueType] = None
    is_nested: bool = False
    nest_name: Optional[str] = None
    profile: Optional[ColumnProfile] = None

def profile_clickhouse_table(database: str, table_name: str, where_clause: str = "") -> Dict[str, Any]:
    """
    Profile a ClickHouse table by analyzing its columns based on their data types.

    For string columns: Count distinct values
    For numeric columns: Calculate min, max, avg
    For map columns: Extract unique keys

    Args:
        database: Name of the ClickHouse database
        table_name: Name of the ClickHouse table to profile
        where_clause: Optional WHERE clause to scope the profiling to a subset of data
                     (do not include the 'WHERE' keyword)

    Returns:
        Dictionary with profiling results for each column

    Raises:
        ClickHouseError: If there's an error executing queries on ClickHouse
        ValueError: If the table doesn't exist or client is not connected

    Example:
        >>> profile_results = profile_clickhouse_table("my_table", "created_at > '2023-01-01'")
        >>> print_profile_results(profile_results)
    """
    if ch_client is None:
        raise ValueError("ClickHouse client is not connected")

    # Validate table exists
    try:
        tables = ch_client.query(f"SHOW TABLES in {database}").result_rows
        table_exists = any(table[0] == table_name for table in tables)
        if not table_exists:
            raise ValueError(f"Table '{database}.{table_name}' does not exist")
    except ClickHouseError as e:
        logger.error(f"Error checking if table exists: {str(e)}")
        raise

    # Get table schema
    try:
        schema_query = f"DESCRIBE TABLE {database}.{table_name}"
        schema_df = ch_client.query_df(schema_query)

        if schema_df.empty:
            raise ValueError(f"Could not retrieve schema for table '{database}.{table_name}'")
    except ClickHouseError as e:
        logger.error(f"Error retrieving table schema: {str(e)}")
        raise

    # Prepare WHERE clause if provided
    where_condition = f"WHERE {where_clause}" if where_clause else ""

    # Initialize results dictionary
    results = {
        "database": database,
        "table_name": table_name,
        "row_count": 0,
        "columns": {}
    }

    # Get total row count (with WHERE clause if provided)
    try:
        count_query = f"SELECT count() FROM {database}.{table_name} {where_condition}"
        count_result = ch_client.query(count_query)
        results["row_count"] = count_result.result_rows[0][0]

        # If table is empty, return early
        if results["row_count"] == 0:
            return results
    except ClickHouseError as e:
        logger.error(f"Error counting rows: {str(e)}")
        raise

    # Process each column based on its type
    for _, row in schema_df.iterrows():
        column_name = row['name']
        column_type = row['type'].lower()

        # Skip processing if column name contains special characters that might cause SQL issues
        if not re.match(r'^[a-zA-Z0-9_]+$', column_name):
            results["columns"][column_name] = {
                "type": column_type,
                "error": "Column name contains special characters"
            }
            continue

        column_info = {"type": column_type}

        try:
            # For string types
            if any(string_type in column_type for string_type in ['string', 'fixedstring', 'enum']):
                # Count distinct values, but limit to avoid excessive load
                distinct_query = f"""
                    SELECT uniq({column_name}) 
                    FROM {database}.{table_name} 
                    {where_condition}
                """
                distinct_count = ch_client.query(distinct_query).result_rows[0][0]
                column_info["distinct_count"] = distinct_count

                # If there are few distinct values, get them (up to a reasonable limit)
                if distinct_count > 0 and distinct_count <= 100:
                    values_query = f"""
                        SELECT DISTINCT {column_name}
                        FROM {database}.{table_name}
                        {where_condition}
                        LIMIT 100
                    """
                    values_result = ch_client.query(values_query)
                    column_info["values"] = [row[0] for row in values_result.result_rows if row[0] is not None]

            # For numeric types
            elif any(num_type in column_type for num_type in ['int', 'float', 'decimal', 'double', 'uint']):
                stats_query = f"""
                    SELECT 
                        min({column_name}), 
                        max({column_name}), 
                        avg({column_name})
                    FROM {database}.{table_name}
                    {where_condition}
                """
                stats_result = ch_client.query(stats_query).result_rows[0]
                column_info.update({
                    "min": stats_result[0],
                    "max": stats_result[1],
                    "avg": stats_result[2]
                })

            # For date and datetime types
            elif any(date_type in column_type for date_type in ['date', 'datetime']):
                stats_query = f"""
                    SELECT 
                        min({column_name}), 
                        max({column_name})
                    FROM {database}.{table_name}
                    {where_condition}
                """
                stats_result = ch_client.query(stats_query).result_rows[0]
                column_info.update({
                    "min": stats_result[0],
                    "max": stats_result[1]
                })

            # For map types
            elif 'map(' in column_type:
                # Extract unique keys from map columns
                # This is more complex and depends on ClickHouse version
                # Using a simpler approach that works with recent versions
                keys_query = f"""
                    SELECT 
                        flatten(groupUniqArray(mapKeys(dimensions))) as keys
                    FROM {database}.{table_name}
                    {where_condition}
                """
                try:
                    keys_result = ch_client.query(keys_query)
                    column_info["unique_keys"] = [row[0] for row in keys_result.keys]
                except ClickHouseError:
                    # Fallback for older ClickHouse versions or if the query fails
                    column_info["error"] = "Could not extract map keys with current ClickHouse version"

            # For array types
            elif 'array(' in column_type:
                # Get array statistics
                length_query = f"""
                    SELECT 
                        min(length({column_name})), 
                        max(length({column_name})), 
                        avg(length({column_name}))
                    FROM {database}.{table_name}
                    {where_condition}
                """
                length_result = ch_client.query(length_query).result_rows[0]
                column_info.update({
                    "min_length": length_result[0],
                    "max_length": length_result[1],
                    "avg_length": length_result[2]
                })

            # For other types, just note the type
            else:
                column_info["note"] = "Basic type information only"

            # Add null count for all columns - FIXED: Use AND instead of WHERE when where_condition is not empty
            null_query = f"""
                SELECT count() 
                FROM {database}.{table_name} 
                {where_condition}
                {"AND" if where_clause else "WHERE"} {column_name} IS NULL
            """
            null_count = ch_client.query(null_query).result_rows[0][0]
            column_info["null_count"] = null_count
            column_info["null_percentage"] = (null_count / results["row_count"]) * 100 if results[
                                                                                              "row_count"] > 0 else 0

        except ClickHouseError as e:
            column_info["error"] = str(e)
            logger.warning(f"Error profiling column '{column_name}': {str(e)}")

        results["columns"][column_name] = column_info

    return results


def print_profile_results(profile_results: Dict[str, Any]) -> None:
    """
    Print the results from profile_clickhouse_table in a readable format.

    Args:
        profile_results: The dictionary returned by profile_clickhouse_table

    Example:
        >>> profile_results = profile_clickhouse_table("my_table")
        >>> print_profile_results(profile_results)
    """
    if not profile_results:
        print("No profile results to display")
        return

    database = profile_results.get("database", "Unknown table")
    table_name = profile_results.get("table_name", "Unknown table")
    row_count = profile_results.get("row_count", 0)
    columns = profile_results.get("columns", {})

    print(f"\n{'=' * 80}")
    print(f"TABLE PROFILE: {database}.{table_name}")
    print(f"{'=' * 80}")
    print(f"Row count: {row_count:,}")
    print(f"{'-' * 80}")

    if not columns:
        print("No column information available")
        return

    # Sort columns by name for consistent output
    for column_name in sorted(columns.keys()):
        column_info = columns[column_name]
        column_type = column_info.get("type", "Unknown type")

        print(f"\nCOLUMN: {column_name}")
        print(f"Type: {column_type}")

        # Print error if present
        if "error" in column_info:
            print(f"ERROR: {column_info['error']}")
            continue

        # Print null statistics
        null_count = column_info.get("null_count", 0)
        null_percentage = column_info.get("null_percentage", 0)
        print(f"Null values: {null_count:,} ({null_percentage:.2f}%)")

        # Print type-specific information
        if any(string_type in column_type for string_type in ['string', 'fixedstring', 'enum']):
            distinct_count = column_info.get("distinct_count", 0)
            print(f"Distinct values: {distinct_count:,}")

            if "values" in column_info and column_info["values"]:
                values = column_info["values"]
                if len(values) <= 10:
                    print(f"Values: {', '.join(str(v) for v in values)}")
                else:
                    print(f"Values (first 10 of {len(values)}): {', '.join(str(v) for v in values[:10])}")

        elif any(num_type in column_type for num_type in ['int', 'float', 'decimal', 'double', 'uint']):
            min_val = column_info.get("min")
            max_val = column_info.get("max")
            avg_val = column_info.get("avg")

            if min_val is not None:
                print(f"Min: {min_val:,}")
            if max_val is not None:
                print(f"Max: {max_val:,}")
            if avg_val is not None:
                print(f"Avg: {avg_val:,}")

        elif any(date_type in column_type for date_type in ['date', 'datetime']):
            min_date = column_info.get("min")
            max_date = column_info.get("max")

            if min_date is not None:
                print(f"Min date: {min_date}")
            if max_date is not None:
                print(f"Max date: {max_date}")

        elif 'map(' in column_type:
            if "unique_keys" in column_info and column_info["unique_keys"]:
                keys = column_info["unique_keys"]
                if len(keys) <= 10:
                    print(f"Unique keys: {', '.join(str(k) for k in keys)}")
                else:
                    print(f"Unique keys (first 10 of {len(keys)}): {', '.join(str(k) for k in keys[:10])}")

        elif 'array(' in column_type:
            min_length = column_info.get("min_length")
            max_length = column_info.get("max_length")
            avg_length = column_info.get("avg_length")

            if min_length is not None:
                print(f"Min length: {min_length:,}")
            if max_length is not None:
                print(f"Max length: {max_length:,}")
            if avg_length is not None:
                print(f"Avg length: {avg_length:.2f}")

    print(f"\n{'=' * 80}\n")


def profile_sample_with_where(database: str, table_name: str, where_clause: str | None = None) -> dict | None:
    """Profile the sample table with a WHERE clause and display the results."""
    if ch_client is None:
        logger.error("ClickHouse client is not connected. Check your environment variables.")
        return None

    try:
        profile_results = profile_clickhouse_table(database, table_name, where_clause)
        print_profile_results(profile_results)
        logger.info("Profiling with WHERE clause completed successfully.")

    except Exception as e:
        logger.error(f"Error profiling table with WHERE clause: {str(e)}")
        return None

    return profile_results


if __name__ == "__main__":
    profile_results = profile_sample_with_where("cst", "entities", "partition = 'lyfja.is'")