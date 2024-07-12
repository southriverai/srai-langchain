import os
from typing import Dict, List

from langchain.vectorstores import VectorStore
from srai_core.store.document_store_base import DocumentStoreBase


class VectorStoreManager:

    def __init__(
        self,
        path_dir_vectorstore_root: str,
        document_store_vector_store: DocumentStoreBase,
    ) -> None:
        self.path_dir_vectorstore_root = path_dir_vectorstore_root
        self.dict_vectorstore: Dict[str, VectorStore] = {}  # TODO vector_stores should be idempotent

    def load_vector_store(
        self,
        vector_store_id: str,
    ) -> VectorStore:
        path_dir_vectorstore_target = os.path.join(self.path_dir_vectorstore_root, vector_store_id)
        #
        if not os.path.isfile(os.path.join(path_dir_vectorstore_target, "index.pkl")):
            return None

        self.vectorstore = FAISS.load_local(
            path_dir_vectorstore_target,
            embeddings=embeddings,
            allow_dangerous_deserialization=True,
        )

    def create_vector_store_for_list_document_id(
        self,
        list_document_id: List[str],
    ) -> None:
        embeddings = OpenAIEmbeddings()
        vector_store = FAISS.load_local(
            path_dir_vectorstore_target,
            embeddings=embeddings,
            allow_dangerous_deserialization=True,
        )
