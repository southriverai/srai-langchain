from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_core.vectorstores import VectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone.vectorstores import PineconeVectorStore
from srai_core.tools_env import get_string_from_env


def prompt(memory: ConversationBufferMemory, vector_store: VectorStore, prompt: str) -> str:
    llm = ChatOpenAI(temperature=0.7, model="gpt-4")

    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm, chain_type="stuff", retriever=vector_store.as_retriever(), memory=memory
    )
    result = conversation_chain.invoke({"question": prompt, "chat_history": ""}, chat_history={"history": ""})
    return result["answer"]


if __name__ == "__main__":

    embedding = OpenAIEmbeddings()
    vector_store = PineconeVectorStore(
        index_name="rag", embedding=embedding, pinecone_api_key=get_string_from_env("PINECONE_API_KEY")
    )

    # vector_store = PineconeVectorStore.from_documents(index_name="rag", embedding=embedding)
    # print(vectorstore.from_texts(texts=["Hello, world!"], index_name="rag", embedding=embedding))

    # memory = ConversationBufferMemory()
    # print(prompt(memory, vector_store, "what is new onset diabetes"))

    # from langchain.chains import RetrievalQA

    # llm = ChatOpenAI(api_key=get_string_from_env("OPENAI_API_KEY"), model="gpt-4", temperature=0.0)  # type: ignore
    # retriever = vector_store.as_retriever()
    # print(retriever.invoke("what is new onset diabetes?"))

    # # = vector_store.invocation_retriever(retriever)
    # qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=vector_store.as_retriever())
    # print(type(qa.invoke("what is new onset diabetes?")))

    # print(qa.invoke("what is new onset diabetes?"))
