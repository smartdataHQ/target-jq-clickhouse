import ipaddress
import uuid
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
import simplejson as json
from clickhouse_connect.driver import Client
from dateutil.parser import parse

CH_PYTHON_CONVERTERS = {
    "DateTime": (datetime, parse),
    "Date": (datetime, parse),
    "UUID": uuid.UUID,
    "Int": int,
    "String": str,
    "FixedString": str,
    "UInt": int,
    "Float": float,
    "Bool": bool,
    "Boolean": bool,
    "Point": tuple,
    "Enum": (str, int),
    "Object": json.dumps,
    "IPv4": (ipaddress.IPv4Address, ipaddress.ip_address),
}


def simple_type(data_type) -> str:
    if "DateTime" in data_type:
        return "DateTime"
    elif "Int" in data_type:
        return "Int"
    elif "Float" in data_type:
        return "Float"
    elif "Enum8" in data_type:
        return "Enum"

    return data_type


def find_data_type(data_type: str) -> str:
    if "Map" in data_type:
        key, value = data_type.split(",")
        key = key[key.find("(") + 1 :].strip()
        value = "(" + value.strip()
        check = [simple_type(key), simple_type(value)]
    else:
        check = [simple_type(data_type)]

    data_types = []
    for data_type in check:
        data_type = data_type.strip()
        while "(" in data_type:
            data_type = data_type[data_type.find("(") + 1 : data_type.rfind(")")]
        data_types.append(data_type)

    return ",".join(data_types)


def find_nested_columns(metadata: dict[str, Any]) -> dict:
    nested_columns = {}
    for column, value in metadata.items():
        value["is_nested"] = False
        if "." in column:
            parts = column.split(".")
            field = parts[-1]
            nested = ".".join(parts[:-1])

            if "Array" in value["type"]:
                value["is_nested"] = True
                value["parent"] = nested
                value["field"] = field
                value["basic_type"] = find_data_type(value["type"])
                if nested not in nested_columns:
                    nested_columns[nested] = []
                nested_columns[nested].append(value)
            else:
                if nested in nested_columns:
                    print("Found non nested field in a nested array column")

    return nested_columns


def find_flat_map_columns(metadata: dict[str, Any]) -> dict:
    # find all columns that are part of a flat map and are not nested
    flat_maps = {}
    for column in metadata:
        if "." in column:
            first_part = column.split(".")[0]
            are_same = [
                x
                for x in metadata
                if x.startswith(first_part) and not metadata[x]["is_array"] and x != column
            ]
            if len(are_same) > 0 and first_part not in flat_maps:
                flat_maps[first_part] = are_same + [column]

    return flat_maps


def find_mapped_columns(metadata: dict[str, Any]) -> dict:
    mapped_columns = {}
    for column, value in metadata.items():
        if "Map" in value["type"]:
            value["is_mapped"] = True
            map_typing = value["type"]
            key_type, value_type = map_typing[map_typing.find("(") + 1 : map_typing.rfind(")")].split(", ")
            key_type = find_data_type(key_type)
            value_type = find_data_type(value_type)
            mapped_columns[column] = {
                "key_type": key_type,
                "value_type": value_type,
                "column": column,
                "has_misc_storage": False,
            }

    for mapped_column in mapped_columns:
        parts = mapped_column.split(".")
        if len(parts) > 1 and f"{'.'.join(parts[:-1])}.other" in metadata:
            mapped_columns[mapped_column]["has_misc_storage"] = True

    return mapped_columns


def find_type_mapped_columns(mapped_columns: dict[str, Any], metadata: dict[str, Any]) -> dict:
    type_mapped_raw = {}
    # find all mapped_columns that share the first part of the name and store them in type_mapped_columns
    for mapped_column in mapped_columns:
        parts = mapped_column.split(".")
        if len(parts) > 1:
            if parts[0] not in type_mapped_raw:
                type_mapped_raw[parts[0]] = []
            type_mapped_raw[parts[0]].append(mapped_column)

        overflow_column = f"{parts[0]}.other"
        if overflow_column in metadata and overflow_column not in type_mapped_raw[parts[0]]:
            type_mapped_raw[parts[0]].append(overflow_column)

    type_mapped_columns = {}
    # remove all from the type_mapped_columns that only have one column
    for type_mapped_column in type_mapped_raw:
        if len(type_mapped_raw[type_mapped_column]) > 1:
            type_mapped_columns[type_mapped_column] = type_mapped_raw[type_mapped_column]

    return type_mapped_columns


