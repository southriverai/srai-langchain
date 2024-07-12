import os

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from srai_core.store.bytes_store_base import BytesStoreBase
from srai_core.store.document_store_base import DocumentStoreBase

from srai_langchain.rag.cbm_store import CbmStore


class AgentRag:

    def __init__(
        self,
        path_dir_vectorstore: str,
        cbm_store: CbmStore,
        document_store_source: DocumentStoreBase,
        bytes_store_source: BytesStoreBase,
        bytes_store_list_page: BytesStoreBase,
    ):
        self.path_dir_vectorstore = path_dir_vectorstore
        self.cbm_store = cbm_store
        self.document_store_source = document_store_source
        self.bytes_store_source = document_store_source

        if not os.path.exists(self.path_dir_vectorstore):
            os.makedirs(self.path_dir_vectorstore)

        self.list_path_file_pdf = []
        self.list_path_file_txt = []
        self.text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

        # Create vector store
        embeddings = OpenAIEmbeddings()
        if not os.path.isfile(os.path.join(path_dir_vectorstore, "index.pkl")):
            self.rebuild_vectorstore()
        else:
            self.vectorstore = FAISS.load_local(
                path_dir_vectorstore,
                embeddings=embeddings,
                allow_dangerous_deserialization=True,
            )
        # Create conversation chain
        self.llm = ChatOpenAI(temperature=0.7, model="gpt-4")

    def rebuild_vectorstore(self):
        list_page = []
        for path_file in self.list_path_file_pdf:
            loader = PyPDFLoader(file_path=path_file)
            list_page.extend(loader.load_and_split(self.text_splitter))
        for path_file in self.list_path_file_txt:
            loader = TextLoader(file_path=path_file)
            list_page.extend(loader.load_and_split(self.text_splitter))

        self.vectorstore = FAISS.from_documents(list_page, embedding=OpenAIEmbeddings())
        self.vectorstore.save_local(self.path_dir_vectorstore)

    def add_path_file_pdf(self, path_file: str):

        self.bytes_store_pdf.save_bytes(path_file, b"")
        self.list_path_file_pdf.append(path_file)

    def add_path_file_txt(self, path_file: str):
        self.list_path_file_txt.append(path_file)

    def prompt(self, chat_id: str, prompt: str) -> str:
        memory = self.cbm_store.try_load_cbm(chat_id)
        if memory is None:
            memory = ConversationBufferMemory()
        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm, chain_type="stuff", retriever=self.vectorstore.as_retriever(), memory=memory
        )
        result = conversation_chain.invoke({"question": prompt})
        self.cbm_store.save_cbm(chat_id, conversation_chain.memory)
        return result["answer"]
