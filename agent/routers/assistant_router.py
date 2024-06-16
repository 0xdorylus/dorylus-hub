import math
from typing import List, Set

from fastapi import APIRouter, Depends, Response

from agent.models.channel import Channel
from agent.models.request_response_model import AssistantListItemModel, GirlListResponseModel, GirlListItemItemModel, \
    PageRequestModel, PromptListResponseModel, PromptListItemModel, IDModel, HotModel
from agent.models.assistant import AssistantModel, Assistant, CreateAssistantModel, \
    AssistantDetailModel, Girl
from agent.models.base import GenericResponseModel
from agent.models.request_response_model import CreateAssistantResponseModel, FilterTagResponseModel, \
    AssistantListResponseModel, AssistantListRequestModel
from agent.models.system_prompt import SystemPrompt
from agent.models.system_tag import SystemTag, SystemtTagModel
from agent.models.user import User
from agent.models.user_config import UserConfig
from agent.services.assistant_service import AssistantService
from agent.utils.common import success_return, fill_model_from_obejct
from agent.utils.x_auth import get_uid_by_token
from agent.models.subscribe import Subscription

from fastapi import Query

router = APIRouter(prefix="/role", tags=["role"])


# @router.get("/me")
# async def get_self():
#     """Get current user"""
#     return {"uid": uid}
#
# @router.post("/me")
# async def send(askForm:AskForm):
#     """Get current user"""
#     return {"uid": uid}
#
# @router.post("/query"):
# async def query(assistant_id:str):
#     """Get current user"""
#
#     return {"uid": uid}

@router.post("/update", response_model=GenericResponseModel[AssistantModel],summary="设置角色")
async def update_assistant(update_form: AssistantModel, uid: str = Depends(get_uid_by_token),
                           assistant_service: AssistantService = Depends()):
    """Update Assistant
        为空的字段会被忽略调
    """
    print(update_form)
    ret = await assistant_service.update_assistant(uid, update_form)
    return GenericResponseModel(result=ret)


@router.post("/create", response_model=GenericResponseModel[CreateAssistantResponseModel],summary="创建角色")
async def create_assistant(assistant_form: CreateAssistantModel, uid: str = Depends(get_uid_by_token),
                           assistant_service: AssistantService = Depends()) :
    """Create Assistant
        创建角色 ，只需部分字段
    """
    ret = await assistant_service.create_assistant(uid, assistant_form)
    return GenericResponseModel(result=ret)


@router.post("/tag_list", response_model=GenericResponseModel[FilterTagResponseModel],summary="系统tag分类列表")
async def tag_list():
    """
        获取左侧filter tag list
        选中一个则在tag_ids里面增加相应的值
    """
    items = await SystemTag.find_all().to_list()
    category: Set[str] = set()
    tag_items: List[SystemtTagModel] = []
    for item in items:
        category.add(item.tag)
        tag_model = SystemtTagModel(**item.dict())
        tag_items.append(tag_model)

    data = {
        "category":category, "items":tag_items
    }
    response_model = FilterTagResponseModel(category=category, items=tag_items)
    # response_model.category = category
    # response_model.items = tag_items

    return GenericResponseModel(result=response_model)


@router.post("/explorer",response_model=GenericResponseModel[AssistantListResponseModel],summary="浏览角色市场")
async def role_list(request_form:AssistantListRequestModel):
    skip = (request_form.page - 1) * request_form.pagesize

    limit = request_form.pagesize
    items : List[AssistantListItemModel]=[]

    sort = (-Assistant.id)
    filter = {"visiablity":1}
    tag_ids = request_form.tag_ids
    if len(tag_ids) > 0:
        filter['tag_ids'] = {"$in": tag_ids}

    total = await Assistant.find(filter).count()

    total_page = math.ceil(total / request_form.pagesize)

    objects = await Assistant.find(filter).sort(sort).skip(skip).limit(limit).to_list()
    for item in objects:
        id = item.id
        if id in ['01HEPT5WH1ASNH9RBK1TGD9280','01HEPSBV12BM7G9H6SJSQX5VMV','01HEQXYWB8AKPAE7QE3HDRN31Q',
                  '01HEPRWAGWGEN2DNDX8QHPPYTH','01HEN02V8G8WGZ70QS5CE95XRK','01HEMZE0B245N8YCM7A3XJ25H8',
                  '01HDR6QGHSFSMX8FHEDA8FMA67']:
            continue
        object = AssistantListItemModel(**item.dict())
        object.creator = await User.get_info(item.uid)
        object.avatar = item.get_avatar()

        items.append(object)

    response_model = AssistantListResponseModel()
    response_model.total = total
    response_model.list = items
    response_model.total_page = total_page
    return GenericResponseModel(result=response_model)


def compare_func(item):
    return item.is_lock ==False
