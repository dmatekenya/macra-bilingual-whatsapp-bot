from langchain_openai import ChatOpenAI
from src.config import settings
from src.prompts.qa_prompt import QA_SYSTEM_PROMPT
from src.services.retrieval import Retriever


class QAService:
    def __init__(self) -> None:
        self.retriever = Retriever()
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_chat_model,
            temperature=0.2,
        )

    def answer_question(self, question: str) -> str:
        retrieved = self.retriever.search(question)

        context = "\n\n".join(
            [f"[Context {i+1}]\n{chunk}" for i, chunk in enumerate(retrieved.answer_contexts)]
        )

        user_prompt = f"""
User question:
{question}

Retrieved context:
{context}

Answer the user using only the retrieved context where possible.
"""

        response = self.llm.invoke(
            [
                ("system", QA_SYSTEM_PROMPT),
                ("user", user_prompt),
            ]
        )
        return response.content