import enum
import random
from inspect import isclass

from typing import *
from typing_extensions import Literal
from pydantic import Field, create_model
from pydantic.fields import FieldInfo
from unidecode import unidecode
from pydantic import BaseModel
from jinja2 import Template

"""
class CustomerIntent(BaseModel):
    customer_intent: IntentOption = Field(description="Identify the reason for first contact")
"""


class ExtendableBaseModel(BaseModel):

    @classmethod
    def create_new_type(cls, name: str, fields: dict, type_identifier: str) -> Type[BaseModel]:
        fields.update({"type": (str, type_identifier)})
        new_type = create_model(name, __base__=cls, **fields)
        new_type.TYPE = type_identifier
        return new_type

    @classmethod
    def add_fields(cls, **field_definitions: Any):
        new_fields: Dict[str, FieldInfo] = {}
        new_annotations: Dict[str, Optional[type]] = {}

        for f_name, f_def in field_definitions.items():
            if isinstance(f_def, tuple):
                try:
                    f_annotation, f_value = f_def
                except ValueError as e:
                    raise Exception(
                        "field definitions should either be a tuple of (<type>, <default>) or just a "
                        "default value, unfortunately this means tuples as "
                        "default values are not allowed"
                    ) from e
            else:
                f_annotation, f_value = None, f_def

            if f_annotation:
                new_annotations[f_name] = f_annotation

            new_fields[f_name] = FieldInfo(annotation=f_annotation)

        cls.model_fields.update(new_fields)
        cls.model_rebuild(force=True)

class AnalysisModel(BaseModel):
    label: str = Field(..., description="Anonymized label to use for this entry")


def create_model_from_form(form_metadata: dict, base_model: Type[BaseModel] = ExtendableBaseModel):
    user_custom_fields = {}

    for field in form_metadata["inputs"]:
        field_name = str(unidecode(field.get("name", "field"))).replace(" ", "_")
        field_type = field.get("type", "str")
        field_description = field.get("description", "")
        options = field.get("values")
        is_list = field.get("list", field.get('is_list', False))

        data_type = Optional[str]
        if field_type == "submit":
            continue
        elif field_type == "select" and len(options) > 0:
            _enum_options = enum.Enum(
                field_name.replace("_", " ").title().replace(" ", "") + "Enum",
                {str(unidecode(v["value"])).lower().replace(" ", "_"): v["label"] for v in options},
            )
            data_type = list[_enum_options] if is_list else _enum_options
        elif field_type == "choices":
            _enum_options = enum.Enum(
                field_name.replace("_", " ").title().replace(" ", "") + "Enum",
                {str(unidecode(v)).lower().replace(" ", "_"): v for v in options},
            )
            data_type = list[_enum_options] if is_list else _enum_options
        elif field_type == "choices2":
            data_type = Optional[list[Literal[options]]]
        elif field_type == "int":
            data_type = Optional[int]
        elif field_type == "checkbox":
            data_type = bool if is_list else bool
        elif field_type == "radio":
            data_type = enum.Enum(
                field_name.replace("_", " ").title().replace(" ", "") + "Enum",
                {str(unidecode(v)).lower().replace(" ", "_"): v for v in options},
            )
        elif field_type == "hidden":
            pass
        else:
            data_type = str

        if field.get('required', False):
            user_custom_fields[field_name] = (data_type, Field(description=field_description, default=...))
        else:
            user_custom_fields[field_name] = (Optional[data_type], Field(description=field_description, default=None))


    CustomModel = create_model(
        "search_form",
        __base__=base_model,
        **user_custom_fields,
    )
    return CustomModel

