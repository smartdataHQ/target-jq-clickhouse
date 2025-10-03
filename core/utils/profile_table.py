"""
ClickHouse Table Profiling Utility

This module provides tools for profiling ClickHouse database tables, analyzing their structure,
and collecting statistics about columns. It can be used to understand the schema and data
characteristics of ClickHouse tables, which is useful for data exploration and quality assessment.

The module supports various column types, including basic types, arrays, maps, and nested structures.
It can analyze data distributions, identify unique values, and calculate basic statistics for
numeric columns.

Example usage:
    profile_results = profile_table(
        database="my_database", 
        table_name="my_table", 
        partitions: List of partitions to profile (not used in this function, but can be extended)
        where_clause="partition = 'my_partition'",
        config={"nested_column": {"type_column": "type"}})

"""

import enum
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from clickhouse_connect.driver.exceptions import ClickHouseError
from pydantic import BaseModel, Field

from cxs.core.persistance.clickhouse import ch_client

logger = logging.getLogger(__name__)


class ColumnType(enum.Enum):
    """Enum representing the structural type of ClickHouse column."""
    BASIC = "Basic"
    ARRAY = "Array"
    MAP = "Map"
    GROUPED = "Grouped" # Grouped columns share the same prefix - e.g., 'campaign.id' - but are not nested arrays.
    NESTED = "Nested"

class ValueType(enum.Enum):
    """Enum representing the data type of ClickHouse column value."""
    STRING = "String"
    NUMBER = "Number"
    DATE = "Date"
    UUID = "UUID"
    BOOLEAN = "Boolean"
    OTHER = "Other"

class ColumnProfile(BaseModel):
    """
    Model representing profiling statistics for a column.
    
    This class stores various statistics about a column's data, including value ranges,
    cardinality information, and presence of values. Different statistics are relevant
    for different column types (e.g., min/max for numeric types, unique values for strings).
    """

    # For numeric types
    min_value: Optional[Union[datetime, float, int]] = Field(None, description="Minimum value (for numeric and date types)")
    max_value: Optional[Union[datetime, float, int]] = Field(None, description="Maximum value (for numeric and date types)")
    avg_value: Optional[float] = Field(None, description="Average value (for numeric types)")

    # General statistics
    value_rows: Optional[int] = Field(None, description="Number of NULL values")
    unique_values: Optional[int] = Field(None, description="Number of distinct values (for string types)")
    unique_keys: Optional[List[str]] = Field(None, description="List of unique keys (for map types)")
    value_list: Optional[dict[str,List[str]]] = Field(default_factory=dict, description="List of unique values for each key (for map types)")

    # For all types
    has_values: bool = Field(False, description="Indicates if the column has any non-NULL values")
    

class ColumnDetails(BaseModel):
    """Model representing schema details for a column."""
    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Original ClickHouse type as string")

    column_type: ColumnType = Field(..., description="Structural type of the column")
    key_data_type: Optional[ValueType] = Field(None, description="Data type of the column values")
    value_data_type: ValueType = Field(..., description="Data type of the column values")

    required: bool = Field(False, description="Whether the column is required (not nullable)")

    # For nested types
    is_nested: bool|None = Field(False, description="Whether this is a nested column")
    is_nested_subcolumn: bool|None = Field(False, description="Whether this is a subcolumn of a nested structure")

    parent_name: Optional[str] = Field(None, description="Parent column if this is a subcolumn")
    child_name: Optional[str] = Field(None, description="Child name if this is a subcolumn")
    nested_path: Optional[List[str]|None] = Field(None, description="Path of nested structure (for deeply nested columns)")
    
    # Profiling information
    profile: Optional[ColumnProfile] = Field(None, description="Profiling information for this column")

class NestedColumnInfo(BaseModel):
    """Model representing information about a nested column structure."""
    parent_name: str = Field(..., description="Name of the parent nested column")
    subcolumns: List[ColumnDetails] = Field(default_factory=list, description="List of subcolumn names in this nested structure")
    column_type: ColumnType = Field(ColumnType.NESTED, description="Structural type of the nested column")
    profile: Optional[ColumnProfile] = Field(None, description="Profiling information for this nested column")

