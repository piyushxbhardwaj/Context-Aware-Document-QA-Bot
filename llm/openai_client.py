from openai import OpenAI
from llm.base import BaseLLM
from app.config import settings

class OpenAILLM(BaseLLM):
    """
    OpenAI Chat Completion Client. Configures and calls OpenAI models to obtain context-constrained responses.
    """
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment or settings.")
        self.model = model or settings.OPENAI_MODEL
        self.client = OpenAI(api_key=self.api_key)

    def generate_answer(self, question: str, context: str) -> str:
        prompt = self._build_prompt(question, context)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        return response.choices[0].message.content.strip()

    def _build_prompt(self, question: str, context: str) -> str:
        return f"""You are an advanced context-aware assistant. You must answer the user's question strictly based on the provided context.
If the answer cannot be found in the context, you must answer exactly: "This information is not available in the provided documents."
Do not make up information or use any external knowledge.

Context:
{context}

Question:
{question}

Answer:"""
