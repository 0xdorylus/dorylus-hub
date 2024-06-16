import logging

import httpx as httpx

from agent.models.base import GenericResponseModel
from agent.models.knowledge import KnowledgeFileRecord
from agent.models.brain import TaskForm, AskForm
from agent.utils.file_helper import calc_file_digest
from agent.utils.index_synthesis import new_index_store, new_vector_store, new_docstore
import openai, os

import sys
from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.node_parser import SimpleNodeParser


default_callback_url = "http://127.0.0.1:9301/AI/Inner/submitTask"
class BrainService:
    llm: None

    def request(self,url,data):
        headers = {'x-app': 'athena'}
        response = httpx.post(url, data=data,headers=headers)
        ret = (response.json())
        print(ret)
        logging.info(response.text)
        return ret



    def __init__(self) -> None:
        self.base_storage_path = '/Users/jc/Documents/project/0xBot/0xbot-brains/knowledge-storage'
        # self.base_storage_path = '/deploy/0xbot/knowledge-storage'

    def callback(self, taskForm:TaskForm):
        form = taskForm.dict()
        if taskForm.callback_url:
            # self.callback(taskForm)
            r = self.request(taskForm.callback_url, data=form)
        else:
            r =self.request(default_callback_url, data=form)
        logging.info(r)

    async def check_file_exist(self, uid, assistant_id, file_digest)->bool:
        return await KnowledgeFileRecord.check_file_digest_exist(uid, assistant_id, file_digest)

    async def knowledge_add_gether(self, taskForm:TaskForm)->GenericResponseModel:
        logging.info(taskForm)

        if not os.path.exists(taskForm.file_path):
            print('file not exist')
            return 'file not exist'

        file_digest = calc_file_digest(taskForm.file_path)
        taskForm.file_digest = file_digest
        if  await self.check_file_exist(taskForm.uid, taskForm.assistant_id, file_digest):
            print('file exist')
            self.callback(taskForm)
            return 'file exist'
        
        await KnowledgeFileRecord(
            uid=taskForm.uid,
            file_path=taskForm.file_path,
            file_digest=file_digest,
            task_id=taskForm.task_id,
            doc_id = taskForm.doc_id,
            op=taskForm.op,
            assistant_id=taskForm.assistant_id
        ).create()

        try:
            storage_path = f'{self.base_storage_path}/{taskForm.uid}/{taskForm.assistant_id}'
            documents = SimpleDirectoryReader(input_files=[taskForm.file_path]).load_data()
            parser = SimpleNodeParser.from_defaults(chunk_size=1024, chunk_overlap=20)
            nodes = parser.get_nodes_from_documents(documents)
            if os.path.exists(storage_path + '/docstore.json'):
                print(f"The file '{storage_path}' exists.")
                storage_context = StorageContext.from_defaults(persist_dir=storage_path)
                index = load_index_from_storage(storage_context)
                index.insert_nodes(nodes)
            else:
                print(f"The file '{storage_path}' does not exists.")
                index = GPTVectorStoreIndex(nodes)
            index.storage_context.persist(storage_path)
        except Exception as e:
            print("###Exception=========================>", str(e))
            await KnowledgeFileRecord.update_status(taskForm.op, taskForm.task_id, taskForm.assistant_id, taskForm.uid, file_digest, "fail", str(e))
        else:
            await KnowledgeFileRecord.update_status(taskForm.op, taskForm.task_id, taskForm.assistant_id, taskForm.uid, file_digest, "done")

        logging.info("knowledge_add end .........")

        self.callback(taskForm)

    async def knowledge_add(self, taskForm:TaskForm)->GenericResponseModel:
        logging.info(taskForm)

        if not os.path.exists(taskForm.file_path):
            print('file not exist')
            return 'file not exist'

        file_digest = calc_file_digest(taskForm.file_path)
        taskForm.file_digest = file_digest
        if  await self.check_file_exist(taskForm.uid, taskForm.assistant_id, file_digest):
            print('file exist')
            # self.callback(taskForm)
            return 'file exist'

        await KnowledgeFileRecord(
            uid=taskForm.uid,
            file_path=taskForm.file_path,
            file_digest=file_digest,
            task_id=taskForm.task_id,
            doc_id = taskForm.doc_id,
            op=taskForm.op,
            assistant_id=taskForm.assistant_id
        ).create()

        try:
            storage_path = f'{self.base_storage_path}/{taskForm.uid}/{taskForm.assistant_id}/{taskForm.doc_id}'
            print("###storage_path: ", storage_path)
            file_metadata = lambda x : {"filename": x}
            documents = SimpleDirectoryReader(input_files=[taskForm.file_path], file_metadata=file_metadata).load_data()
            parser = SimpleNodeParser.from_defaults(chunk_size=1024, chunk_overlap=20)
            nodes = parser.get_nodes_from_documents(documents)
            index = GPTVectorStoreIndex(nodes)
            index.storage_context.persist(storage_path)
        except Exception as e:
            print("###Exception=========================>", str(e))
            await KnowledgeFileRecord.update_status(taskForm.op, taskForm.task_id, taskForm.assistant_id, taskForm.uid, file_digest, "fail", str(e))
        else:
            await KnowledgeFileRecord.update_status(taskForm.op, taskForm.task_id, taskForm.assistant_id, taskForm.uid, file_digest, "done")

        logging.info("knowledge_add end .........")

        # self.callback(taskForm)

    def knowledge_update(self, taskForm:TaskForm)->GenericResponseModel:
        logging.info(taskForm)

        self.callback(taskForm)


    def knowledge_del(self, taskForm:TaskForm)->GenericResponseModel:
        logging.info(taskForm)

        self.callback(taskForm)


    async def ask_document(self, askForm:AskForm)->GenericResponseModel:
        print("###askForm: ", askForm)
        if not len(askForm.doc_ids):
            askForm.doc_ids = await KnowledgeFileRecord.get_doc_ids(askForm.uid, askForm.assistant_id)

        storage_path = f'{self.base_storage_path}/{askForm.uid}/{askForm.assistant_id}/'
        persist_dirs = []
        for doc_id in askForm.doc_ids:
            path = storage_path + doc_id
            print("path:", path)
            if os.path.exists(path + '/docstore.json'):
                persist_dirs.append(path)
        # print("persist_dirs:", persist_dirs)

        storage_context = StorageContext.from_defaults()
        storage_context.index_store = new_index_store(persist_dirs)
        storage_context.vector_store = new_vector_store(persist_dirs)
        storage_context.docstore = new_docstore(persist_dirs)
        index = load_index_from_storage(storage_context)
        query_engine = index.as_query_engine()
        response = query_engine.query(askForm.prompt)
        return response.response
        # if os.path.exists(storage_path + '/docstore.json'):
        #     storage_context = StorageContext.from_defaults(persist_dir=storage_path)
        #     index = load_index_from_storage(storage_context)
        #     query_engine = index.as_query_engine(response_mode="tree_summarize")
        #     response = query_engine.query(askForm.prompt)
        #     print(response)
        #     return response.response
        # else:
        #     return 'you have not knowledge base'
        
    async def get_document_status(self, task_id: str, uid: str, assistant_id: str)->GenericResponseModel:
        status = await KnowledgeFileRecord.get_status(task_id, uid, assistant_id)
        print("###get_document_status=>status: ", status)
        return status

    async def get_doc_ids(self, uid: str, assistant_id: str)->list:
        return await KnowledgeFileRecord.get_doc_ids(uid, assistant_id)


    async def ask(self,askForm:AskForm)->GenericResponseModel:
        print("###askForm: ", askForm)
        if not len(askForm.doc_ids):
            askForm.doc_ids = await KnowledgeFileRecord.get_doc_ids(askForm.uid, askForm.assistant_id)

        storage_path = f'{self.base_storage_path}/{askForm.uid}/{askForm.assistant_id}/'
        persist_dirs = []
        for doc_id in askForm.doc_ids:
            path = storage_path + doc_id
            print("path:", path)
            if os.path.exists(path + '/docstore.json'):
                persist_dirs.append(path)
        # print("persist_dirs:", persist_dirs)

        storage_context = StorageContext.from_defaults()
        storage_context.index_store = new_index_store(persist_dirs)
        storage_context.vector_store = new_vector_store(persist_dirs)
        # storage_context.docstore =ry(askForm.prompt)
        # return response.response
        # if os.path.exists(storage_path + '/docstore.json'):
        #     storage_context = StorageContext.from_defaults(persist_dir=storage_path)
        #     index = load_index_from_storage(storage_context)
        #     query_engine = index.as_query_engine(response_mode="tree_summarize")
        #     response = query_engine.query(askForm.prompt)
        #     print(response)
        #     return response.response
        # else:
        #     return 'you have not knowledge base' new_docstore(persist_dirs)
        #         index = load_index_from_storage(storage_context)
        #         query_engine = index.as_query_engine()
        #         response = query_engine.que


    @classmethod
    async def check_user_input(cls,):
        pass