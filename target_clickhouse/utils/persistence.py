import clickhouse_connect

def get_clickhouse_connection(host: str, port: int, username: str, password: str, database: str):
    return clickhouse_connect.get_client(
        host=host,
        port=port,
        username=username,
        password=password,
        verify=False,
        database=database,
        connect_timeout=9999,
        settings={
            "connect_timeout": 9999,
            "send_timeout": 9999,
            "distributed_ddl_task_timeout": 9999,
            "max_partitions_per_insert_block": 10_000,
        },
        send_receive_timeout=9999
    )