from pydantic import BaseModel, Field
from typing import List
import os
import json
from anthropic import Anthropic

class QuizQuestion(BaseModel):
    question: str = Field(description="The quiz question")
    options: List[str] = Field(description="Four possible answers")
    correct_answer: int = Field(description="Index of the correct answer (0-3)")

class QuizList(BaseModel):
    questions: List[QuizQuestion] = Field(description="A list of quiz questions generated from the text")

class QuizGenerator:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        
        self.client = Anthropic(api_key=api_key)
        # Using Claude 3 Sonnet (widely available)
        self.model = "claude-sonnet-4-5-20250929"

    def generate_quiz(self, transcript_text: str, language: str = "en") -> List[QuizQuestion]:
        prompt = f"""
        You are an expert educational content creator. Your task is to create effective multiple-choice quiz questions from the provided video transcript.
        
        Target Language: {language}
        
        Transcript:
        {transcript_text}
        
        Generate 5-10 high-quality multiple-choice questions that test understanding of the key concepts and important details from the transcript.
        The questions and answers should be in the target language specified above.
        Each question must have:
        - A clear 'question'
        - Exactly 4 'options' (possible answers)
        - The 'correct_answer' as an index (0-3) indicating which option is correct
        
        Make the questions engaging and the incorrect options plausible but clearly wrong to someone who understood the content.
        
        Return the result as a VALID JSON object with a "questions" key containing a list of objects, each with "question", "options", and "correct_answer" keys.
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
            questions_data = data.get("questions", [])
            
            return [QuizQuestion(**item) for item in questions_data]
            
        except Exception as e:
            print(f"Error generating quiz: {e}")
            raise e
