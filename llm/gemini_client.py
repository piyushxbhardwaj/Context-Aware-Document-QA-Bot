import google.generativeai as genai
from llm.base import BaseLLM
from app.config import settings

class GeminiLLM(BaseLLM):
    """
    Google Gemini Client. Configures and calls the Gemini API to obtain context-constrained responses.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment or settings.")
        genai.configure(api_key=self.api_key)
        # Use gemini-1.5-flash as default fast model
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def generate_answer(self, question: str, context: str) -> str:
        prompt = self._build_prompt(question, context)
        response = self.model.generate_content(
            prompt,
            generation_config={"temperature": 0.0}
        )
        return response.text.strip()

    def _build_prompt(self, question: str, context: str) -> str:
        return f"""You are an advanced context-aware assistant. You must answer the user's question strictly based on the provided context.
If the answer cannot be found in the context, you must answer exactly: "This information is not available in the provided documents."
Do not make up information or use any external knowledge.

Context:
{context}

Question:
{question}

Answer:"""
