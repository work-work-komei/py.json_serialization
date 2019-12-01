from typing import TypeVar
import json
from src.info import HELPER
from type_provider import ListType, MapType

T = TypeVar("T")

CONTAINER_TYPES = {list, dict}


def parse(text, cls, option):
    return _from_json_obj(json.loads(text), cls, option, cls.__name__)


def from_json_obj(json_obj, cls, option):
    return _from_json_obj(json_obj, cls, option, cls.__name__)


def _from_json_obj(source, cls, option, path):
    store = HELPER.get_store(cls)
    if store is None:
        raise ValueError("cls must be decorated by json_class")

    if store.cls.validate_type(type(source)):
        raise ValueError(f"Unexpected JSON object expected: {store.cls.expected_types}, actual: {type(source)}")

    dst = store.cls.creator()

    for key, member in store.members.items():
        json_key = member.json_key
        cur_path = f"{path}.{json_key}"
        src = member.getter(source)
        if src is None:
            if member.mamdarory:
                raise ValueError(f"Property is mandatory but null or not found: {path}")
            else:
                continue

        value = src
        if member.recursive is not None and type(src) in CONTAINER_TYPES:
            value = _expand(src, cls, member, option, cur_path)

        setattr(dst, member.setter_name, value)


def _expand(source, cls, member, opt, path):
    recursive = member.recursive
    if isinstance(member, ListType):
        return [_from_json_obj(src, recursive.get_type(cls, src), opt, f"{path}.{i}") for i, src in enumerate(source)]
    elif isinstance(member, MapType):
        return {k: _from_json_obj(src, recursive.get_type(cls, src), opt, f"{path}.{k}") for k, src in source.items()}
    else:
        return _from_json_obj(source, recursive.get_type(cls, source), opt, path)