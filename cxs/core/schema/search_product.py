from pydantic import BaseModel
from pydantic import Field


class DocumentImage(BaseModel):
    uri: str
    width: int
    height: int


class Embedding(BaseModel):
    text: str
    vector: list[float]
    images: list[DocumentImage]


class ProductSearchDocument(BaseModel):

    label: str = Field(..., description="label of the document")
    og_title: str = Field(..., description="The og:title of the document")
    og_last_modified: str = Field(
        ..., description="The ISO 8601 formatted timestamp when the document was last modified"
    )

    brand: str = Field(
        ..., description="The properly spelled brand name according to the brand itself"
    )
    product_line: str = Field(..., description="Product line")
    product_variant: str = Field(..., description="Product variant")
    product: str = Field(..., description="A full descriptive name of the product")
    model: str = Field(..., description="The model number or year of the product")

    category_level_1: str = Field(..., description="The root category of the product")
    category_level_2: str = Field(..., description="The second level category of the product")
    category_level_3: str = Field(
        ...,
        description="The third level category of the product if useful for classification of the product",
    )
    category_level_4: str = Field(
        ...,
        description="The fourth level category of the product if useful for classification of the product",
    )

    color: str = Field(..., description="The color of the product")
    normalized_color: str = Field(
        ...,
        description="The normalized color name for the product that translates brand specific color names to a common color name",
    )

    price: float = Field(description="The price of the product")
    price_from: float = Field(description="The price of the product if it is a range")
    price_to: float = Field(description="The price of the product if it is a range")
    availability: str = Field(..., description="The availability of the product")

    content: str = Field(
        ...,
        description="The complete product description copied verbatim from the input data. Ignore all content irrelevant to the main product on the page. Must be in same language as input.",
    )
    sales_pitch: str = Field(
        ...,
        description="Everything a trained sales person would say to sell this product. Must be in same language as input.",
    )
    specs: str = Field(
        ...,
        description="All product specifications and details - not in main content - phrased in general language as it could be described by a seasoned salesperson in a lengthy conversation with a customer. Must be in same language as input.",
    )
    typical_queries: list[str] = Field(
        ...,
        description="10 user sentences typical for users looking for a product like this or other products in this product category. Must be in same language as input.",
    )
    questions: list[str] = Field(
        ...,
        description="10 product specific questions that are answered on this page. Must be in same language as input.",
    )
    search_words: list[str] = Field(
        ...,
        description="10 search-words/keywords a customer might use when searching for this product. Must be in same language as input.",
    )


class ExtendProduct(BaseModel):

    brand: str = Field(
        ..., description="The properly spelled brand name according to the brand itself"
    )
    product_line: str = Field(..., description="Product line")
    product_variant: str = Field(..., description="Product variant")
    product: str = Field(..., description="A full descriptive name of the product")
    model: str = Field(..., description="The model number or year of the product")

    sales_pitch: str = Field(
        ...,
        description="Everything a trained sales person would say to sell this product. Must be in same language as input.",
    )
    specs: str = Field(
        ...,
        description="All product specifications and details - not in main content - phrased in general language as it could be described by a seasoned salesperson in a lengthy conversation with a customer. Must be in same language as input.",
    )
    typical_queries: list[str] = Field(
        ...,
        description="10 user sentences typical for users looking for a product like this or other products in this product category. Must be in same language as input.",
    )
    questions: list[str] = Field(
        ...,
        description="10 product specific questions that are answered on this page. Must be in same language as input.",
    )
    search_words: list[str] = Field(
        ...,
        description="10 search-words/keywords a customer might use when searching for this product. Must be in same language as input.",
    )
