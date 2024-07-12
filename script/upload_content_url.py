import hashlib
import os

import requests
from langchain_text_splitters import CharacterTextSplitter
from openai import Client
from pinecone import Pinecone, Vector
from srai_core.store.database_disk import DatabaseDisk
from srai_core.tools_env import get_string_from_env
from tqdm import tqdm

# TODO MarkdownTextSplitter


# def get_embeddings(text):
#     response = openai.Embedding.create(input=text, model="text-embedding-ada-002")  # Example embedding model
#     return response["data"][0]["embedding"]
def scrape_url(url) -> str:
    jina_header = {}
    url_md = f"https://r.jina.ai/{url}"
    response = requests.get(url_md, headers=jina_header)

    if response.status_code != 200:
        print(f"Failed to fetch HTML {response.status_code}")
        print(response.text)
        raise ValueError(f"Failed to fetch HTML {response.status_code}")
    else:
        return response.text


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
    list_url = []
    list_url.append("https://en.wikipedia.org/wiki/soviet_union")
    list_url.append("https://en.wikipedia.org/wiki/nuclear_fusion")
    for url in tqdm(list_url):

        source_content: str = scrape_url(url)
        source_content_hash = hashlib.sha256(source_content.encode("utf-8")).hexdigest()
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        list_chunk = text_splitter.split_text(source_content)
        dict_chunk = {}
        for chunk in list_chunk:
            chunk_content_hash = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
            dict_chunk[chunk_content_hash] = chunk
        list_chunk_id = list(dict_chunk.keys())
        list_chunk_present = []
        for i in range(0, len(list_chunk_id), 10):
            fetch_response = index.fetch(ids=list_chunk_id[i : i + 10])
            list_chunk_present.extend(fetch_response.vectors.keys())
        print(f"out of {len(list_chunk)} we found {len(list_chunk_present)}")

        list_vector = []
        for chunk_content_hash, chunk in dict_chunk.items():
            if chunk_content_hash in list_chunk_present:
                continue
            try:
                embedding = (
                    client_openai.embeddings.create(input=chunk, model="text-embedding-ada-002").data[0].embedding
                )
            except Exception:
                continue
            metadata = {
                "text": chunk,
                "source_content_hash": source_content_hash,
                "chunk_content_hash": chunk_content_hash,
                "url_root": url.lower(),
                "url": url.lower(),
            }
            list_vector.append(Vector(id=chunk_content_hash, values=embedding, metadata=metadata))
        print(len(list_vector))
        if len(list_vector) > 0:
            if len(list_vector) > 10:
                for i in range(0, len(list_vector), 10):
                    index.upsert(list_vector[i : i + 10])
            else:

                index.upsert(list_vector)
