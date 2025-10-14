__import__("pkg_resources").declare_namespace(__name__)
from sqlalchemy.orm import DeclarativeBase


class CXSBaseModel(DeclarativeBase):
    pass