def fetch_metadata(connection: Client, table: str) -> dict[str, Any]:
    data = connection.query(f"DESCRIBE {table}")
    all = {}
    columns = [column for column in data.column_names]
    for row in data.result_set:
        row_dict = dict(zip(columns, row))
        if row_dict.get("default_type", "") == "ALIAS":
            # we can't insert to ALIAS columns, so ignore them
            continue

        row_dict["is_map"] = "map" in row_dict["type"].lower()
        row_dict["is_req"] = (
                "nullable" not in row_dict["type"].lower() and "array" not in row_dict["type"].lower()
        )
        row_dict["is_array"] = "array(" in row_dict["type"].lower()
        row_dict["basic_type"] = find_data_type(row_dict["type"])
        if row_dict["is_map"]:
            row_dict["converter"] = CH_PYTHON_CONVERTERS.get(row_dict.get("basic_type").split(",")[1], None)
        else:
            row_dict["converter"] = CH_PYTHON_CONVERTERS.get(row_dict.get("basic_type"), None)

        all[row_dict["name"]] = row_dict

    nested = find_nested_columns(all)
    flat_maps = find_flat_map_columns(all)
    mapped = find_mapped_columns(all)
    type_mapped = find_type_mapped_columns(mapped, all)
    return {
        "all": all,
        "nested": nested,
        "mapped": mapped,
        "type_mapped": type_mapped,
        "flat_maps": flat_maps
    }


def remove_all_empty_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    for column in dataframe.columns:
        # find all columns that are completely empty
        if dataframe[column].isnull().all():
            dataframe.drop(column, axis=1, inplace=True)

        # find all columns that only have empty arrays and dicts in them
        elif dataframe[column].apply(lambda x: len(x) if type(x) in [list, dict] else 1).sum() == 0:
            dataframe.drop(column, axis=1, inplace=True)
    return dataframe

def replace_none_where_needed(metadata, dataframe: pd.DataFrame) -> pd.DataFrame:
    null_uuid = uuid.UUID("00000000-0000-0000-0000-000000000000")
    for column in dataframe.columns:
        column_meta = metadata["all"][column]
        if column_meta["is_map"]:
            dataframe[column] = dataframe[column].apply(lambda x: {} if x is None else x)
        elif column_meta["is_array"]:
            if column_meta["basic_type"] == "String":
                dataframe[column] = dataframe[column].apply(
                    lambda x: [y if y else "" for y in x]
                )
            elif column_meta["basic_type"] in ["Float"]:
                dataframe[column] = dataframe[column].apply(
                    lambda x: [y if isinstance(y, float) else np.nan for y in x]
                )
            elif column_meta["basic_type"] in ["UUID"]:
                dataframe[column] = dataframe[column].apply(
                    lambda x: [y if y else null_uuid for y in x]
                )
        else:
            if column_meta["basic_type"] == "String":
                dataframe[column] = dataframe[column].apply(lambda x: x if x else "")
            elif column_meta["basic_type"] in ["Float", "Int"]:
                dataframe[column] = dataframe[column].fillna(0)
            elif column_meta["basic_type"] in ["UUID"]:
                dataframe[column] = dataframe[column].apply(lambda x: x if x else null_uuid)
    return dataframe


def flatten_nested_fields(client, items):
    metadata = fetch_metadata(client, "dev.semantic_events_dev")
    nested = metadata["nested"]

    for item in items:
        for nested_field_name, components in nested.items():
            # only process if item has this nested field and it's a list
            if not isinstance(item.get(nested_field_name), list):
                continue

            nested_field_values = item[nested_field_name]
            for component in components:
                value_array = []
                item[component["name"]] = value_array
                for nested_field_value in nested_field_values:
                    value_array.append(
                        nested_field_value.get(component["field"])
                        if nested_field_value and "field" in component
                        else None
                    )

            del item[nested_field_name]

    return metadata, items