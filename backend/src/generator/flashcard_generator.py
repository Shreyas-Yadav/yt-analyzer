from pydantic import BaseModel, Field
from typing import List
import os
from llama_index.llms.anthropic import Anthropic
from llama_index.core.program import LLMTextCompletionProgram

class FlashcardItem(BaseModel):
    front: str = Field(description="The question or concept on the front of the flashcard")
    back: str = Field(description="The answer or explanation on the back of the flashcard")

class FlashcardList(BaseModel):
    flashcards: List[FlashcardItem] = Field(description="A list of flashcards generated from the text")

class FlashcardGenerator:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        
        self.llm = Anthropic(model="claude-sonnet-4-5-20250929", api_key=api_key, max_tokens=10240)

    def generate_flashcards(self, transcript_text: str, language: str = "en") -> List[FlashcardItem]:
        prompt_template_str = """
        You are an expert educational content creator. Your task is to create effective flashcards from the provided video transcript.
        
        Target Language: {language}
        
        Transcript:
        {transcript_text}
        
        Generate 5-10 high-quality flashcards that cover the key concepts and important details from the transcript.
        The flashcards should be in the target language specified above.
        Each flashcard must have a 'front' (question/concept) and a 'back' (answer/explanation).
        """

        program = LLMTextCompletionProgram.from_defaults(
            output_cls=FlashcardList,
            llm=self.llm,
            prompt_template_str=prompt_template_str,
            verbose=True
        )

        output = program(transcript_text=transcript_text, language=language)
        return output.flashcards
