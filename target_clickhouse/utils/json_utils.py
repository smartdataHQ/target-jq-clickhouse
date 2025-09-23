import simplejson as json

def json_serialize(df_json: str):
    """
    Fix df.to_json(orient='records') output:
    - Convert Python-style literals (None/False/True) to proper JSON
    - Recursively parse nested JSON strings
    - Return a valid JSON string ready for jq
    """
    # Replace Python-style literals
    df_json = df_json.replace('None', 'null').replace('False', 'false').replace('True', 'true')

    # Load JSON
    records = json.loads(df_json)

    # Recursively parse any nested JSON strings
    def parse_nested(value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        elif isinstance(value, list):
            return [parse_nested(v) for v in value]
        elif isinstance(value, dict):
            return {k: parse_nested(v) for k, v in value.items()}
        return value

    # Convert back to JSON string
    return json.dumps([parse_nested(record) for record in records])