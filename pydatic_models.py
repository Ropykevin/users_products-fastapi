from pydantic import BaseModel


class UserOut(BaseModel):
    username: str
    email: str

class UserCreate(UserOut):
    password: str



class UserLogin(BaseModel):
    username: str
    password: str



class ProductBase(BaseModel):
    name: str
    cost: float
    price:float
    stock_quantity:int


class ProductUpdate(BaseModel):
    name: str | None = None
    cost: float | None = None
    price: float | None = None
    stock_quantity: int | None = None

class ProductUpdateOut(ProductUpdate):
    id: int


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int

    class Config:
        orm_mode = True


class SaleBase(BaseModel):
    quantity: int
    pid:int


class SaleCreate(SaleBase):
    pid: int

class SaleOut(SaleCreate):
    pass

class SaleUpdate(BaseModel):
    quantity: int | None = None
    pid:int | None = None


class SaleUpdateOut(SaleUpdate):
    id :int
    total_price:int


class Sale(SaleBase):
    id: int
    total_price: float
    product_id: int

    class Config:
        orm_mode = True