class GroupedColumnInfo(BaseModel):
    """Model representing information about a nested column structure."""
    parent_name: str = Field(..., description="Name of the parent nested column")
    subcolumns: List[ColumnDetails] = Field(default_factory=list, description="List of subcolumn names in this nested structure")
    column_type: ColumnType = Field(ColumnType.NESTED, description="Structural type of the nested column")
    profile: Optional[ColumnProfile] = Field(None, description="Profiling information for this nested column")



class ProfiledTable(BaseModel):
    """
    Model representing a profiled ClickHouse table.
    
    This class stores information about a table that has been profiled, including
    its database and table name, the WHERE clause used for filtering, the number of rows
    that were analyzed, and detailed information about each column in the table.
    
    The column dictionary contains either ColumnDetails objects for regular columns
    or NestedColumnInfo objects for nested structures.
    """
    database: str = Field(..., description="Database name containing the table")
    table: str = Field(..., description="Table name that was profiled")
    where_clause: Optional[str] = Field(None, description="WHERE clause used for profiling")
    rows: Optional[int] = Field(None, description="Number of rows in the table that were profiled")
    columns: Dict[str, ColumnDetails | NestedColumnInfo | GroupedColumnInfo] = Field(default_factory=dict, description="Dictionary of column profiles keyed by column name")

## --- Configuration ---
# Set of known type annotations in ClickHouse
CLICKHOUSE_ANNOTATIONS = {'lowcardinality', 'nullable'}

def parse_ch_types(type_string: str) -> dict | None:
    """
    Parses a ClickHouse type into a dictionary with explicit keys for
    Map types (key, value) and a 'root_type' field for all types.
    """
    type_string = type_string.strip().lower()
    annotations = []

    # 1. Peel away annotations.
    while True:
        try:
            first_paren_index = type_string.index('(')
            if not type_string.endswith(')'):
                break

            outer_name = type_string[:first_paren_index]
            if outer_name in CLICKHOUSE_ANNOTATIONS:
                annotations.append(outer_name)
                type_string = type_string[first_paren_index + 1:-1].strip()
            else:
                break
        except ValueError:
            break

    # 2. Parse the core type.
    try:
        first_paren_index = type_string.index('(')
        if not type_string.endswith(')'):
            return None

        core_type = type_string[:first_paren_index]
        content = type_string[first_paren_index + 1:-1]

        args = []
        if content.strip():
            level = 0
            start_index = 0
            for i, char in enumerate(content):
                if char == '(':
                    level += 1
                elif char == ')':
                    level -= 1
                elif char == ',' and level == 0:
                    arg = parse_ch_types(content[start_index:i])
                    if not arg: return None
                    args.append(arg)
                    start_index = i + 1

            last_arg = parse_ch_types(content[start_index:])
            if not last_arg: return None
            args.append(last_arg)

        # 3. Format the output based on the root type.
        result = {'data_type': core_type, 'annotations': annotations}
        if core_type == 'Map':
            if len(args) != 2:
                return None  # Map must have exactly two arguments.
            result['key'] = args[0]
            result['value'] = args[1]
        else:
            result['args'] = args

        return result

    except ValueError:
        # Simple type.
        return {'data_type': type_string, 'annotations': annotations, 'args': []}

def resolve_datatype(data_type: str) -> ValueType:
    """
    Maps a ClickHouse data type string to a ValueType enum.
    
    This function analyzes the given data type string and determines which
    high-level category it belongs to (string, number, date, etc.).
    
    Args:
        data_type: The ClickHouse data type as a string (e.g., 'String', 'Int32', 'DateTime')
        
    Returns:
        A ValueType enum representing the high-level category of the data type
    """
    data_type = data_type.lower()
    if 'string' in data_type or 'fixedstring' in data_type or 'enum' in data_type:
        return ValueType.STRING
    elif any(num_type in data_type for num_type in ['int', 'float', 'decimal', 'double', 'uint']):
        return ValueType.NUMBER
    elif any(date_type in data_type for date_type in ['date', 'datetime']):
        return ValueType.DATE
    elif 'uuid' in data_type:
        return ValueType.UUID
    elif 'bool' in data_type:
        return ValueType.BOOLEAN
    else:
        return ValueType.OTHER

