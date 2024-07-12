import pickle as pkl
from typing import Optional

from langchain.memory import ConversationBufferMemory
from srai_core.store.bytes_store_base import BytesStoreBase


class CbmStore:
    def __init__(self, bytes_store: BytesStoreBase):
        self.bytes_store = bytes_store

    def try_load_cbm(self, cdm_id) -> Optional[ConversationBufferMemory]:
        try:
            return self.load_cbm(cdm_id)
        except Exception:
            return None

    def load_cbm(self, cdm_id) -> ConversationBufferMemory:
        return pkl.loads(self.bytes_store.load_bytes(cdm_id))

    def save_cbm(
        self,
        cdm_id: str,
        cfm: ConversationBufferMemory,
    ) -> None:
        self.bytes_store.save_bytes(cdm_id, pkl.dumps(cfm))
