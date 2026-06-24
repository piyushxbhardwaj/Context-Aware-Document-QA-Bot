class BaseLLM:
    """Base abstract client interface for LLMs."""
    
    def generate_answer(self, question: str, context: str) -> str:
        """Generates an answer from context strictly."""
        raise NotImplementedError("Subclasses must implement generate_answer()")
