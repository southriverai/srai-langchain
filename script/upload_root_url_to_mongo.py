from typing import List

from pinecone import Pinecone
from srai_core.store.database_mongo import DatabaseMongo
from srai_core.tools_env import get_string_from_env

# collect all the root_url for the pinecone metadata


if __name__ == "__main__":
    # collect_root_url

    pinecone_api_key = get_string_from_env("PINECONE_API_KEY")
    mongodb_connection_string = get_string_from_env("MONGODB_CONNECTION_STRING")
    client_pinecone = Pinecone(api_key=pinecone_api_key)
    database = DatabaseMongo("askurl", mongodb_connection_string)
    document_store = database.get_document_store("rag_agent_header")
    # TODO check current
    if document_store.exists_document("all"):
        print(document_store.load_document("all"))
    else:
        print("not found")
    index = client_pinecone.Index("rag")
    root_urls = []
    list_chunk_id: List[str] = list(index.list())[0]  # type: ignore

    dict_url_root = {}
    for i in range(0, len(list_chunk_id), 10):
        list_chunk_id_part = list_chunk_id[i : i + 10]

        fetch_response = index.fetch(ids=list_chunk_id_part)

        for value in fetch_response.vectors.values():
            dict_metadata = value.metadata
            if "url_root" in dict_metadata:
                url_root = dict_metadata["url_root"]
                dict_url_root[url_root] = True
    list_url_root = list(dict_url_root.keys())
    print(list_url_root)

    rag_agent_id = "all"
    document = {"rag_agent_id": rag_agent_id, "list_url_root": ["http://www.av.vc/"]}
    document_store.save_document(rag_agent_id, {"url": document})