def determine_column_type(column_name: str, column_type_str: str) -> Tuple[ColumnType, ValueType, ValueType]:
    """
    Analyzes a ClickHouse column type string and determines its structural and value types.
    
    This function parses the given column type string to identify whether it's a basic type,
    an array, a map, or a nested structure. It also determines the data types of the values
    (and keys for map types).
    
    Args:
        column_type_str: The ClickHouse column type as a string (e.g., 'String', 'Array(Int32)', 'Map(String, Float64)')
        
    Returns:
        A tuple containing:
        - ColumnType: The structural type of the column (BASIC, ARRAY, MAP)
        - ValueType: The data type of the values
        - ValueType or None: The data type of the keys (for map types) or None (for other types)
        
    Raises:
        ValueError: If the array or map type definition is invalid
    """
    column_type_str = column_type_str.lower()
    
    structure = parse_ch_types(column_type_str)
    data_type = structure.get('data_type')
    key_data_type = None

    if data_type == 'array':
        column_type = ColumnType.ARRAY
        if structure.get('args'):
            value_data_type = resolve_datatype(structure.get('args', [])[0].get('data_type'))
        else:
            raise ValueError(f"Invalid array type definition: {column_type_str}")
    elif data_type == 'map':
        column_type = ColumnType.MAP
        if structure.get('args') and len(structure['args']) == 2:
            key_data_type = resolve_datatype(structure['args'][0].get('data_type'))
            value_data_type = resolve_datatype(structure['args'][1].get('data_type'))
        else:
            raise ValueError(f"Invalid map type definition: {column_type_str}")
    elif '.' in column_name:
        column_type = ColumnType.GROUPED
        value_data_type = resolve_datatype(structure.get('data_type'))
    else:
        column_type = ColumnType.BASIC
        value_data_type = resolve_datatype(structure.get('data_type'))

    return column_type, value_data_type, key_data_type


