import importlib
import inspect
import pkgutil

from aiocache import cached as pcached
from aiocache.serializers import PickleSerializer


def cxs_solution(type: str = None, provider: str = None, variant: str = None, **kwargs):
    def decorator(cls):
        cls.__cxs_solution__ = {"type": type, "provider": provider, "variant": variant, **kwargs}
        cls.__is_cxs_solution__ = True
        return cls

    return decorator


def cxs_component(component_type: str = None, component_variant: str = None, **kwargs):
    def decorator(cls):
        cls.__cxs_annotation_params__ = {
            "component_type": component_type,
            "component_variant": component_variant,
            **kwargs,
        }
        cls.__cxs_is_annotated__ = True
        return cls

    return decorator


def find_cxs_annotated_classes(base_package, annotation_name):
    annotated_classes = set()
    seen_classes = {}

    for finder, module_name, ispkg in pkgutil.walk_packages(
        base_package.__path__, base_package.__name__ + "."
    ):
        try:
            module = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if getattr(obj, f"__is_{annotation_name}__", False):
                    annotation_params = getattr(obj, f"__{annotation_name}__", {})
                    if id(obj) not in seen_classes:
                        seen_classes[id(obj)] = (obj.__module__, obj, annotation_params)
                        annotated_classes.add(
                            (module_name, obj, frozenset(annotation_params.items()))
                        )
        except Exception as e:
            print(f"Could not inspect module {module_name}: {e}")

    return annotated_classes
