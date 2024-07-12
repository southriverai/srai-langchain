import os

from langchain.indexes import VectorstoreIndexCreator
from langchain_community.utilities import ApifyWrapper
from langchain_core.documents import Document
from langchain_openai.embeddings import OpenAIEmbeddings

os.environ["OPENAI_API_KEY"] = "Your OpenAI API key"
os.environ["APIFY_API_TOKEN"] = "Your Apify API token"


if __name__ == "__main__":

    apify = ApifyWrapper()

    loader = apify.call_actor(
        actor_id="apify/website-content-crawler",
        run_input={"startUrls": [{"url": "https://python.langchain.com"}]},
        dataset_mapping_function=lambda item: Document(
            page_content=item["text"] or "", metadata={"source": item["url"]}
        ),
    )

    index = VectorstoreIndexCreator(embedding=OpenAIEmbeddings()).from_loaders([loader])
