import os
import traceback
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

import bcrypt
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, ValidationError
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Enum, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session, scoped_session

Base = declarative_base()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql://root:password123@localhost:4406/db_items")


# Enum for Item status
class StatusEnum(PyEnum):
    NEW = "NEW"
    APPROVED = "APPROVED"
    EOL = "EOL"


# User model with corrected relationships
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True)
    hash_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    items = relationship("Item", back_populates="owner")  # Added back_populates for proper ORM relationship


# Item model with status field and corrected relationships
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    description = Column(Text, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    status = Column(Enum(StatusEnum), default=StatusEnum.NEW)  # Added status field
    owner = relationship("User", back_populates="items")  # Added back_populates for proper ORM relationship
    history = relationship("ItemHistory", back_populates="item")  # Added relationship to ItemHistory


# ItemHistory model to track status changes
class ItemHistory(Base):
    __tablename__ = "item_history"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey('items.id'))
    old_status = Column(Enum(StatusEnum), index=True)  # Track old status, indexed to increase performance
    new_status = Column(Enum(StatusEnum), index=True)  # Track new status, indexed to increase performance
    change_date = Column(DateTime, default=datetime.utcnow)  # Record change date
    item = relationship("Item", back_populates="history")  # Added back_populates for proper ORM relationship


# Create all tables in the database
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
SessionLocal = scoped_session(sessionmaker(bind=engine))


# Dependency for session management
def get_db():
    """
    Dependency function to manage database sessions.

    :return: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()


class ItemCreate(BaseModel):
    title: Optional[bool] = True
    status: Optional[StatusEnum] = None
    description: Optional[str] = None
    id: Optional[int] = None
    owner_id: int
    status: StatusEnum  # Added status field to schema

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    id: Optional[int] = None
    is_active: Optional[bool] = True

    # items: List[ItemCreate] = []

    class Config:
        orm_mode = True


class StatusUpdate(BaseModel):
    status: StatusEnum  # Schema for updating status


def hash_password(raw_password: str) -> str:
    # Hash the password
    hashed_password = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt())
    # Convert the hashed password to a string for storing in the database
    return hashed_password.decode('utf-8')


# CRUD functions with proper session management and added functionality
def create_user(db: Session, user: UserCreate):
    """
    Creates a new user in the database.

    :param db: Database session
    :param user: UserCreate object containing user data
    :return: Created user object
    """
    try:
        new_hashed_password = hash_password(user.password)
        db_user = User(email=user.email, hash_password=new_hashed_password, is_active=True)

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return UserCreate(id=db_user.id, email=db_user.email)
    except ValidationError as x:
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"{x}")
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"{e}")


def create_user_item(db: Session, item: ItemCreate, user_id: int):
    """
    Creates a new item associated with a user in the database.

    :param db: Database session
    :param item: ItemCreate object containing item data
    :param user_id: ID of the user who owns the item
    :return: Created item object
    """
    try:
        db_item = Item(**item.dict(), owner_id=user_id)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return ItemCreate(id=db_item.id, title=db_item.title, status=db_item.status,
                          description=db_item.description)
    except ValidationError as x:
        raise HTTPException(status_code=400, detail=f"{x}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")


def update_item_status(db: Session, item_id: int, status: StatusEnum):
    """
    Updates the status of an item in the database and records the change in history.

    Improvement made:
        Improved error handling in the update_item_status function to raise a 404 error if the item is not found.

    :param db: Database session
    :param item_id: ID of the item to update
    :param status: New status for the item
    :return: Updated item object
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    try:
        old_status = item.status  # Track old status before updating
        item.status = status
        db.add(item)
        db.commit()
        db.refresh(item)
        add_status_history(db, item, old_status, status)  # Add status change history
        return ItemCreate(id=item.id, title=item.title, status=item.status,
                          description=item.description)
    except ValidationError as x:
        raise HTTPException(status_code=400, detail=f"{x}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")


def add_status_history(db: Session, item: Item, old_status: StatusEnum, new_status: StatusEnum):
    """
    Adds a new entry to the item history table to record the change in status.

    :param db: Database session
    :param item: Item object whose status changed
    :param old_status: Previous status of the item
    :param new_status: New status of the item
    """
    try:
        history_entry = ItemHistory(
            item_id=item.id,
            old_status=old_status,
            new_status=new_status,
            change_date=datetime.utcnow()
        )
        db.add(history_entry)
        db.commit()
    except ValidationError as x:
        raise HTTPException(status_code=400, detail=f"{x}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")


def get_items_by_status(db: Session, status: StatusEnum):
    """
    Retrieves a list of items with the specified status from the database.

    :param db: Database session
    :param status: StatusEnum value to filter items by
    :return: List of items with the specified status
    """
    return db.query(Item).filter(Item.status == status).all()


# API routes
@app.get("/")
def read_root():
    """
    Default route handler.

    :return: Welcome message
    """
    return {"Hello": "World"}


@app.get("/health/alive")
def read_root():
    """
    Default route handler.

    :return: Welcome message
    """
    return {"status": "Success", "message": "Application is healthy"}


@app.post("/users/", response_model=UserCreate)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    """
    API endpoint to create a new user.

    :param user: UserCreate object containing user data
    :param db: Database session (dependency injection)
    :return: Created user object
    """
    return create_user(db, user)


@app.post("/users/{user_id}/items/", response_model=ItemCreate)
def create_item_for_user(user_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    """
    API endpoint to create a new item for a specific user.

    :param user_id: ID of the user who owns the item
    :param item: ItemCreate object containing item data
    :param db: Database session (dependency injection)
    :return: Created item object
    """
    return create_user_item(db, item, user_id)


# Endpoint to update item status
@app.put("/items/{item_id}/status", response_model=ItemCreate)
def update_item_status_endpoint(item_id: int, status_update: StatusUpdate, db: Session = Depends(get_db)):
    """
    API endpoint to update the status of an item.

    :param item_id: ID of the item to update
    :param status_update: StatusUpdate object containing new status data
    :param db: Database session (dependency injection)
    :return: Updated item object
    """
    return update_item_status(db, item_id, status_update.status)


# Endpoint to get items by status
@app.get("/items/status/{status}", response_model=List[ItemCreate])
def get_items_by_status_endpoint(status: StatusEnum, db: Session = Depends(get_db)):
    """
    API endpoint to retrieve items by status.

    :param status: StatusEnum value to filter items by
    :param db: Database session (dependency injection)
    :return: List of items with the specified status
    """
    return get_items_by_status(db, status)
