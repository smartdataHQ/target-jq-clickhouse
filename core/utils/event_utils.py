import copy
import enum
import hashlib
import os
import re
import uuid
import json

from copy import deepcopy
from datetime import datetime
from functools import reduce
from deepmerge import Merger
import dotenv
from pydantic import BaseModel
from markdownify import markdownify as md

dotenv.load_dotenv()

def unique_dicts_across_lists(config, path, base, *next):
    next_list = []
    for li in next:
        next_list.extend(li)
    merged_list = [json.dumps(lst, sort_keys=True) for lst in base + next_list]
    unique_dicts = set(merged_list)
    return [json.loads(s) for s in unique_dicts]


merger = Merger(
    [
        (list, unique_dicts_across_lists),
        (dict, ["merge"]),
        (set, ["union"])
    ],
    ["override"],
    ["override"]
)


def normalize_event(event: dict):

    if not event:
        return {}

    if not event.get("type") and not event.get("event"):
        return event

    # Add default values to the event
    normalized_event = copy.deepcopy(event)
    if not "timestamp" in normalized_event or not normalized_event["timestamp"]:
        normalized_event["timestamp"] = datetime.now().isoformat()

    # elevate fields from proeprties
    elevate = ["involves", "content", "classification", "flags", "dimensions", "analysis"]
    for field in elevate:
        if "properties" in normalized_event and field in normalized_event["properties"]:
            normalized_event[field] = normalized_event["properties"][field]
            del normalized_event["properties"][field]

    if "_process" in normalized_event:
        normalized_event["underscore_process"] = normalized_event["_process"]
        del normalized_event["_process"]

    if (event.get("event_gid") is None or str(event.get("event_gid")) == "00000000-0000-0000-0000-000000000000"):
        normalized_event["event_gid"] = calculate_event_id(event)

    return normalized_event


def calculate_event_id(event: dict):

    all_ids = [
        involved.get("id") or involved.get("entity_gid") for involved in event.get("involves", [])
    ]
    all_ids.sort()
    ids = "--".join(all_ids)
    if event.get("partition"):
        event_gid_url = f"https://{event.get('partition')}/event/{event.get('type')}/{event.get('event').replace(' ', '-').lower()}/{ids}/{event.get('timestamp')}"
    elif event.get("event"):
        event_gid_url = f"https://contextsuite.com/event/{event.get('type')}/{event.get('event').replace(' ', '-').lower()}/{ids}/{event.get('timestamp')}"
    else:
        event_gid_url = str(uuid.uuid4())

    return str(uuid.uuid5(uuid.NAMESPACE_DNS, event_gid_url.lower()))


