from pydantic import BaseModel, ConfigDict


class StudentBase(BaseModel):
    full_name: str
    study_group: str


class StudentCreate(StudentBase):
    pass


class StudentResponse(StudentBase):
    id: int
    total_points: int
    available_points: int

    model_config = ConfigDict(from_attributes=True)


class ItemBase(BaseModel):
    name: str
    type: str


class ItemCreate(ItemBase):
    pass


class ItemResponse(ItemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TransactionCreate(BaseModel):
    student_id: int
    item_id: int
    points_change: int


class TransactionResponse(BaseModel):
    id: int
    student_id: int
    item_id: int
    points_change: int

    model_config = ConfigDict(from_attributes=True)