def profile_ch_table(database: str, table_name: str, where_clause: str = "", config: dict | None = None, lc_probe:bool=False) -> ProfiledTable:
    """
    Profiles a ClickHouse table by analyzing its schema and collecting statistics about its columns.
    
    This function retrieves the schema of the specified table, analyzes each column's type,
    and collects statistics about the data in each column (e.g., unique values, min/max values).
    It can optionally filter the data using a WHERE clause.
    
    Args:
        database: The name of the ClickHouse database
        table_name: The name of the table to profile
        where_clause: Optional WHERE clause to filter the data (without the "WHERE" keyword)
        config: Optional configuration for special column handling, particularly for nested columns
               Format: {"nested_column_name": {"type_column": "type_column_name"}}
        
    Returns:
        A ProfiledTable object containing the profiling results
        
    Raises:
        ValueError: If the ClickHouse client is not connected or the table doesn't exist
        ClickHouseError: If there's an error executing a query
    """
    if ch_client is None:
        raise ValueError("ClickHouse client is not connected")

    profiled_table = ProfiledTable(database=database, table=table_name, where_clause=where_clause, rows=0, columns={})

    # Validate table exists
    try:
        tables = ch_client.query(f"SHOW TABLES in `{database}`").result_rows
        table_exists = any(table[0] == table_name for table in tables)
        if not table_exists:
            raise ValueError(f"Table {database}.`{table_name}' does not exist")
    except ClickHouseError as e:
        logger.error(f"Error checking if table exists: {str(e)}")
        raise

    # Get table schema (using cache)
    try:
        schema_df = ch_client.query_df(f"DESCRIBE TABLE {database}.`{table_name}`")
        if schema_df is None or schema_df.empty:
            raise ValueError(f"Could not retrieve schema for table {database}.`{table_name}'")
    except ClickHouseError as e:
        logger.error(f"Error retrieving table schema: {str(e)}")
        raise

    # Get total row count (with WHERE clause if provided)
    try:
        where_condition = f"WHERE {where_clause}" if where_clause else ""
        count_query = f"SELECT count() FROM {database}.`{table_name}` {where_condition}"
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Executing count query: {count_query}")
            
        count_result = ch_client.query(count_query)
        profiled_table.rows = count_result.result_rows[0][0]
    except ClickHouseError as e:
        logger.error(f"Error counting rows: {str(e)}")
        raise

    try:
        for _, row in schema_df.iterrows():
            column_name = row['name']
            column_type_str = row['type'].lower()

            # Check if this is a nested column (contains a dot)
            child_name = column_name
            parent_name = None
            is_first_nested = None
            is_nested_column = None

            column_type, value_data_type, key_data_type = determine_column_type(column_name, column_type_str)

            if '.' in column_name:
                parent_name, child_name = column_name.split('.', 1)
                is_nested_column = True

                if parent_name not in profiled_table.columns:
                    if column_type == ColumnType.GROUPED:
                        profiled_table.columns[parent_name] = GroupedColumnInfo(parent_name=parent_name)
                    else:
                        profiled_table.columns[parent_name] = NestedColumnInfo(parent_name=parent_name)
                    is_first_nested = True

            column_details = ColumnDetails(
                name=column_name,
                type=column_type_str,
                column_type=column_type,
                key_data_type=key_data_type,
                value_data_type=value_data_type,
                required=False,
                is_nested=is_first_nested,
                is_nested_subcolumn=is_nested_column,
                parent_name=parent_name,
                child_name=child_name,
                nested_path=[parent_name,child_name] if parent_name and child_name else [column_name]
            )

            if is_nested_column:
                profiled_table.columns[parent_name].subcolumns.append(column_details)
            else:
                profiled_table.columns[column_name] = column_details

        # Second pass: profile columns using batching
        row_count = profiled_table.rows
        if row_count > 0:  # Only profile if there's data
            columns_to_profile = []

            for column_name, column_details in list(profiled_table.columns.items()):
                if not (isinstance(column_details, ColumnDetails) and column_details.is_nested_subcolumn):
                    columns_to_profile.append((column_name, column_details))

            # Process columns in batches
            where_condition = f"WHERE {where_clause}" if where_clause else ""

            # Process basic columns in batches
            batch_size = 10  # Adjust based on your needs
            for i in range(0, len(columns_to_profile), batch_size):
                batch = columns_to_profile[i:i+batch_size]
                probe_columns_batch(database, table_name, batch, where_condition, config)

            if lc_probe:
                profile_low_cardinality_columns(database, table_name, columns_to_profile, where_condition, config)

    except Exception as e:
        logger.error(f"Error processing rows: {str(e)}")
        raise

    return profiled_table

def profile_low_cardinality_columns(database: str, table_name: str, analysed_columns: List[Tuple[str, ColumnDetails | NestedColumnInfo | GroupedColumnInfo]], where_condition: str, config: dict | None = None) -> None:
    select_parts = []
    for column, column_details in analysed_columns:
        if isinstance(column_details, ColumnDetails) and column_details.value_data_type == ValueType.STRING:
            if column_details.profile and column_details.profile.unique_values and column_details.profile.unique_values > 1 and column_details.profile.unique_values < 200:
                if column_details.column_type == ColumnType.MAP and column_details.profile.unique_keys:
                    for map_key in column_details.profile.unique_keys:
                        select_parts.append(
                            f"arraySort(groupUniqArray(trim(`{column}`['{map_key}']))) as `{column}__{map_key}__map_keys`"
                        )
                elif column_details.column_type == ColumnType.BASIC:
                    select_parts.append(f"arraySort(groupUniqArray(`{column}`)) as `{column}__{column}__map_keys`")

    if select_parts:
        query = f"SELECT {', '.join(select_parts)} FROM {database}.`{table_name}` {where_condition}"
        try:
            results = ch_client.query(query)
            cached_columns = {col[0]: col[1] for col in analysed_columns}
            for res_row in results.named_results():
                for key, value in res_row.items():
                    if '__' in key:
                        col_name, value_key, map_key = key.rsplit('__')
                        column = cached_columns[col_name]
                        column.profile.value_list[value_key] = value if isinstance(value, list) else [value]

        except ClickHouseError as e:
            logger.warning(f"Error executing low cardinality query: {str(e)}")
            raise e