# todo - Find a way to cache the customized outcome of this field
def create_model_from_config(name: str, schema: dict, semantic_event: dict = None) :
    user_custom_fields = {}

    for key in schema["schema_fields"]:
        field = schema["schema_fields"][key]

        ignore = field.get("ignore", False)
        if ignore:
            continue

        field_name = str(unidecode(field.get("name", key))).replace(" ", "_")
        field_type = field.get("type", "str")
        field_description = field.get("prompt", "")
        options = field.get("options")
        ignore_options = field.get("ignore_options")
        class_name = field.get("class")
        is_list = field.get("list", False)

        data_type = str
        if options and not ignore_options:
            _enum_options = enum.Enum(
                field_name.replace("_", " ").title().replace(" ", "") + "Enum",
                {str(unidecode(v)).lower().replace(" ", "_"): str(v).replace('"',"'") for v in options},
            )
            data_type = list[_enum_options] if is_list else _enum_options
        elif class_name:
            custom_class = None
            if class_name == "CustomerIntent":
                custom_class = build_customer_intent_model(field)
            elif class_name == "EntitySentiment":
                custom_class = build_entity_sentiment_model(field)

            if not custom_class:
                raise Exception("Custom class not found or not supported")
            data_type = list[custom_class] if is_list else custom_class
        elif field_type == "str" and is_list:
            data_type = list[str]
        elif field_type == "int":
            data_type = list[str] if is_list else int
        elif field_type == "float":
            data_type = list[str] if is_list else float
        elif field_type == "boolean":
            data_type = list[bool] if is_list else bool

        if '{{' in field_description:
            field_description = Template(field_description).render(semantic_event)

        user_custom_fields[field_name] = (data_type, FieldInfo(description=field_description.replace('"', "'")))

    # Create a new user class with custom fields at runtime
    CustomModel = create_model(
        name,
        __base__=AnalysisModel,
        **user_custom_fields,
    )
    return CustomModel


def build_customer_intent_model(config: dict):
    pass
    """
    user_custom_fields = {
        'customer_intent': (CustomerIntent, FieldInfo(description="Identify the reason for first contact"))
    }
    """


def create_enum(name: str, options: list):
    return enum.Enum(
        name + "Enum", {str(unidecode(v)).lower().replace(" ", "_"): v for v in options}
    )


def build_entity_sentiment_model(config: dict):

    class_settings = config.get("class_settings", {})
    user_custom_fields = {}

    if "type" in class_settings:
        user_custom_fields["type"] = (
            create_enum("Type", class_settings["type"]),
            FieldInfo(description='The type of sentiment where "Opinion" is the default value'),
        )
    else:
        user_custom_fields["type"] = (
            create_enum("Type", ["Opinion"]),
            FieldInfo(description='The type of sentiment where "Opinion" is the default value'),
        )

    user_custom_fields["reason"] = (
        str,
        FieldInfo(description="Concise reason for this entity sentiment analysis"),
    )
    if "sentiment" in class_settings:
        user_custom_fields["sentiment"] = (
            create_enum("Sentiment", class_settings["sentiment"]),
            FieldInfo(description="The sentiment expressed"),
        )
    else:
        user_custom_fields["sentiment"] = (
            create_enum(
                "Sentiment", ["Very Positive", "Positive", "Neutral", "Negative", "Very Negative"]
            ),
            FieldInfo(description="The sentiment expressed"),
        )

    if not class_settings.get("ignore_target_category"):
        if "target_category" in class_settings:
            user_custom_fields["target_category"] = (
                create_enum("TargetCategoryEnum", class_settings["target_category"]),
                FieldInfo(description="Category of the target entity"),
            )
        else:
            user_custom_fields["target_category"] = (
                create_enum(
                    "TargetCategoryEnum",
                    ["Person", "Location", "Organization", "Product", "Event", "Other"],
                ),
                FieldInfo(description="Category of the target entity"),
            )

    if not class_settings.get("ignore_target_type"):
        if "target_type" in class_settings:
            user_custom_fields["target_type"] = (
                create_enum("TargetTypeEnum", class_settings["target_type"]),
                FieldInfo(description="The type of entity that the target entity of the sentiment"),
            )
        else:
            user_custom_fields["target_type"] = (
                str,
                FieldInfo(
                    description="The type of entity that the target entity of the sentiment. This is an entity type that firts the target entity category. One word that is capitalized and in singular form."
                ),
            )

    if not class_settings.get("ignore_target_entity"):
        user_custom_fields["target_entity"] = (
            str,
            FieldInfo(
                description="Propper name for the entity that is the target entity of the sentiment"
            ),
        )

    user_custom_fields["entity"] = (
        str,
        FieldInfo(description="Named entity's name for the target entity of the sentiment"),
    )
    user_custom_fields["entity_id"] = (
        str,
        FieldInfo(
            description="Named entity's numerical or coded identifier if specified for the target entity of the sentiment"
        ),
    )

    _sentimentClass = create_model(
        "EntitySentiment",
        __base__=ExtendableBaseModel,
        **user_custom_fields,
    )
    return _sentimentClass

