# from typing import List, Optional
#
# from pydantic import BaseModel
#
# # Schemas for request and response validation
# from main import StatusEnum
#
#
# class ItemCreate(BaseModel):
#     title: str
#     status: StatusEnum
#     description: Optional[str] = None
#     id: Optional[int] = None
#     owner_id: int
#     status: StatusEnum  # Added status field to schema
#
#     class Config:
#         orm_mode = True
#
#
# # class ItemCreate(ItemBase):
# #     pass
#
#
# # class Item(ItemBase):
# #     id: Optional[int] = None
# #     owner_id: int
# #     status: StatusEnum  # Added status field to schema
# #
# #     class Config:
# #         orm_mode = True
#
#
#
#
#
# class User(UserBase):
#     id: Optional[int] = None
#     is_active: Optional[bool] = True
#     items: List[Item] = []
#
#     class Config:
#         orm_mode = True
#
#
# class UserId(BaseModel):
#     id: int