def get_source_fields(item: BaseModel, config, default_source_fields=None, **kwargs):

    source_fields = config.get("source_fields", default_source_fields)
    user_content = [] # todo - why is this returning a list?

    event_dict = item if isinstance(item, dict) else item.model_dump()
    if source_fields:
        for field in source_fields:
            # filter out fields that do not match the kwargs settings
            filter_field = False
            for key in kwargs:
                if key in source_fields[field]:  # matches a settings value we need to make sure that they are the same
                    if source_fields[field][key] != kwargs[key]:
                        filter_field = True
                        break
            if filter_field:
                continue

            if ".*" in field:
                # todo - this is a stupid way to do this
                event_data = item.dict().get(field.split(".*")[0])
                for prop in item.dict().get(field.split(".*")[0]):
                    if field == "content.*":
                        user_content.append({"content": prop.get("value")})
                    elif field == "dimensions.*":
                        user_content.append({"content": f"{prop}: {event_data[prop]}"})
                    elif field == "classification.*":
                        user_content.append({"content": f"{prop.get('type')}: {prop.get('value')}"})
            else:
                settings = source_fields[field] if isinstance(source_fields, dict) else field
                try:
                    value = reduce(lambda a, b: a.get(b) if isinstance(a, dict) else getattr(a, b), field.split("."), event_dict)
                except Exception as e:
                    # property not found
                    print(e)
                    continue

                if isinstance(settings, str):
                    user_content.append({settings: value})
                    continue

                value_type = settings.get("type", "str")

                if value:
                    if value_type in ["str","text"] or isinstance(settings,dict) and value_type == "email_body":
                        if isinstance(settings,dict) and value_type == "email_body":
                            if settings.get('clean'):
                                value = md(value)
                                value = re.sub(r'\xa0+', ' ', value)
                                value = value.replace('\xc2', ' ')
                                value = value.replace('\0', '')
                                value = value.replace('\n\n', '\n')
                                value = value.replace('\t', '')
                                value = value.replace('\xad', '')
                                value = value.replace('\_', '')
                                value = value.replace('| |', ' ')
                                value = re.sub(r"\s+", ' ', value, flags=re.UNICODE)

                        if settings.get('extract'):
                            for extract, regex in settings.get("extract", {}).items():
                                res = re.compile(regex).search(value)
                                if res and res.group(1):
                                    if not event_dict.get('underscore_process'):
                                        event_dict['underscore_process'] = {}
                                    event_dict['underscore_process'][extract] = res.group(1) if res else None
                        if settings.get('start_after') and settings.get('start_after') in value:
                            if 'start_after_condition' not in settings or event_dict.get('underscore_process',{}).get(settings.get('start_after_condition','_none')):
                                pos_of_string = value.find(settings['start_after']) + len(settings['start_after'])
                                value = value[pos_of_string:]
                        if 'stop_before' in settings:
                            if 'stop_before_condition' not in settings or event_dict.get('underscore_process', {}).get(settings.get('stop_before_condition','_none')):
                                terminators = settings.get('stop_before', [])
                                if isinstance(terminators, str):
                                    terminators = [terminators]
                                for terminator in terminators:
                                    pos_of_string = value.find(terminator)
                                    if pos_of_string < 0: # try regex
                                        try:
                                            pos_of_string = re.compile(terminator).search(value).start()
                                        except Exception:
                                            pass # not a regex or not found
                                    if pos_of_string != -1:
                                        value = value[:pos_of_string]

                        property = event_dict
                        parts = field.split(".")
                        for part in parts[0:-1]:
                            property = property.get(part)
                        property[parts[-1]] = value

                        if 'label' in settings:
                            value = settings["label"] + ': ' + value

                        user_content.append({settings.get("target", "content"): value})
                        continue

                    if value_type == "transcript":
                        user_content.append(
                            {
                                settings.get("target", "content"): "\n".join(
                                    [f"{com['speaker']}: {com['text']}" for com in value]
                                )
                            }
                        )
                    elif value_type == "email":
                        user_content.append({settings.get("target", "content"): f"{str(value)}"})
                    elif value_type == "involves":
                        user_content.append({settings.get("target", "content"): f"Involves: {json.dumps(value)}"})
                    elif value_type == "assumed_time":
                        user_content.append({settings.get("target", "content"): f"Assume this happens at: {str(value)}"})
                    elif value_type == "voice_url":
                        if isinstance(value, list):
                            user_content = user_content + value
                        else:
                            user_content.append({settings.get("target", "content"): f"Recording URL: {str(value)}"})
                    else:
                        user_content.append({settings.get("target", "content"): f"{value_type}: {value}"})

    else:
        user_content = [{"content": item.content[content]} for content in item.content]

    return user_content