def find_annotated_class(field: FieldInfo):
    """
    Find the annotated class from a field.
    :param field: FieldInfo
    :return: Annotated class
    """
    annotations = field.annotation
    while hasattr(annotations, '__args__'):
        annotations = annotations.__args__[0]
    return annotations

def total_enum_values(model: Type[BaseModel]) -> Tuple[int, dict[str, int]]:
    enum_count = 0
    enum_sizes: dict[str, int] = {}
    for field in model.model_fields:
        field_info: FieldInfo = model.model_fields[field]

        annotated_class = find_annotated_class(field_info)
        if isclass(annotated_class) and issubclass(annotated_class, enum.Enum):
            nr_of_enums = len(annotated_class)
            enum_sizes[field] = nr_of_enums
            enum_count += nr_of_enums
        elif isclass(annotated_class) and issubclass(annotated_class, BaseModel):
            sub_enum_count, sub_enum_sizes = total_enum_values(annotated_class)
            enum_count += sub_enum_count
            enum_sizes.update(sub_enum_sizes)

    return enum_count, enum_sizes

def alter_tools_for_voice(models: list[Type[BaseModel]], enum_limit: int = 20) -> list[BaseModel]:
    """
    Alter all tool schemas for streaming voice service when they have limit capacity.
    :param models: List of tool schemas
    :param enum_limit: Limit of enum values
    :return:
    """
    reduced_models = []
    for model in models:
        enum_count, enum_sizes = total_enum_values(model)
        if enum_count > enum_limit:
            model = create_minimal_schema(model, enum_limit)
        reduced_models.append(model)

    return reduced_models

def get_random_sample_of_enum_values(field: FieldInfo, samples: int = 3) -> str:
    """
    Get random sample of enum values.
    :param field: FieldInfo
    :param samples: Number of samples
    :return:
    """
    annotated_class = find_annotated_class(field)
    # create a randomized list of enum values
    enum_values = list(annotated_class)
    random.shuffle(enum_values)
    return ', '.join([str(x.value).split(';')[0] for x in list(annotated_class)[:samples]])


def create_missing_schema(model: Type[BaseModel], field_name: str = None) -> Type[BaseModel]:
    return create_model(
        'MissingArgumentsSchema',
        **{
            **{k: (v.annotation, v) for k, v in model.model_config['reduced_fields'].items() if k == field_name or not field_name},
        }
    )

def missing_schema_fields(model: Type[BaseModel]) -> list[str]:
    return [k for k, v in model.model_config['reduced_fields'].items()]

def create_minimal_schema(model: Type[BaseModel], enum_limit: int = 20) -> Type[BaseModel]:
    """
    Create a minimal pydantic schema from any given schema.
    The minimal schema will remove all large enum fields and replace them string fields with new description.
    :rtype: object
    :param model:
    :param enum_limit:
    :return:
    """
    enum_count, enum_sizes = total_enum_values(model)
    oversized_enums = {k: v for k, v in enum_sizes.items() if v > enum_limit}
    # todo - detect list fields
    if oversized_enums:
        reduced_model = create_model(
            'ReducedModel',
            **{
                **{k: (v.annotation, v.default) for k, v in model.model_fields.items() if k not in oversized_enums},
                **{k: (str, Field(default=v.default, description=f"{v.description}, Example values are {get_random_sample_of_enum_values(v,3)}. Use must use the same language as the examples are in.")) for k, v in model.model_fields.items() if k in oversized_enums}
            }
        )
        #check if the model is a subclass of CXSBaseTool
        reduced_model.model_config['reduced_fields'] = {k: v for k, v in model.model_fields.items() if k in oversized_enums}
        reduced_model.model_config['full_model_name'] = model.__name__
        return reduced_model
    return model