import enum
from typing import Dict, List, Literal, Optional, Tuple, Type, Union, Any, Annotated
from pydantic import BaseModel, Field
from pydantic import model_validator

from cxs.core.schema import empty_list, empty_dict, CXSBase, OmitIfNone


class BaseProductCondition(enum.Enum):
    NEW = "New"
    USED = "Used"
    REFURBISHED = "Refurbished"
    OPEN_BOX = "Open-Box"
    SEALED = "Sealed"
    ANY = "Any"

class BaseProductFinancing(enum.Enum):
    LEASE = "Lease"
    LOAN = "Loan"
    RENT = "Rent"
    BUY = "Buy"
    SUBSCRIBE = "Subscribe"
    ANY = "Any"

class BaseProductOrdering(enum.Enum):
    CHEAPEST = "Cheapest"
    MOST_EXPENSIVE = "Most Expensive"
    NEWEST = "Newest"
    OLDEST = "Oldest"
    MOST_RELEVANT = "Most Relevant"
    BEST_SELLING = "Best Selling"
    HIGHEST_RATED = "Highest Rated"
    LOWEST_RATED = "Lowest Rated"
    ANY = "Any"

class ProductListing(CXSBase):
    sku: Optional[str] = Field(description="A unique product identifier if available", default="")
    name: str = Field(description="The name of the listing.")
    price: Optional[float] = Field(description="The price of the product in the listing.", default=0)
    general_description: Annotated[Optional[str], OmitIfNone()] = Field(description="A general description of the product.", default="")

    color: Annotated[Optional[str], OmitIfNone()] = Field(description="The color of the product.", default="")
    url: Annotated[Optional[str], OmitIfNone()] = Field(description="The url of the listing.", default="")
    image: Annotated[Optional[str], OmitIfNone()] = Field(description="The availability of the product.", default="")

class BaseProductInfo(ProductListing):

    model_config = {"extra": "allow"}

    slug: Annotated[Optional[str],OmitIfNone()] = Field(description="The product slug", default="")
    category: Annotated[Optional[str],OmitIfNone()] = Field(description="The assumed category of the product. Capitalized, in singular form and in English.", default="")
    sub_category: Annotated[Optional[str], OmitIfNone()] = Field(description="The assumed category of the product. Capitalized, in singular form and in English.", default="")
    manufacturer: Annotated[Optional[str], OmitIfNone()] = Field(description="The name of the manufacturer of the product.", default="")
    brand: Annotated[Optional[str], OmitIfNone()] = Field(description="The name of the brand of the product.", default="")
    product_type: Annotated[Optional[str], OmitIfNone()] = Field(description="The core type of the product. Capitalized, in singular form and in English.", default="")
    product_line: Annotated[Optional[str], OmitIfNone()] = Field(description="The product line of the product.", default="")
    product_variant: Annotated[Optional[str], OmitIfNone()] = Field(description="A full product name", default="")
    main_features: Annotated[Optional[list[str]], OmitIfNone()] = Field(description="Various desired features of the product.", default_factory=lambda: empty_list())
    images: Annotated[Optional[list[str]], OmitIfNone()] = Field(description="Image URLs of the product.", default_factory=lambda: empty_list())
    listings: Annotated[Optional[list[ProductListing]], OmitIfNone()] = Field(description="The pricing of the product.", default_factory=lambda: empty_list())
    availability: Annotated[Optional[dict[str, str]], OmitIfNone()] = Field(description="The availability of the product.", default_factory=lambda: empty_dict())
    properties: Annotated[Optional[dict[str, str]], OmitIfNone()] = Field(description="Various Product Properties.", default_factory=lambda: empty_dict())

    @model_validator(mode="before")
    def pre_init(cls, values):
        for key, value in values.items():
            if key == 'category':
                values[key] = str(value)
            if key == 'availability' and isinstance(value, dict):
                values[key] = {key: str(value) for key, value in value.items()}
        return values

    __pydantic_extra__ = "allow"

class ProductDetailsInfo(BaseProductInfo):
    full_description: Optional[str] = Field(description="A general description of the product.", default="")
    properties: Optional[dict] = Field(description="A general description of the product.", default_factory=lambda: empty_dict())

class ProductDetailsModel(CXSBase):
    sku: list[str] = Field(description="A list of product SKUs, one for each products you want to look up.")

class ProductVectorSearchModel(CXSBase):
    query: str = Field(description="A text query describing what products to search for.")

class BaseProductSearchModel(CXSBase):
    query: str = Field(description="A search query with likely search keywords. Fill other search parameters to get more accurate results.")
    price_min: Optional[int] = Field(description="The minimum price of the products to return.", default=0)
    price_max: Optional[int] = Field(description="The maximum price of the products to return.", default=0)
    condition: Optional[BaseProductCondition] = Field(description="The condition of the product.", default=BaseProductCondition.ANY)
    financing: Optional[BaseProductFinancing] = Field(description="The financing options for the product.", default=BaseProductFinancing.ANY)
    ordering: Optional[BaseProductOrdering] = Field(description="The product ordering best suited to provide meaningful results.", default=BaseProductOrdering.ANY)
    items: Optional[int] = Field(description="The number of products you need returned.", default=10)

    @model_validator(mode="before")
    def pre_init(cls, values):
        if 'query' not in values or not values.get('query'):
            values['query'] = ''
        if 'condition' not in values or not values.get('condition'):
            values['condition'] = BaseProductCondition.ANY
        if 'financing' not in values or not values.get('financing'):
            values['financing'] = BaseProductFinancing.ANY
        if 'ordering' not in values or not values.get('ordering'):
            values['ordering'] = BaseProductOrdering.ANY
        if 'price_min' not in values or not values.get('price_min'):
            values['price_min'] = 0
        if 'price_max' not in values or not values.get('price_max'):
            values['price_max'] = 0
        if 'items' not in values or not values.get('items'):
            values['items'] = 0
        return values

    __pydantic_extra__ = "allow"

class ProductSearchModel(BaseProductSearchModel):
    color: Optional[str] = Field(description="The color of the product.", default="")

    __pydantic_extra__ = "deny"

class ProductSearchResults(BaseModel):
    products: List[BaseProductInfo|ProductListing] = Field(description="The list of products found.", default_factory=lambda: empty_list())
    total: int = Field(description="The total number of products found using the query parameters you provided.", default=0)
    facets: Annotated[Optional[dict],OmitIfNone()] = Field(description="Breakdown of the number of products found in each facet group.", default= empty_dict())
    presentation: Annotated[Optional[str],OmitIfNone()] = Field(description="Use this instructions to format your output.", default= '')
