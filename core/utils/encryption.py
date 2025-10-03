import logging
import os
import dotenv
import io
import base64
import json
import zipfile

from cryptography.fernet import Fernet
from functools import reduce

dotenv.load_dotenv()
FERNET_KEY_PATTERN = os.getenv("FERNET_KEY_PATTERN")

def calculate_fernet(organization_id: str):
    flist = FERNET_KEY_PATTERN.split(",")
    fstring = ""
    for f in flist:
        fstring += organization_id[int(f)]
    return base64.urlsafe_b64encode(fstring.encode())

def fetch_encrypted_content(event: dict, config: dict):
    try:
        content_to_encrypt = {}
        field_name = config.get('name', 'encrypted_content')
        for source_field in config.get("fields", []):
            value = reduce(lambda a, b: a.get(b), source_field.split("."), event)
            content_to_encrypt[source_field] = value

        mem_zip = io.BytesIO()
        fernet_key = Fernet(calculate_fernet(config.get("encoding_key")))
        with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            encrypted_value = fernet_key.encrypt(json.dumps(content_to_encrypt).encode())
            zf.writestr("transcript.json", encrypted_value.decode())
        some = io.BytesIO()
        mem_zip.seek(0)
        base64.encode(mem_zip, some)
        some.seek(0)
        return field_name, some.getvalue()
    except Exception as e:
        logging.error(f"Error fetching encrypted content: {str(e)}")
        return None, None
