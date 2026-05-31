from pydantic import BaseModel, ConfigDict, Field


class MerchProductResponse(BaseModel):
    id: str
    name: str
    price: int
    image: str


class MerchOrderLineRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=64)
    quantity: int = Field(ge=1, le=99)


class MerchOrderCreateRequest(BaseModel):
    items: list[MerchOrderLineRequest] = Field(min_length=1)


class MerchOrderLineResponse(BaseModel):
    product_id: str
    product_name: str
    unit_price: int
    quantity: int
    line_total: int

    model_config = ConfigDict(from_attributes=True)


class MerchOrderResponse(BaseModel):
    id: int
    total_points: int
    available_points: int
    items: list[MerchOrderLineResponse]

    model_config = ConfigDict(from_attributes=True)
