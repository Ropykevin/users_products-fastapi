from fastapi import FastAPI,HTTPException,Depends
import uvicorn
from datetime import timedelta,datetime,timezone
from models import SessionLocal,User,Product,Sale
from pydatic_models import UserCreate, UserLogin, ProductCreate,\
UserOut, ProductBase, ProductUpdate, ProductUpdateOut,SaleCreate,SaleUpdate,SaleUpdateOut,SaleOut
from sqlalchemy import func
from fastapi.middleware.cors import CORSMiddleware
from auth import pwd_context,authenticate_user,create_access_token,ACCESS_TOKEN_EXPIRE_MINUTES,get_current_user
import pytz
app=FastAPI()

origins=[
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST","PUT"],
    allow_headers=["Authorization", "Content-Type"],
)
db = SessionLocal()

# get users


@app.get("/users")
def get_all_users():
    users = db.query(User).all()
    db.close()
    return users
# register user

@app.post("/register" ,response_model=UserOut)
def create_user(user: UserCreate):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=400, detail="Username already registered")
    password = pwd_context.hash(user.password)
    db_user = User(username=user.username,email=user.email, password=password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    db.close()
    return db_user

# login user

@app.post("/login")
def login(user: UserLogin):
    db_user = authenticate_user(user.username, user.password)
    if not db_user:
        raise HTTPException(
            status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    print(access_token)
    return {"access_token": access_token, "token_type": "bearer"}




# get products
@app.get("/products")
def get_products(current_user: User = Depends(get_current_user)):
    products = db.query(Product).filter(
        Product.user_id == current_user.id).all()
    db.close()
    return products


# post products
@app.post("/products")
def create_product(product: ProductCreate, current_user: User = Depends(get_current_user)):
    db_product = Product(**product.model_dump(), user_id=current_user.id)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    db.close()
    return db_product

# put products 
@app.put("/products/{pid}")
async def update_product(pid: int, product: ProductUpdate, current_user: User = Depends(get_current_user), response_model = Product):
    prod = db.query(Product).filter(Product.id == pid,
                                    Product.user_id == current_user.id).first()
    if not prod :
        raise HTTPException(status_code=404,detail="product does not exist")

    if not prod.name == product.name and product.name is not None:
        prod.name = product.name

    if not prod.cost == product.cost and product.cost is not None:
        prod.cost = product.cost
    
    if not prod.price == product.price and product.price is not None:
        prod.price = product.price
    
    if not prod.stock_quantity == product.stock_quantity and product.stock_quantity is not None:
        prod.stock_quantity = product.stock_quantity

    db.commit()

    prod = db.query(Product).filter(Product.id == pid).first()
    return prod

# get sales

@app.get("/sales")
def get_sales( current_user: User = Depends(get_current_user)):
    sales = db.query(Sale).join(Product).filter(
        Product.user_id == current_user.id).all()
    db.close()
    return sales

# post sales 


@app.post("/sales", response_model=SaleOut)
def make_sale(sale: SaleCreate, current_user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == sale.pid,
                                       Product.user_id == current_user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    total_price = product.price * sale.quantity
    db_sale = Sale(quantity=sale.quantity,
                        total_price=total_price, product_id=sale.pid)
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)


# update sale 


@app.put("/sales/{sale_id}", response_model=SaleUpdateOut)
async def update_sale(sale_id: int, sale_update: SaleUpdate, current_user: User = Depends(get_current_user)):
    sale = db.query(Sale).join(Product).filter(Sale.id == sale_id,
                                               Product.user_id == current_user.id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    sale.quantity = sale_update.quantity
    sale.pid = sale_update.pid
    db.commit()

    return sale

# sales per day

@app.get("/sales_per_day")
def sales_per_day(current_user: User = Depends(get_current_user)):
    today = datetime.now(pytz.utc).replace(
        hour=0, minute=0, second=0, microsecond=0)
    sales = (
        SessionLocal().query(func.date(Sale.sold_at), func.count(Sale.id))
        .filter(Sale.product.has(user_id=current_user.id), Sale.sold_at >= today)
        .group_by(func.date(Sale.sold_at))
        .all()
    )
    dates = [sale[0].isoformat() for sale in sales]
    counts = [sale[1] for sale in sales]
    return {"data": [{"x": dates, "y": counts, "type": "line", "name": "Sales per Day"}]}


# profit per day
@app.get("/profit_per_day")
def profit_per_day(current_user: User = Depends(get_current_user)):
    today = datetime.now(pytz.utc).replace(
        hour=0, minute=0, second=0, microsecond=0)
    sales = (
        SessionLocal().query(func.date(Sale.sold_at), func.sum(Sale.total_price))
        .filter(Sale.product.has(user_id=current_user.id), Sale.sold_at >= today)
        .group_by(func.date(Sale.sold_at))
        .all()
    )
    dates = [sale[0].isoformat() for sale in sales]
    profits = [sale[1] for sale in sales]
    return {"data": [{"x": dates, "y": profits, "type": "line", "name": "Profit per Day"}]}

# sales per product

@app.get("/sales_per_product")
def sales_per_product(current_user: User = Depends(get_current_user)):
    products = (
        SessionLocal().query(Product.id, Product.name, func.count(Sale.id))
        .join(Sale)
        .filter(Product.user_id == current_user.id)
        .group_by(Product.id, Product.name)
        .all()
    )
    product_names = [product[1] for product in products]
    sales_counts = [product[2] for product in products]
    return {"data": [{"x": product_names, "y": sales_counts, "type": "bar", "name": "Sales per Product"}]}


# profit per product 
@app.get("/profit_per_product")
def profit_per_product(current_user: User = Depends(get_current_user)):
    products = (
        SessionLocal().query(Product.id, Product.name, func.sum(Sale.total_price))
        .join(Sale)
        .filter(Product.user_id == current_user.id)
        .group_by(Product.id, Product.name)
        .all()
    )
    product_names = [product[1] for product in products]
    profits = [product[2] for product in products]
    return {"data": [{"x": product_names, "y": profits, "type": "bar", "name": "Profit per Product"}]}


if __name__ == "__main__":
    config = uvicorn.Config("main:app", port=8000, log_level="info")
    server = uvicorn.Server(config)
    server.run()
