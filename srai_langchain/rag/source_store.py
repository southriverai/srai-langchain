import datetime
import hashlib
import time
from typing import Dict

from srai_core.store.bytes_store_base import BytesStoreBase
from srai_core.store.document_store_base import DocumentStoreBase


class SourceStore:

    def __init__(self, header_store: DocumentStoreBase, content_store: BytesStoreBase):
        self.header_store = header_store
        self.content_store = content_store

    def create_header(self, source_id: str, source_type: str, source_content: bytes):
        source_timestamp = get_posix_timestamp()
        source_content_hash = hashlib.sha256(source_content).hexdigest()
        dict_header = {
            "source_id": source_id,
            "source_type": source_type,
            "source_timestamp": source_timestamp,
            "source_content_hash": source_content_hash,
        }
        return dict_header

    def save_source_pubmed_db(self, source_id: str, source_bytes: bytes):
        header = self.create_header(source_id, "pubmed_db", source_bytes)
        self.header_store.save_document(source_id, header)
        self.content_store.save_bytes(source_id, source_bytes)

    def save_source_simple_http_get(self, source_id: str, source_url: str, source_bytes: bytes):
        header = self.create_header(source_id, "simple_http_get", source_bytes)
        header["metadata_source_url"] = source_url
        self.header_store.save_document(source_id, header)
        self.content_store.save_bytes(source_id, source_bytes)

    def save_source_crawlee_http_get(self, source_id: str, source_url: str, source_bytes: bytes):
        header = self.create_header(source_id, "crawlee_http_get", source_bytes)
        header["metadata_source_url"] = source_url
        self.header_store.save_document(source_id, header)
        self.content_store.save_bytes(source_id, source_bytes)

    def load_source_content(self, source_id: str) -> bytes:
        return self.content_store.load_bytes(source_id)

    def load_source_content_string(self, source_id: str, encoding="utf-8") -> str:
        return self.content_store.load_bytes(source_id).decode(encoding)

    def load_source_header(self, source_id: str) -> dict:
        return self.header_store.load_document(source_id)

    def load_source_header_all(self) -> Dict[str, dict]:
        return self.header_store.load_document_all()

    def list_source_id(self):
        return self.header_store.load_list_document_id()
