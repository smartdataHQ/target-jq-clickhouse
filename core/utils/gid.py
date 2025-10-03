import uuid
import re

def normalize_gid_url(gid_url):
    normalized_gid_url: str = gid_url
    if normalized_gid_url.endswith('/'):
        normalized_gid_url = normalized_gid_url[:-1]
    normalized_gid_url = re.sub(r"^http://", "https://", normalized_gid_url, flags=re.IGNORECASE)
    return normalized_gid_url

def create_gid(gid_url, normalize=False):
    if normalize:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, normalize_gid_url(gid_url).lower()))
    else:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, gid_url.lower()))
