import pandas as df
import pandas as pd

from cxs.core.schema.entity import EntityCH
from cxs.core.schema.timeseries import TimeSeries, TimeSeriesCH, DefinedMetric
from cxs.core.utils.persist import save_to_ch, save_df_to_clickhouse

db_clients = {}
try:
    from cxs.core.persistance.clickhouse import ch_async_client
    db_clients["async_clickhouse"] = ch_async_client
except Exception as e:
    print(f"Error connecting to ClickHouse: {str(e)}")

async def save_timeseries_to_ch(timeserie: TimeSeries):

    # Save all entities
    all_entities = timeserie.entities
    for entity in [timeserie.owner, timeserie.source, timeserie.publisher, timeserie.publication]:
        if entity:
            all_entities.append(entity)

    all_entities = [EntityCH(**entity.model_dump()) for entity in all_entities] # Convert to ClickHouse Entity
    # todo - aremove redundant entities based on gid
    print(f"Saving {len(all_entities)} entities in ClickHouse")
    await save_entities_to_ch(all_entities, db_clients)

    # create a dataframe for all the entities so we can join them together
    df_entities = df.DataFrame([s.model_dump() for s in all_entities])
    df_entities.rename(columns={'gid': 'entity_gid', 'gid_url': 'entity_gid_url', }, inplace=True)
    # convert 'entity_gid' into a string
    df_entities = df_entities[['entity_gid', 'entity_gid_url', 'dimensions', 'location','properties']]
    df_entities.entity_gid = df_entities.entity_gid.astype(str)
    df_entities.set_index('entity_gid', inplace=True) # so we can join on it later

    # create the datapoints dataframe
    df_data_points = df.DataFrame([s.model_dump() for s in timeserie.datapoints]) # todo - performance optimization - batch insert without going back an forth with pydantic
    if 'entity' in df_data_points.columns:
        df_data_points = df_data_points.drop(columns='entity')

    df_data_points.entity_gid = df_data_points.entity_gid.astype(str)
    df_data_points = df_data_points.join(df_entities, on='entity_gid', rsuffix='_entity', how='left')

    df_data_points.measured_by_gid = df_data_points.measured_by_gid.astype(str)
    df_data_points = pd.merge(df_data_points, df_entities, left_on='measured_by_gid', right_on='entity_gid', how='left', suffixes=('','_measured_by_entity'))

    # combine the dimensions and dimensions_entity dict into one dict
    df_data_points['dimensions'] = df_data_points.apply(lambda x: {**x.get('dimensions_measured_by_entity',{}), **x.get('dimensions_entity',{}), **x.get('dimensions',{})}, axis=1)
    # this is hazardous - we are assuming that the location_entity is a dict with only one key and these should no
    # df_data_points['location'] = df_data_points.apply(lambda x: {**{k: v[0] if len(v) > 0 else None for k, v in x.get('location_entity',{}).items()}, **x.get('location',{})}, axis=1)
    df_data_points['location'] = df_data_points.apply(lambda x: {k.replace('location.',''): str(v[0]) if len(v) > 0 else '' for k, v in x.get('location_entity',{}).items()} if not x.get('location') else x.get('location'), axis=1)
    # todo - should we inherit from both?
    df_data_points['location'] = df_data_points.apply(lambda x: {k.replace('location.',''): str(v[0]) if len(v) > 0 else '' for k, v in x.get('location_measured_by_entity',{}).items()} if not x.get('location') else x.get('location'), axis=1)

    df_data_points['geohash_head'] = df_data_points.apply(lambda x: x.get('location',{}).get('geohash', '')[:5], axis=1)
    df_data_points['geohash_tail'] = df_data_points.apply(lambda x: x.get('location',{}).get('geohash', '')[5:], axis=1)

    # move designated properties to datapoint metadata - this is slower
    for transfer_property in ['device.', 'demography.', 'classification.', 'topology.', 'usage.', 'product.',]:
        df_data_points[transfer_property[:-1]] = df_data_points.apply(lambda x: {k[len(transfer_property):]: str(v) for k, v in x.get('properties',{}).items() if k.startswith(transfer_property)}, axis=1)
        # todo - should we inherit from both?
        df_data_points[transfer_property[:-1]] = df_data_points.apply(lambda x: {k[len(transfer_property):]: str(v) for k, v in x.get('properties_measured_by_entity',{}).items() if k.startswith(transfer_property)}, axis=1)

    # drop the entity_gid and dimensions_entity columns
    df_data_points = df_data_points.drop(columns=['dimensions_entity', 'location_entity', 'properties', 'dimensions_measured_by_entity', 'location_measured_by_entity', 'properties_measured_by_entity','entity_gid_url_entity','entity_gid_url_measured_by_entity'])

    # assign things from the series to the datapoints
    df_data_points['series_gid'] = timeserie.gid
    df_data_points['period'] = timeserie.resolution.name
    df_data_points['owner_gid'] = timeserie.owner.gid if timeserie.owner else None
    df_data_points['publisher_gid'] = timeserie.publisher.gid if timeserie.publisher else None
    df_data_points['source_gid'] = timeserie.source.gid if timeserie.source else None
    df_data_points['country'] = timeserie.country

    await save_datapoints_ch(df_data_points, db_clients)

    # todo - save timeserie
    ts_basics = timeserie.model_copy()
    ts_basics.datapoints = []
    ts_basics.entities = []
    timeseries_ch = TimeSeriesCH(**ts_basics.model_dump())
    await save_entities_to_ch([timeseries_ch], db_clients, 'ql.timeseries')

    # todo - save metrics
    await save_entities_to_ch(list(timeserie.metrics.values()), db_clients, 'ql.metrics')
    pass

async def save_datapoints_ch(df_data_points: pd.DataFrame, db_clients, table: str = 'ql.data_points'):
    return await save_df_to_clickhouse(table, df_data_points, db_clients, None)

async def save_entities_to_ch(entities: [EntityCH|TimeSeriesCH|DefinedMetric], db_clients, table: str = 'ql.entities'):
    return await save_to_ch(entities, table, db_clients, None)