def log_version(
    event: dict, config: dict, channel: str, service: str, write_key: str, step: str, merge: bool
):
    DEVELOPER = os.getenv("DEVELOPER", "Unknown")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "Unknown")

    log_event = {
        "timestamp": datetime.now().isoformat(),
        "entity_gid": uuid.UUID(config.get("account",{}).get('id')),
        "type": event["type"],
        "event": event["event"],
        "event_gid": event["event_gid"],
        "analysis": event["analysis"],
        "dimensions": {
            "partition": event.get("partition"),
            "channel": channel,
            "service": service,
            "write_key": write_key,
            "step": step,
            "environment": ENVIRONMENT,
        },
        "involves": [
            {
                "role": "Customer",
                "label": config.get("account",{}).get('name'),
                "entity_type": "Account",
                "entity_gid": config.get("account",{}).get('id'),
                "id": DEVELOPER
            }
        ],
        "flags": {"merge": merge},
        "partition": "contextsuite.com",
    }
    if "services" in config and config["services"]:
        if "involves" not in log_event:
            log_event["involves"] = []

        service_list: list[str] = (
            [a.get("provider", "") + "--" + a.get("variant", "") for a in log_event["analysis"]]
            if "analysis" in log_event
            else []
        )

        for service_key in config["services"]:
            service = config["services"][service_key]
            if service.get("provider", "") + "--" + service.get("model", "") in service_list:
                log_event["involves"].append(
                    {
                        "role": service_key,
                        "label": (
                            service["provider"] + " (" + service["model"] + ")"
                            if "provider" in service and "model" in service
                            else service["provider"]
                        ),
                        "id_type": "api_key" if "api_key" in service else "",
                        "id": (
                            str(hashlib.md5(service["api_key"].encode()).hexdigest())
                            if "api_key" in service
                            else ""
                        ),
                    }
                )
    if DEVELOPER:
        if "involves" not in log_event:
            log_event["involves"] = []
        log_event["involves"].append(
            {"role": "Developer", "label": DEVELOPER, "id_type": "email", "id": DEVELOPER}
        )

    if "logging" in config and config["logging"]:
        log_event = augment_event(log_event, config["logging"])
    return log_event


def save_version(event: dict, config: dict):
    if "persist" in config and config["persist"]:
        event = augment_event(event, config["persist"])
    if "_process" in event:
        del event["_process"]
    return event


def augment_event(event: dict, config: dict):
    if "reassign" in config and config["reassign"]:
        for field in config["reassign"]:
            field_name = list(field.keys())[0]
            if field_name not in event:
                continue
            reassign_config = field[field_name]
            value = reduce(lambda a, b: a.get(b), field_name.split("."), event)
            if "reg_extract" in reassign_config and reassign_config["reg_extract"]:
                results = re.search(str(reassign_config["reg_extract"]), str(value), re.IGNORECASE)
                if results:
                    value = results[0]

            target = reassign_config["target"]
            target_field = reassign_config.get("name", field_name)
            if target == "classification":
                if not "classification" in event:
                    event["classification"] = []
                event["classification"].append({"type": target_field, "value": value})
            elif target == "content":
                if not "content" in event:
                    event["content"] = {}
                event["content"][target_field] = value
            elif target == "dimensions":
                if not "dimensions" in event:
                    event["dimensions"] = {}
                event["dimensions"][target_field] = value

    if "overwrite" in config:
        overwrite = deepcopy(config["overwrite"])
        for field in overwrite:
            if overwrite[field] == "$timestamp":
                overwrite[field] = datetime.now().isoformat()
        event = {**event, **overwrite}

    if "ignore" in config:
        for field in config["ignore"]:
            if "." in field:
                nested_fields = field.split(".")
                nested_field = event
                for nested in nested_fields[:-1]:
                    nested_field = nested_field.get(nested, {})
                if nested_fields[-1] in nested_field:
                    del nested_field[nested_fields[-1]]
            elif field in event:
                del event[field]
    return event