def probe_columns_batch(database: str, table_name: str, columns_batch: List[Tuple[str, ColumnDetails | NestedColumnInfo | GroupedColumnInfo]], where_condition: str, config: dict | None = None) -> None:
    """
    Process a batch of columns in a single query to collect statistics efficiently.
    
    This function builds and executes a single SQL query that collects various statistics
    for multiple columns at once, which is more efficient than querying each column separately.
    Different statistics are collected based on the column type (e.g., min/max for numeric types,
    unique values for all types).
    
    Args:
        database: The name of the ClickHouse database
        table_name: The name of the table to profile
        columns_batch: A list of tuples containing column name and column details
        where_condition: WHERE clause to filter the data (including the "WHERE" keyword if needed)
        config: Optional configuration for special column handling, particularly for nested columns
    
    The function updates the profile attribute of each column in the columns_batch directly.
    """
    
    # Build the query parts for each column
    select_parts = []
    
    for column_name, column_details in columns_batch:
        # Add distinct count for all columns

        # Add type-specific parts
        if column_details.column_type == ColumnType.MAP:
            select_parts.extend([
                f"groupUniqArrayArray(mapKeys(`{column_name}`)) as {column_name}__map_keys",
                f"arrayUniq(flatten(groupArrayArray(mapKeys(`{column_name}`)))) as {column_name}__distinct_count",
                f"countIf(length(mapKeys(`{column_name}`)) > 0) as {column_name}__value_rows"
            ])
        elif column_details.column_type == ColumnType.ARRAY:
            if column_details.value_data_type == ValueType.STRING:
                select_parts.extend([
                    f"countIf(`{column_name}` IS NOT NULL and length(`{column_name}`) > 0) as {column_name}__value_rows",
                    f"uniq(`{column_name}`) as {column_name}__distinct_count",
                    # f"groupUniqArrayArray(arrayMap(t -> lower(trim(t)), `{column_name}`)) as {column_name}__map_keys",
                ])
        elif column_details.column_type == ColumnType.GROUPED:
            pass
        elif column_details.column_type == ColumnType.NESTED:
            first_column = column_details.subcolumns[0] if column_details.subcolumns else None
            type_column = config.get(column_details.parent_name,{}).get('type_column', first_column.child_name)
            select_parts.extend([
                f"arrayDistinct(arrayFlatten(groupArray(`{column_details.parent_name}.{type_column}`))) as {column_name}__map_keys",
                f"countIf(length(arrayFlatten(`{column_details.parent_name}.{type_column}`)) > 0) as {column_name}__value_rows"
            ])
        elif column_details.value_data_type == ValueType.DATE:
            select_parts.extend([
                f"min(`{column_name}`) as {column_name}__min_value",
                f"max(`{column_name}`) as {column_name}__max_value",
                f"countIf(`{column_name}` IS NOT NULL) as {column_name}__value_rows"
            ])
        elif column_details.value_data_type == ValueType.NUMBER:
            select_parts.extend([
                f"min(`{column_name}`) as {column_name}__min_value",
                f"max(`{column_name}`) as {column_name}__max_value",
                f"countIf(`{column_name}` IS NOT NULL and `{column_name}` <> 0) as {column_name}__value_rows"
            ])
        elif column_details.value_data_type == ValueType.STRING:
            select_parts.append(f"uniq(`{column_name}`) as {column_name}__distinct_count")
            select_parts.append(f"countIf(`{column_name}` IS NOT NULL and `{column_name}` != '') as {column_name}__value_rows")
        else:
            select_parts.append(f"uniq(`{column_name}`) as {column_name}__distinct_count")
            select_parts.append(f"countIf(`{column_name}` IS NOT NULL) as {column_name}__value_rows")
    
    # Build and execute the query
    query = f"SELECT {', '.join(select_parts)} FROM {database}.`{table_name}` {where_condition}"
    
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Executing batch query: {query}")
    
    try:
        results = ch_client.query(query)
        
        # Process results
        for profile_row in results.named_results():
            for key, value in profile_row.items():
                # Parse the column name and metric from the result key
                if '_' in key:
                    col_name, metric = key.rsplit('__', 1)
                    
                    # Find the matching column details
                    for name, details in columns_batch:
                        if name == col_name:
                            # Initialize profile if needed
                            if not details.profile:
                                details.profile = ColumnProfile(**{})
                            
                            # Set the appropriate profile attribute
                            if metric == 'map_keys':
                                details.profile.unique_keys = value
                            elif metric == 'distinct_count':
                                details.profile.unique_values = value
                            elif metric == 'min_value':
                                details.profile.min_value = value
                            elif metric == 'max_value':
                                details.profile.max_value = value
                            elif metric == 'value_rows':
                                details.profile.value_rows = value
                                details.profile.has_values = value is not None and value > 0
                            break
    
    except ClickHouseError as e:
        logger.warning(f"Error executing batch query: {str(e)}")


