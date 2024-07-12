import hashlib
import os

from langchain_text_splitters import CharacterTextSplitter
from markdownify import markdownify
from openai import Client
from pinecone import Pinecone, Vector
from srai_core.store.database_disk import DatabaseDisk
from srai_core.tools_env import get_string_from_env
from tqdm import tqdm

from srai_langchain.rag.source_store import SourceStore

if __name__ == "__main__":

    database = DatabaseDisk("database", os.path.join("data", "database"))
    client_pinecone = Pinecone(api_key=get_string_from_env("PINECONE_API_KEY"))
    client_openai = Client(api_key=get_string_from_env("OPENAI_API_KEY"))
    index_name = "rag"
    index = None
    for index in client_pinecone.list_indexes():
        print(index.name)
        if index.name == index_name:
            break
    if index is None:
        raise ValueError(f"Index {index_name} not found")

    index = client_pinecone.Index(index_name)
    query_store = database.get_document_store("query")
    article_status_store = database.get_document_store("article_status")
    source_header_store = database.get_document_store("source_header")
    source_content_store = database.get_bytes_store("source_content")
    source_store = SourceStore(source_header_store, source_content_store)  # TODO move source store to its own library
    source_store.list_source_id()

    for source_id in tqdm(source_store.list_source_id()):
        list_vector = []
        header = source_store.load_source_header(source_id)
        if "metadata_source_url" not in header:
            continue
        if "nomad" in header["metadata_source_url"]:
            print(header["metadata_source_url"])
        else:
            continue

        source_url = header["metadata_source_url"]
        source_content_hash = header["source_content_hash"]
        source = source_store.load_source_content_string(source_id)
        # markdownify
        source = markdownify(source)

        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        list_chunk = text_splitter.split_text(source)
        dict_chunk = {}
        for chunk in list_chunk:
            chunk_content_hash = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
            dict_chunk[chunk_content_hash] = chunk
        list_chunk_id = list(dict_chunk.keys())
        fetch_response = index.fetch(ids=list_chunk_id)

        for chunk_content_hash, chunk in dict_chunk.items():
            if chunk_content_hash in fetch_response.vectors:
                continue

            embedding = client_openai.embeddings.create(input=chunk, model="text-embedding-ada-002").data[0].embedding
            metadata = {
                "source_id": source_id,
                "text": chunk,
                "source_content_hash": source_content_hash,
                "chunk_content_hash": chunk_content_hash,
                "url_root": "https://www.banskonomad.com/",
                "url": source_url,
            }
            list_vector.append(Vector(id=chunk_content_hash, values=embedding, metadata=metadata))
        print(len(list_vector))
        if len(list_vector) > 0:
            index.upsert(list_vector)
