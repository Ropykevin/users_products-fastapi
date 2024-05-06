from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email:str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class ProductBase(BaseModel):
    name: str
    cost: float
    price:float
    stock_quantity:int


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int

    class Config:
        orm_mode = True
