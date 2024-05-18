from typing import Optional
from fastapi import FastAPI

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from typing import List, Optional
from pydantic import BaseModel

Base = declarative_base()

engine = create_engine('mysql://testuser:pass@localhost/items')

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()

class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

class UserId(BaseModel):
    id: int

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    items: List[Item] = []

    class Config:
        orm_mode = True

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(50))
    is_active = Column(Boolean, default=True)

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), index=True)
    status = Column(String(50))
    description = Column(String(50))
    owner_id = Column(Integer)

class ItemHistory(Base):
    __tablename__ = "item_history"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer)
    old_assignee = Column(Integer)
    new_assignee = Column(Integer)

Base.metadata.create_all(bind=engine)


def create_user(user: UserCreate):
    db = SessionLocal()
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = User(email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    return db_user

def create_user_item(item: ItemCreate, user_id: int):
    db = SessionLocal()
    db_item = Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    return db_item

@app.get("/")
def read_root():
    return {"Hello": "Azure"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

@app.post("/users/")
def create_user_endpoint(user: UserCreate):
    db = SessionLocal()
    return create_user(user=user)

@app.post("/users/{user_id}/items/")
def create_item_for_user(user_id: int, item: ItemCreate):
    db = SessionLocal()
    return create_user_item(item=item, user_id=user_id)

@app.post("/reassign_item/{item_id}/")
def assign_item(item_id: int, new_owner: UserId):
    db = SessionLocal()
    item = db.query(Item).filter(Item.id==item_id).first()
    item.owner_id = new_owner.id
    db.add(item)
    db.commit()
    add_history(db, item, new_owner.id)

def add_history(db, item, new_owner_id):
    history_entry = ItemHistory(
            item_id = item.id,
            old_assignee = item.owner_id,
            new_assignee = new_owner_id
            )
    db.add(history_entry)
    db.commit()



