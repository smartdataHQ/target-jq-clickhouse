import json
import logging
from typing import Sequence

import dotenv
import pandas as pd
from clickhouse_connect.driver import AsyncClient

from cxs.core.schema.entity import EntityCH
from cxs.core.schema.semantic_event import SemanticEvent, SemanticEventCH
from cxs.core.schema.timeseries import DefinedMetric, TimeSeriesCH

dotenv.load_dotenv()


def timeseries_as_df(timeseries):
    ent_df = pd.DataFrame([s.model_dump() for s in timeseries])
    ent_df = ent_df.join(pd.json_normalize(ent_df["metrics"], record_prefix="metrics")).drop(
        columns=["metrics"]
    )
    ent_df["owner"] = ent_df["owner"].apply(lambda x: str(x.get("gid") if x else None))
    ent_df["source"] = ent_df["source"].apply(lambda x: str(x.get("gid") if x else None))
    ent_df["publisher"] = ent_df["publisher"].apply(lambda x: str(x.get("gid") if x else None))
    ent_df["publication"] = ent_df["publication"].apply(lambda x: str(x.get("gid") if x else None))
    return ent_df


def entities_as_df(entities):
    normalize_fields = [
        "classification",
        "content",
        "involves",
        "analysis",
        "embeddings",
        "ids",
        "location",
        "media",
    ]
    ent_df = pd.DataFrame([s.model_dump() for s in entities])
    for field in normalize_fields:
        if field in ent_df.columns:
            ent_df = ent_df.join(pd.json_normalize(ent_df[field])).drop(columns=[field])
    return ent_df


def events_as_df(semantic_events):
    # todo - performance optimization - batch insert
    normalize_fields = ["classification", "sentiment", "involves", "analysis"]
    events_df = pd.DataFrame([s.model_dump(round_trip=True) for s in semantic_events])
    for field in normalize_fields:
        if field in events_df.columns:
            events_df = events_df.join(pd.json_normalize(events_df[field])).drop(columns=[field])
    return events_df


async def get_from_ch(timestamp: str, event_gid: str, partitions: [str], db_clients: dict):
    async_clickhouse: AsyncClient = db_clients["async_clickhouse"]
    partitions_str = "['" + "','".join(partitions) + "']"
    query = (
        f"SELECT * FROM cst.semantic_events WHERE event_gid = '{event_gid}' AND partition IN {partitions_str}"
    )
    if timestamp:
        query += f" AND timestamp = '{timestamp.replace('T', ' ')}'"
    results = await async_clickhouse.query(query)
    events = []
    for row in results.named_results():
        events.append(SemanticEvent(**row))

    return events[0] if len(events) == 1 else events


async def save_to_ch(
    records: Sequence[SemanticEventCH | EntityCH | TimeSeriesCH | DefinedMetric],
    table: str,
    db_clients: dict,
    logger,
):
    try:
        blacklisted_columns = []
        serialized_columns = []
        rename_columns = {}
        if isinstance(records[0], SemanticEventCH):
            se_df = events_as_df(records)
            blacklisted_columns = ["underscore_process", "source"]
            rename_columns = {"messageId": "message_id"}
        elif isinstance(records[0], EntityCH):
            serialized_columns = ["properties"]
            se_df = entities_as_df(records)
        elif isinstance(records[0], TimeSeriesCH):
            blacklisted_columns = ["datapoints", "entities", "series_type", "country"]
            rename_columns = {
                "owner": "owner_gid",
                "source": "source_gid",
                "publisher": "publisher_gid",
                "publication": "publication_gid",
            }
            se_df = timeseries_as_df(records)
        elif isinstance(records[0], DefinedMetric):
            se_df = pd.DataFrame([s.model_dump() for s in records])
            se_df["uom"] = se_df["uom"].apply(lambda x: x.name if x else None)
            se_df["adj_type"] = se_df["adj_type"].apply(lambda x: x.name if x else None)
        else:
            raise Exception("Unknown record type")

        for remove_column in blacklisted_columns:
            if remove_column in se_df.columns:
                se_df = se_df.drop(columns=remove_column)

        # serialize the value of each property in the dict-column
        for column in serialized_columns:
            if column in se_df.columns:
                se_df[column] = se_df[column].apply(
                    lambda x: {
                        key: (
                            json.dumps(value)
                            if isinstance(value, dict) or isinstance(value, list)
                            else str(value)
                        )
                        for key, value in x.items()
                    }
                )

        for old_name, new_name in rename_columns.items():
            if old_name in se_df.columns:
                se_df = se_df.rename(columns={old_name: new_name})

        return await save_df_to_clickhouse(
            table=table,
            data_frame=se_df,
            db_clients=db_clients,
            logger=logger,
        )
    except Exception as e:
        if logger:
            logger.error(f"Error Saving to Clickhouse: {str(e)}")
        else:
            print(f"Error Saving to Clickhouse: {str(e)}")

        raise e


async def save_df_to_clickhouse(
    table: str,
    data_frame: pd.DataFrame,
    db_clients: dict,
    logger: logging.Logger | None,
):
    res = None
    if not data_frame.empty and "async_clickhouse" in db_clients:
        # check if the database connection needs to be awaited
        async_clickhouse: AsyncClient = db_clients.get("async_clickhouse")
        if not isinstance(db_clients["async_clickhouse"], AsyncClient):
            async_clickhouse = await db_clients.get("async_clickhouse")
            db_clients["async_clickhouse"] = async_clickhouse

        res = await async_clickhouse.insert_df(table, data_frame)
        if logger:
            logger.info(
                "Async inserted %s of %s records into '%s' in %.3f seconds (0 inserts is expected when using async_clickhouse (Nothing inserted yet))",
                res.written_rows,
                len(data_frame),
                table,
                int(res.summary.get("elapsed_ns")) / 1e9,
            )
        else:
            print(
                f"Async inserted {res.written_rows} of {len(data_frame)} records into '{table}' in {int(res.summary.get('elapsed_ns'))/1e+9} seconds (0 inserts is expected when using async_clickhouse (Nothing inserted yet))"
            )

    else:
        # log to file if database is not available
        data_frame.to_csv(f"{table}.csv", mode="a", header=False, index=False)
        if logger:
            logger.error("Database not available. Logging to file.")
        # todo - send this to kafka
    return res