@router.post("/girls",response_model=GenericResponseModel[GirlListResponseModel])
async def girl_list(request_form:AssistantListRequestModel,uid: str = Depends(get_uid_by_token)):
    skip = (request_form.page - 1) * request_form.pagesize

    limit = request_form.pagesize

    sort = (-Girl.id)
    filter = {}
    tag_ids = request_form.tag_ids
    if len(tag_ids) > 0:
        filter['tag_ids'] = {"$in": tag_ids}

    total = await Girl.find(filter).count()

    total_page = math.ceil(total / request_form.pagesize)

    objects = await Girl.find(filter).sort(sort).skip(skip).limit(limit).to_list()
    user = await User.get(uid)

    items : List[GirlListItemItemModel]=[]
    outs : List[GirlListItemItemModel]=[]

    for item in objects:
        item.get_avatar()
        background = item.get_backgroud()
        is_lock = True
        if item.is_public:
            is_lock = False
        if user.level>0:
            is_lock = False


        object = GirlListItemItemModel(**item.dict())
        object.background = background
        object.is_lock = is_lock

        items.append(object)

    sorted_data = sorted(items, key=compare_func, reverse=True)

    response_model = GirlListResponseModel()
    response_model.total = total
    response_model.list = sorted_data
    response_model.total_page = total_page
    return GenericResponseModel(result=response_model)

@router.post("/mylist",response_model=GenericResponseModel[AssistantListResponseModel])
async def my_role_list(request_form:AssistantListRequestModel,uid: str = Depends(get_uid_by_token)):
    """
        我创建的角色列表
    :param request_form: AssistantListRequestModel
    :param uid: str
    :return: AssistantListResponseModel
    """
    skip = (request_form.page - 1) * request_form.pagesize

    limit = request_form.pagesize
    items : List[AssistantListItemModel]=[]

    sort = (-Assistant.id)
    filter = {"uid":uid}
    tag_ids = request_form.tag_ids
    if len(tag_ids) > 0:
        filter['tag_ids'] = {"$in": tag_ids}

    total = await Assistant.find(filter).count()

    total_page = math.ceil(total / request_form.pagesize)

    objects = await Assistant.find(filter).sort(sort).skip(skip).limit(limit).to_list()
    for item in objects:
        object = AssistantListItemModel(**item.dict())
        object.creator = await User.get_info(item.uid)
        items.append(object)

    response_model = AssistantListResponseModel()
    response_model.total = total
    response_model.list = items
    response_model.total_page = total_page
    return GenericResponseModel(result=response_model)

@router.get("/detail",response_model=GenericResponseModel[AssistantDetailModel],summary="AI角色详情")
async def role_detail(id: str, uid: str = Depends(get_uid_by_token)):
    """
        角色详情


    """
    assistant = await Assistant.get(id)
    vo = AssistantDetailModel(**assistant.dict())
    vo.avatar = assistant.get_avatar()

    if vo:
        channel = await Channel.get_ai_channel(uid, id)
        vo.creator = await User.get_info(vo.uid)
        vo.tags = await SystemTag.get_tags(vo.tag_ids)
        if channel:
            vo.current_user_subscribed_channel_id = channel.id
            vo.current_user_subscribed  = True
        if not vo.banner:
            vo.banner = "https://irole.network/s/2023-11-08/01HEQW44NAYVPFHZDQDTV2S9SF.jpg"


    return GenericResponseModel(result=vo)


@router.post("/prompt_list",response_model=GenericResponseModel[PromptListResponseModel])
async def list_prompt(request_form:PageRequestModel, uid: str = Depends(get_uid_by_token)) :
    data = await SystemPrompt.find_all().to_list()

    """
         我创建的角色列表
     :param request_form: PageRequestModel
     :param uid: str
     :return: PromptListResponseModel
     """
    skip = (request_form.page - 1) * request_form.pagesize

    limit = request_form.pagesize
    items: List[PromptListItemModel] = []

    sort = (-SystemPrompt.id)


    total = await SystemPrompt.find(filter).count()

    total_page = math.ceil(total / request_form.pagesize)

    objects = await SystemPrompt.find(filter).sort(sort).skip(skip).limit(limit).to_list()
    for item in objects:
        vo = PromptListItemModel(**item.dict())
        items.append(vo)

    response_model = PromptListResponseModel()
    response_model.total = total
    response_model.list = items
    response_model.total_page = total_page
    return GenericResponseModel(result=response_model)



@router.post("/unsubscribe_tool",response_model=GenericResponseModel)
async def unsubscribe_tool(assistant_id: str, tool_id: str, uid: str = Depends(get_uid_by_token)):
    ret = await Assistant.unsubscribe_tool(uid, assistant_id, tool_id)
    return GenericResponseModel()


@router.post("/subscribe_tool",response_model=GenericResponseModel)
async def subscribe_tool(assistant_id: str, tool_id: str, uid: str = Depends(get_uid_by_token)):
    ret = await Assistant.subscribe_tool(uid, assistant_id, tool_id)
    return GenericResponseModel()





@router.post("/trigger_tool",response_model=GenericResponseModel)
async def trigger_tool(assistant_id: str, tool_id: str, uid: str = Depends(get_uid_by_token)):
    ret = await Assistant.subscribe_tool(uid, assistant_id, tool_id)
    return GenericResponseModel()






