from datetime import datetime

import pymongo
from beanie import Document
from bson import ObjectId
from fastapi import UploadFile

from agent.models.tool import Tool
from agent.utils.common import get_unique_id
from pydantic import BaseModel, Field
from agent.models.file_meta import SoldityFileMeta

class TrainFileDataModel(BaseModel):
    assistant_id:str=None
    file:UploadFile


class Knowledge(Document):
    id:str=Field(default_factory=get_unique_id)
    uid:str=""
    assistant_id:str=""
    status:int=0
    file:str=""
    url:str=""
    src_type:str=""
    filename:str=""
    type:str=""
    create_at:datetime=datetime.now()
    update_at:datetime=datetime.now()
    class Settings:
        name = "knowledge"


    class Config:
        json_schema_extra = {
            "example": {
                "uid": "111",
                "assistant_id": "100",
                "file": "bots001",
                "src_type":"file"

            }
        }

class KnowledgeFileRecord(Document):
    uid:str=None
    task_id:str=None
    assistant_id:str=None
    file_path:str=None
    file_digest:str=None
    op:str=None
    status:str="processing"    # processing 处理中， done 完成， fail 失败
    err_msg:str=""
    doc_id:str="" #    api input doc id
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    @classmethod
    async def check_file_digest_exist(cls, uid: str, assistant_id: str, file_digest: str) -> bool:
        query = {
            "file_digest": file_digest,
            "uid": uid,
            "assistant_id": assistant_id
        }
        ret = await cls.find_one(query)
        if ret:
            return True
        return False

    @classmethod
    async def update_status(
                            cls,
                            op: str,
                            task_id: str,
                            assistant_id: str,
                            uid: str,
                            file_digest: str,
                            status: str,
                            err_msg: str = ""
                            ):
        kfr = await cls.find_one(
                                cls.op==op,
                                cls.file_digest == file_digest,
                                cls.uid == uid,
                                cls.task_id == task_id,
                                cls.assistant_id == assistant_id
                                )
        kfr.status = status
        kfr.err_msg = err_msg
        await kfr.save()

    @classmethod
    async def get_status(cls, task_id: str, uid: str, assistant_id: str) -> "KnowledgeFileRecord":
        kfr = await cls.find_one(cls.task_id == task_id, cls.uid==uid, cls.assistant_id==assistant_id)
        if not kfr:
            return 'unknow'
        return kfr.status

    @classmethod
    async def get_doc_ids(cls, uid: str, assistant_id: str) -> list:
        query = {
            "uid": uid,
            "assistant_id": assistant_id,
            "status" : "done"
        }
        kfrs = await cls.find(query).to_list()
        print("kfrs=======>", kfrs)
        doc_ids = [kfr.doc_id for kfr in kfrs]
        print("doc_ids=======>", doc_ids)
        return doc_ids

    class Settings:
        name = "athena_knowledge_file_record"

        # indexes = [
        #     [
        #         {"file_digest": pymongo.TEXT}
        #     ],
        # ]
