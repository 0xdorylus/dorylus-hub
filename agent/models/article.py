import logging

from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from ipaddress import IPv4Address
from typing import Optional, List, Set

import pymongo
from beanie import Document, Indexed, before_event, after_event

from agent.connection import get_next_id
from agent.utils.common import get_unique_id, error_return, encode_input
from agent.utils.common import op_log
from agent.utils.common import success_return
from fastapi import Depends, HTTPException, status
from agent.models.request_response_model import UserInfoModel, UserDetailModel


class ArticleResponseModel(BaseModel):
    id: str
    title: str
    content: str = ""
    creator: UserInfoModel = {}
    create_at: datetime = datetime.now()


class ArticleListRequestModel(BaseModel):
    page: int = 1
    pagesize: int = 10


class ArticleListItemModel(BaseModel):
    id: str
    title: str
    content: str = ""
    creator: UserInfoModel = {}
    create_at: datetime = datetime.now()


class ArticleListResponseModel(BaseModel):
    total: int = 0
    total_page: int = 1
    list: List[ArticleListItemModel] = []


class CreateArticleRequestModel(BaseModel):
    title: str
    content: str
    uid: str
    category_id: str = ""


class UpdateArticleRequestModel(BaseModel):
    id: str
    title: str
    content: str
    category_id: str = ""


class ArticleCategory(Document):
    id: str = Field(default_factory=get_unique_id)
    title: str = Field("", min_length=1)
    content: Optional[str] = ""
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    class Settings:
        name = "article_category"


class Article(Document):
    id: str = Field(default_factory=get_unique_id)
    article_id: int = 0
    uid: str = ""
    title: str = Field("", min_length=1)
    content: str = Field("", min_length=1)
    category_id: str = ""
    is_hot: int = 0
    is_show: int = 1
    view_num: int = 0
    up_num: int = 0
    down_num: int = 0
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    class Settings:
        name = "article"

    @classmethod
    async def create_article(cls, uid, form: CreateArticleRequestModel):
        data = form.model_dump()
        data['uid'] = uid
        data['article_id'] = await get_next_id("article")
        doc = await Article(**data).create()
        return doc

    @classmethod
    async def update_article(cls, uid, form: UpdateArticleRequestModel):
        data = form.model_dump()
        doc = await Article.find_one(Article.id == form.id).update({"$set": data})
        return doc
