import asyncio
import hashlib
import os
from typing import List

from crawlee.playwright_crawler.playwright_crawler import PlaywrightCrawler
from crawlee.playwright_crawler.types import PlaywrightCrawlingContext
from srai_core.store.database_disk import DatabaseDisk

from srai_langchain.rag.source_store import SourceStore


async def main(source_store: SourceStore, list_url: List[str], scrape_count: int) -> None:

    crawler = PlaywrightCrawler(
        # Limit the crawl to max requests. Remove or increase it for crawling all links.
        max_requests_per_crawl=scrape_count,
    )

    # Define the default request handler, which will be called for every request.
    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        context.log.info(f"Processing {context.request.url} ...")

        # Extract data from the page.
        data = {
            "url": context.request.url,
            "content": await context.page.content(),
        }
        # hash the url
        source_id = hashlib.sha256(data["url"].encode()).hexdigest()
        source_store.save_source_crawlee_http_get(source_id, data["url"], data["content"].encode("utf-8"))

        # Push the extracted data to the default dataset.
        await context.push_data(data)

        # Enqueue all links found on the page.
        await context.enqueue_links()

    # Run the crawler with the initial list of requests.
    await crawler.run(list_url)


if __name__ == "__main__":

    database = DatabaseDisk("database", os.path.join("data", "database"))
    source_store = SourceStore(database.get_document_store("source_header"), database.get_bytes_store("source_content"))
    # list_url = ["http://www.av.vc/"]
    list_url = ["https://www.banskonomad.com/"]
    asyncio.run(main(source_store, list_url, 1000))
    for header in source_store.load_source_header_all().values():
        if header["source_type"] == "crawlee_http_get":
            if "metadata_source_url" in header:
                if "nomad" in header["metadata_source_url"]:
                    print(header["metadata_source_url"])