def merge_documents(
    event: dict, outcome: dict, config: dict, cost: list[dict] = None, overwrite_cost: bool = False
):
    schema_fields = config.get("schema_fields")
    if not schema_fields:
        event = merger.merge(event, outcome)
    else:
        for field_name in outcome:
            field_value = outcome[field_name]
            if field_name in schema_fields and field_value is not None:
                field_settings = schema_fields[field_name]
                remark_indicator = None
                if "remark_indicator" in field_settings and field_settings.get("remark_indicator"):
                    remark_indicator = field_settings.get("remark_indicator")

                if "target" in field_settings:
                    target_field = field_settings["target"]
                    if not target_field:
                        continue
                    if isinstance(target_field, list):
                        sep = field_settings.get("target_separator", ";")
                        if not "classification" in event:
                            event["classification"] = []
                        for a_value in field_value:
                            if a_value is None or a_value.value is None:
                                continue
                            split_values = a_value.value.split(sep)
                            for i, target in enumerate(target_field):
                                f_value = split_values[i].strip() if i < len(split_values) else None
                                if remark_indicator and remark_indicator in f_value:
                                    f_value = f_value.split(remark_indicator)[0].strip()
                                event["classification"].append(
                                    {
                                        "type": target,
                                        "value": f_value,
                                    }
                                )  # todo - support other target types
                    elif target_field == "classification":
                        if not "classification" in event:
                            event["classification"] = []
                        if not isinstance(field_value, list):
                            field_value = [field_value]
                        for classification in field_value:
                            classification_value = classification if isinstance(classification, str) else classification.value if isinstance(classification, enum.Enum) else None
                            if remark_indicator and remark_indicator in classification_value:
                                if isinstance(target_field, list):
                                    event["classification"].append(
                                        {
                                            "type": field_name,
                                            "value": classification_value.split(remark_indicator)[0].strip(),
                                        }
                                    )
                                else:
                                    event["classification"].append(
                                        {
                                            "type": field_name,
                                            "value": classification_value.split(remark_indicator)[0].strip(),
                                        }
                                    )
                            else:
                                event["classification"].append(
                                    {"type": field_name, "value": classification_value}
                                )
                    elif target_field == "content":
                        if not "content" in event:
                            event["content"] = {}
                        event["content"][field_name] = field_value
                    elif target_field == "dimensions":
                        if not "dimensions" in event:
                            event["dimensions"] = {}
                        if isinstance(field_value, enum.Enum):
                            field_value = field_value.value
                        if remark_indicator and remark_indicator in field_value:
                            event["dimensions"][field_name] = field_value.split(remark_indicator)[0].strip()
                        else:
                            event["dimensions"][field_name] = field_value
                    elif target_field == "flags":
                        if not "flags" in event:
                            event["flags"] = {}
                        event["flags"][field_name] = field_value
                    elif target_field == "_process":
                        if not "underscore_process" in event:
                            event["underscore_process"] = {}
                        event["underscore_process"][field_name] = field_value
                    elif target_field == "customer_intent":
                        if not "classification" in event:
                            event["classification"] = []
                        for intent_entry in field_value:
                            intent = intent_entry.value
                            if "  " in intent:
                                intent, intent_category = intent.split("  ")
                                event["classification"].append({"intent_category": intent_category})
                            event["classification"].append({"intent": intent})
                    elif target_field == "sentiment":
                        if not "sentiment" in event or not event["sentiment"]:
                            event["sentiment"] = []
                        for sentiment in field_value:
                            event["sentiment"].append(sentiment)
                    elif target_field == "metrics":
                        if not "metrics" in event or not event["metrics"]:
                            event["metrics"] = {}
                        event["metrics"][field_name] = (
                            float(field_value) if type(field_value) == "str" else field_value
                        )
                    else:
                        event[target_field] = field_value

    if overwrite_cost and "analysis" not in event:
        event["analysis"] = []

    if cost is not None:
        if "analysis" not in event or not event["analysis"]:
            event["analysis"] = []

        for cost_item in cost:
            if isinstance(cost_item, list):
                for item in cost_item:
                    event["analysis"].append(item)
            else:
                event["analysis"].append(cost_item)

    if "underscore_process" in event:
        event["_process"] = event["underscore_process"]
        del event["underscore_process"]

    return event
