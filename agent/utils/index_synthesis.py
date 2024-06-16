
import json
from llama_index.vector_stores.simple import SimpleVectorStore
from llama_index.storage.docstore.simple_docstore import SimpleDocumentStore
from llama_index.storage.index_store.simple_index_store import SimpleIndexStore

def new_index_store(persist_dirs):
    new_index_store_dict= SimpleIndexStore.from_persist_dir(persist_dirs[0]).to_dict()
    new_index_id = list(new_index_store_dict["index_store/data"].keys())[0]
    new_index_store_dict["index_store/data"][new_index_id]["__data__"] = json.loads(new_index_store_dict["index_store/data"][new_index_id]["__data__"])
    for i in range(1, len(persist_dirs)):
        index_store_dict = SimpleIndexStore.from_persist_dir(persist_dirs[i]).to_dict()
        index_id = list(index_store_dict["index_store/data"].keys())[0]
        # print("#index_id: ", index_id)
        new_index_store_dict["index_store/data"][new_index_id]["__data__"]["nodes_dict"] = {
            **new_index_store_dict["index_store/data"][new_index_id]["__data__"]["nodes_dict"],
            **json.loads(index_store_dict["index_store/data"][index_id]["__data__"])["nodes_dict"]
            }
    # print(new_index_store_dict)
    return SimpleIndexStore.from_dict(new_index_store_dict)

def new_vector_store(persist_dirs):
    new_vector_store = SimpleVectorStore.from_persist_dir(persist_dirs[0]).to_dict()
    for i in range(1, len(persist_dirs)):
        vector_store = SimpleVectorStore.from_persist_dir(persist_dirs[i]).to_dict()
        new_vector_store["embedding_dict"] = {**new_vector_store["embedding_dict"],**vector_store["embedding_dict"]}
        new_vector_store["text_id_to_ref_doc_id"] = {**new_vector_store["text_id_to_ref_doc_id"],**vector_store["text_id_to_ref_doc_id"]}
    # print('new_vector_store============>', new_vector_store)
    return SimpleVectorStore.from_dict(new_vector_store)

def new_docstore(persist_dirs):
    new_docstore = SimpleDocumentStore.from_persist_dir(persist_dirs[0]).to_dict()
    for i in range(1, len(persist_dirs)):
        docstore = SimpleDocumentStore.from_persist_dir(persist_dirs[i]).to_dict()
        new_docstore["docstore/data"] = {**new_docstore["docstore/data"], **docstore["docstore/data"]}
        new_docstore["docstore/ref_doc_info"] = {**new_docstore["docstore/ref_doc_info"], **docstore["docstore/ref_doc_info"]}
        new_docstore["docstore/metadata"] = {**new_docstore["docstore/metadata"], **docstore["docstore/metadata"]}

    # print('new_docstore============>', new_docstore)
    return SimpleDocumentStore.from_dict(new_docstore)



# new_docstore(['./storage-test/yitian', './storage-test/yizhou'])
