import hashlib
import json
from typing import Literal, Optional

# import markdownify
import requests
from pymed import PubMed
from pymed.article import PubMedArticle
from srai_core.store.database_base import DatabaseBase

from srai_langchain.rag.source_store import SourceStore


class ClientPubmed:
    # TODO move to its own library
    def __init__(self, tool_name: str, email: str, jina_api_key: str, database: DatabaseBase):
        self.tool_name = tool_name
        self.email = email
        self.jina_api_key = jina_api_key
        # self.jina_header = {"Authorization": f"Bearer {jina_api_key}"}
        self.jina_header = {}

        self.query_store = database.get_document_store("query")
        self.article_status_store = database.get_document_store("article_status")
        self.source_header_store = database.get_document_store("source_header")
        self.source_content_store = database.get_bytes_store("source_content")
        self.source_store = SourceStore(
            self.source_header_store, self.source_content_store
        )  # TODO move source store to its own library

    def resolve_query_pubmed(self, query: str):
        query_id = hashlib.sha256(query.encode()).hexdigest()
        query_result = self.query_store.try_load_document(query_id)
        if query_result is not None:
            print(f"Query found returning cache {query_id}")
            return query_result

        print(f"Query not found {query_id} fetching from PubMed")
        pubmed = PubMed(tool=self.tool_name, email=self.email)
        total_result_count = pubmed.getTotalResultsCount(query)
        results = pubmed.query("New Onset Diabetes", max_results=500)
        list_article_reference = []
        for result in results:
            if type(result) is PubMedArticle:
                article: PubMedArticle = result
                article_reference_json = article.toJSON()
                article_reference_dict = json.loads(article_reference_json)
                list_article_reference.append(article_reference_dict)

        query_result = {
            "query": query,
            "query_id": query_id,
            "total_result_count": total_result_count,
            "list_article_reference": list_article_reference,
        }
        self.query_store.save_document(query_id, query_result)
        return query_result

    def markdownify_article_reference_abstract(self, article_reference: dict) -> str:
        # TODO make it look like https://r.jina.ai/https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11219943/?report=printable
        title = article_reference["title"]
        list_author = article_reference["authors"]
        abstract = article_reference["abstract"]

        markdown_txt = f"# {title}\n\n"
        markdown_txt += "## Authors\n\n"
        for author in list_author:
            markdown_txt += f"- {author}\n\n"

        markdown_txt += f"## Abstract\n\n{abstract}\n\n"
        return markdown_txt

    def get_pubmed_id_to_pmc_id(self, pubmed_id: str) -> Optional[str]:
        print(f"Resolving PMC ID for {pubmed_id}")

        url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?tool={self.tool_name}&email={self.email}&ids={pubmed_id}&format=json"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch PMC ID {response.status_code}")
            return None
        else:
            for record in response.json()["records"]:
                if "live" in record:
                    if record["live"] == "false":
                        return None
                if record["pmcid"] is not None:
                    return record["pmcid"]
            return None

            # pas

    def resolve_article_reference(self, article_reference: dict) -> Optional[str]:
        article_doi = article_reference["doi"]
        if article_doi is None:
            print("No DOI found in article reference")
            return None
        list_article_doi = article_reference["doi"].split("\n")
        print(list_article_doi[0])
        article_id = hashlib.sha256(list_article_doi[0].encode()).hexdigest()

        article_status = self.article_status_store.try_load_document(article_id)

        if article_status is not None:
            if article_status["status"] == "failed-no-absract":
                return None
            elif article_status["status"] == "abstract-no-pmc-id":
                return self.source_store.load_source(article_id).decode("utf-8")
            elif article_status["status"] == "fulltext-md":
                return self.source_store.load_source(article_id).decode("utf-8")
            elif article_status["status"] == "failed-with-pmc-id":
                print("retrying")
            else:
                raise ValueError(f"Unknown status {article_status['status']}")

        article_status = self.resolve_article_pubmed_md(
            article_id,
            article_reference,
        )
        article_status = {"status": article_status}
        self.article_status_store.save_document(article_id, article_status)

    def resolve_article_pubmed_md(
        self,
        article_id: str,
        article_reference: dict,
    ) -> Literal["fulltext-md", "abstract-no-pmc-id", "failed-no-absract", "failed-with-pmc-id"]:

        pubmed_id = article_reference["pubmed_id"].split("\n")[0]

        print(f"Resolving article {pubmed_id}")
        # url_pubmed = f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}"  # TODO use this for pdf
        pmc_id = self.get_pubmed_id_to_pmc_id(pubmed_id)
        if pmc_id is None:
            print(f"Failed to resolve PMC ID for {pubmed_id}")
            if article_reference["abstract"] is None:
                return "failed-no-absract"
            markdown = self.markdownify_article_reference_abstract(article_reference)
            self.source_store.save_source_pubmed_db(article_id, markdown.encode("utf-8"))
            return "abstract-no-pmc-id"

        url_pmc = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/?report=printable"
        url_pmc_md = f"https://r.jina.ai/{url_pmc}"

        response = requests.get(url_pmc_md, headers=self.jina_header)
        if response.status_code != 200:
            print(f"Failed to fetch HTML {response.status_code}")
            print(response.text)
            return "failed-with-pmc-id"
        self.source_store.save_source_simple_http_get(article_id, url_pmc_md, response.content)

        return "fulltext-md"

    def resolve_query_result(self, query: str) -> list[str]:
        query_result = self.resolve_query_pubmed(query)
        list_article_str = []
        for article_reference in query_result["list_article_reference"]:
            article_str = self.resolve_article_reference(article_reference)
            if article_str is not None:
                list_article_str.append(article_str)
        return list_article_str

    def status_query_result(self, query: str):
        query_result = self.resolve_query_pubmed(query)
        total_result_count = query_result["total_result_count"]
        article_reference_count = len(query_result["list_article_reference"])

        no_doi_count = 0
        no_status_count = 0
        fulltext_md_count = 0
        astract_md_count = 0
        failed_no_abstract_count = 0
        failed_with_pmc_id_count = 0
        for article_reference in query_result["list_article_reference"]:
            article_doi = article_reference["doi"]
            if article_doi is None:
                no_doi_count += 1
                continue
            list_article_doi = article_doi.split("\n")
            article_id = hashlib.sha256(list_article_doi[0].encode()).hexdigest()
            article_status = self.article_status_store.try_load_document(article_id)
            if article_status is None:
                no_status_count += 1
            else:
                if article_status["status"] == "fulltext-md":
                    fulltext_md_count += 1
                elif article_status["status"] == "abstract-no-pmc-id":
                    astract_md_count += 1
                elif article_status["status"] == "failed-no-absract":
                    failed_no_abstract_count += 1
                elif article_status["status"] == "failed-with-pmc-id":
                    failed_with_pmc_id_count += 1
                else:
                    raise ValueError(f"Unknown status {article_status['status']}")

        query_status = {
            "query": query,
            "query_id": query_result["query_id"],
            "total_result_count": total_result_count,
            "article_reference_count": article_reference_count,
            "fulltext_md_count": fulltext_md_count,
            "astract_md_count": astract_md_count,
            "failed_no_abstract_count": failed_no_abstract_count,
            "failed_with_pmc_id_count": failed_with_pmc_id_count,
        }
        return query_status
