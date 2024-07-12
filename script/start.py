import json
import os

from srai_core.store.database_disk import DatabaseDisk
from srai_core.tools_env import get_string_from_env

from srai_langchain.client_pubmed import ClientPubmed

if __name__ == "__main__":

    pubmed_tool_name = "srai=research-ai"
    pubmed_email = "jaap.oosterbroek@gmail.com"
    jina_api_key = get_string_from_env("JINA_API_KEY")
    query = "New Onset Diabetes"
    database = DatabaseDisk("database", os.path.join("data", "database"))

    client_pubmed = ClientPubmed(pubmed_tool_name, pubmed_email, jina_api_key, database)
    query_status = client_pubmed.status_query_result(query)
    print(json.dumps(query_status, indent=2))
    list_article_txt = client_pubmed.resolve_query_result(query)