def print_results(profiled_tabel: ProfiledTable) -> None:
    """
    Print profile results in a formatted table with headers and proper alignment.
    """
    if not profiled_tabel:
        print("No profiled table to display")
        return

    # Define headers and their widths
    headers = [
        ("Column Name", 30),
        ("Type", 10),
        ("Value Type", 10),
        ("Key Type", 15),
        ("Value Rows", 10),
        ("Unique Values", 14),
        ("Min Value", 10),
        ("Max Value", 10),
        ("Unique Keys", 40)
    ]
    
    # Print header row
    header_row = " | ".join(f"{header:<{width}}" for header, width in headers)
    print(f"Profiling results for {profiled_tabel.database}.{profiled_tabel.table} (Row Count: {profiled_tabel.rows})")
    print("-" * len(header_row))
    print(header_row)
    print("-" * len(header_row))

    # Extract table information
    for column_details in profiled_tabel.columns.values():

        if isinstance(column_details, NestedColumnInfo):
            row = [
                f"{column_details.parent_name:<{headers[0][1]}}",
                f"{'Nested':<{headers[1][1]}}",
                f"{'Various':<{headers[2][1]}}",
                f"{'':<{headers[3][1]}}",
                f"{str(column_details.profile.value_rows):<{headers[4][1]}}" if column_details and column_details.profile and column_details.profile.value_rows is not None else f"{'0':<{headers[4][1]}}",
                f"{str(len(column_details.profile.unique_keys)):<{headers[5][1]}}" if column_details and column_details.profile and column_details.profile.unique_keys else f"{'0':<{headers[5][1]}}",
                f"{'':<{headers[6][1]}}",
                f"{'':<{headers[7][1]}}",
                f"{column_details.subcolumns[0].child_name + ': ' + str(column_details.profile.unique_keys):<{headers[8][1]}}" if column_details and column_details.profile and column_details.profile.unique_keys else f"{'':<{headers[8][1]}}",
            ]
        elif isinstance(column_details, GroupedColumnInfo):
            row = [
                f"{column_details.parent_name:<{headers[0][1]}}",
                f"{'Grouped':<{headers[1][1]}}",
                f"{'Various':<{headers[2][1]}}",
                f"{'':<{headers[3][1]}}",
                f"{str(column_details.profile.value_rows):<{headers[4][1]}}" if column_details and column_details.profile and column_details.profile.value_rows is not None else f"{'':<{headers[4][1]}}",
                f"{str(len(column_details.profile.unique_keys)):<{headers[5][1]}}" if column_details and column_details.profile and column_details.profile.unique_keys else f"{'':<{headers[5][1]}}",
                f"{'':<{headers[6][1]}}",
                f"{'':<{headers[7][1]}}",
                f"{column_details.subcolumns[0].child_name + ': ' + str(column_details.profile.unique_keys):<{headers[8][1]}}" if column_details and column_details.profile and column_details.profile.unique_keys else f"{'':<{headers[8][1]}}",
            ]
        else:
            profile = column_details.profile
            full_column_name = '.'.join(column_details.nested_path) if column_details.nested_path else column_details.name

            try:

                unique_keys = ""
                min_value = ""
                max_value = ""

                if profile:
                    unique_keys = str(profile.unique_keys)
                    # if len(unique_keys) > headers[-1][1]:
                    #    unique_keys = unique_keys[:headers[-1][1] - 3] + "..."

                    min_value = profile.min_value
                    max_value = profile.max_value

                if len(full_column_name) > headers[0][1]:
                    full_column_name = full_column_name[:headers[0][1] - 3] + "..."

                row = [
                    f"{full_column_name:<{headers[0][1]}}",
                    f"{str(column_details.column_type.value):<{headers[1][1]}}",
                    f"{str(column_details.value_data_type.value):<{headers[2][1]}}",
                    f"{str(column_details.key_data_type.value):<{headers[3][1]}}" if column_details.key_data_type else f"{'':<{headers[3][1]}}",
                    f"{str(profile.value_rows):<{headers[4][1]}}" if profile and profile.value_rows is not None else f"{'0':<{headers[4][1]}}",
                    f"{str(profile.unique_values):<{headers[5][1]}}" if profile and profile.unique_values is not None else f"{'0':<{headers[5][1]}}",
                    f"{str(min_value):<{headers[6][1]}}" if min_value is not None else f"{'':<{headers[6][1]}}",
                    f"{str(max_value):<{headers[7][1]}}" if max_value is not None else f"{'':<{headers[7][1]}}",
                    f"{unique_keys:<{headers[8][1]}}" if unique_keys != 'None' and unique_keys != '[]' else f"{'':<{headers[8][1]}}"
                ]
            except Exception as e:
                logger.error(f"Error printing profile for column '{column_details.name}': {str(e)}")
                continue

        print(" | ".join(row))
    print("-" * len(header_row))

