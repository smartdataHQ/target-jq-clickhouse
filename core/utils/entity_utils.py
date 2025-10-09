import os
import dotenv
import pandas as pd

dotenv.load_dotenv()
FERNET_KEY_PATTERN = os.getenv("FERNET_KEY_PATTERN")


def entities_as_df(entities):
    # todo - performance optimization - batch insert

    entities_df = pd.DataFrame([s.model_dump(round_trip=True) for s in entities])
    if "classification" in entities_df.columns:
        entities_df = entities_df.join(pd.json_normalize(entities_df["classification"])).drop(
            columns=["classification"]
        )
    if "ids" in entities_df.columns:
        entities_df = entities_df.join(pd.json_normalize(entities_df["ids"])).drop(columns=["ids"])
    if "embeddings" in entities_df.columns:
        entities_df = entities_df.join(pd.json_normalize(entities_df["embeddings"])).drop(
            columns=["embeddings"]
        )
    if "media" in entities_df.columns:
        entities_df = entities_df.join(pd.json_normalize(entities_df["media"])).drop(
            columns=["media"]
        )
    if "content" in entities_df.columns:
        entities_df = entities_df.join(pd.json_normalize(entities_df["content"])).drop(
            columns=["content"]
        )
    if "location" in entities_df.columns:
        entities_df = entities_df.join(pd.json_normalize(entities_df["location"])).drop(
            columns=["location"]
        )

    return entities_df
