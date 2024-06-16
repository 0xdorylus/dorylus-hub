import math
from typing import List

from fastapi import APIRouter, Depends, Response, HTTPException

from agent.models.article import Article
from agent.models.assistant import AssistantModel, Assistant, CreateAssistantModel
from agent.models.base import GenericResponseModel
from agent.models.article import ArticleListResponseModel, ArticleListItemModel, ArticleListRequestModel,  ArticleResponseModel, CreateArticleRequestModel, UpdateArticleRequestModel
from agent.models.user import User
from agent.services.acl_service import AclService
from agent.services.assistant_service import AssistantService
from agent.utils.x_auth import get_uid_by_token

router = APIRouter(prefix="/article", tags=["article"])


@router.post("/create", response_model=GenericResponseModel[ArticleResponseModel],response_description="create article")
async def create(form:CreateArticleRequestModel ,uid: str = Depends(get_uid_by_token),acl_service: AclService = Depends()):
    if acl_service.user_can_create_article(uid):
        doc = await Article.create_article(uid,form)
        return GenericResponseModel(result=ArticleResponseModel(**doc.dict()))
    else:
        raise HTTPException(403,"Can't Create")

@router.post("/update", response_model=GenericResponseModel[ArticleResponseModel],response_description="create article")
async def update(form:UpdateArticleRequestModel ,uid: str = Depends(get_uid_by_token),acl_service: AclService = Depends()):
    if acl_service.user_can_create_article(uid):
        doc = await Article.update_article(uid,form)
        return GenericResponseModel(result=doc)
    else:
        raise HTTPException(403,"Can't Update")

@router.get("/detail", response_model=GenericResponseModel[ArticleResponseModel])
async def detail(id:str):
    """
    详情，隐私协议，注册协议等，指定ID
    :param id:
    :return:
    """
    article = await Article.get(id)
    if article:
        vo =  ArticleResponseModel(**article.model_dump())
        vo.creator = await User.get_info(vo.id)
        return GenericResponseModel(result=vo)
    else:
        raise HTTPException(404,"Not Found")

@router.post("/list", response_model=GenericResponseModel[ArticleListResponseModel])
async def list_article(request_form: ArticleListRequestModel):
    skip = (request_form.page - 1) * request_form.pagesize

    limit = request_form.pagesize
    items: List[ArticleListItemModel] = []

    sort = (-Article.id)
    query = {}

    # print(query)
    total = await Article.find(query).count()
    total_page = math.ceil(total / request_form.pagesize)
    objects = await Article.find(query).sort(sort).skip(skip).limit(limit).to_list()
    for item in objects:
        vo = ArticleListItemModel(**item.dict())
        vo.creator = await User.get_info(item.uid)
        items.append(vo)

    response_model = ArticleListResponseModel()
    response_model.total = total
    response_model.list = items
    response_model.total_page = total_page
    return GenericResponseModel(result=response_model)