def profile_table(database: str, table_name: str, partitions: list[str], where_clause: str | None = None,
                  config: dict|None = None, lc_probe: bool=False) -> ProfiledTable | None:
    """
    Convenience function to profile a ClickHouse table with an optional WHERE clause and display results.
    
    This function is a wrapper around profile_clickhouse_table that adds error handling and
    automatically prints the results in a formatted table. It's the main entry point for
    profiling a table from the command line or in interactive use.
    
    Args:
        database: The name of the ClickHouse database
        table_name: The name of the table to profile
        partitions: List of partitions to profile (not used in this function, but can be extended)
        where_clause: Optional WHERE clause to filter the data (without the "WHERE" keyword)
        config: Optional configuration for special column handling, particularly for nested columns
               Format: {"nested_column_name": {"type_column": "type_column_name"}}
        
    Returns:
        A ProfiledTable object containing the profiling results, or None if an error occurred
        
    Example:
        profile_results = profile_table(
            database="my_database", 
            table_name="my_table", 
            where_clause="partition = 'my_partition'", 
            config={"nested_column": {"type_column": "type"}})
    """
    if ch_client is None:
        logger.error("ClickHouse client is not connected. Check your environment variables.")
        return None

    partition_where_clause = f"""partition in ['{"'".join(partitions)}']"""
    if where_clause:
        where_clause = f"{partition_where_clause} AND ({where_clause})"
    else:
        where_clause = partition_where_clause

    return profile_ch_table(database, table_name, where_clause or "", config, lc_probe)


if __name__ == "__main__":
    # Example usage with sampling
    # profile_results = profile_table(database="cst", table_name="entities", partitions=['lyfja.is'], where_clause="type = 'Product'", config={"ids": {"type_column": "id_type"}, "content": {"type_column": "type"}, "involves": {"type_column": "entity_type"}}, lc_probe=True)
    profile_results = profile_table(database="dev", table_name="entities")

    # Print the results in a readable format
    print_results(profile_results)

    # You can also use the results programmatically
    if profile_results:
        # Example: Count how many nested structures were found
        nested_structures = set()
        for column_name, column_details in profile_results.columns.items():
            if isinstance(column_details, ColumnDetails) and column_details.is_nested_subcolumn:
                nested_structures.add(column_details.parent_name)
        
        print(f"\nFound {len(nested_structures)} nested structures in the table.")