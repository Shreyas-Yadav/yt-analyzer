from pydantic import BaseModel, Field
from typing import List
import os
import json
from anthropic import Anthropic

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
        
        self.client = Anthropic(api_key=api_key)
        # Using Claude 3 Sonnet (widely available)
        self.model = "claude-sonnet-4-5-20250929"

    def generate_flashcards(self, transcript_text: str, language: str = "en") -> List[FlashcardItem]:
        prompt = f"""
        You are an expert educational content creator. Your task is to create effective flashcards from the provided video transcript.
        
        Target Language: {language}
        
        Transcript:
        {transcript_text}
        
        Generate 5-10 high-quality flashcards that cover the key concepts and important details from the transcript.
        The flashcards should be in the target language specified above.
        
        Return the result as a VALID JSON object with a "flashcards" key containing a list of objects, each with "front" and "back" keys.
        Do not include any other text, explanations, or markdown formatting. Just the JSON.
        """

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text.strip()
            
            # Clean up potential markdown code blocks if the model includes them
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            flashcards_data = data.get("flashcards", [])
            
            return [FlashcardItem(**item) for item in flashcards_data]
            
        except Exception as e:
            print(f"Error generating flashcards: {e}")
            # Return empty list or re-raise depending on desired behavior. 
            # Re-raising to let the caller handle the error (which returns 500)
            raise e
