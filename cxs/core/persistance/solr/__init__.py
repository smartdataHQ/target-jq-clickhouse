import logging
import os

import dotenv
import pysolr

dotenv.load_dotenv()
logger = logging.getLogger(__name__)

SOLR_HOST = os.getenv("SOLR_HOST")
SOLR_CORE = os.getenv("SOLR_CORE")
ENVIRONMENT = os.getenv("ENVIRONMENT")

solr_connection: pysolr.Solr | None
try:
    if not SOLR_HOST or ENVIRONMENT in ["onprem"]:
        solr_connection = None
    else:
        solr_connection = pysolr.Solr(SOLR_HOST + "/" + SOLR_CORE, always_commit=True)
except Exception as e:
    solr_connection = None
    logger.error(f"Error connecting to Solr: {str(e)}")
