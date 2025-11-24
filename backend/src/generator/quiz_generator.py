from pydantic import BaseModel, Field
from typing import List
import os
from llama_index.llms.anthropic import Anthropic
from llama_index.core.program import LLMTextCompletionProgram

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
        
        self.llm = Anthropic(model="claude-sonnet-4-5-20250929", api_key=api_key, max_tokens=10240)

    def generate_quiz(self, transcript_text: str, language: str = "en") -> List[QuizQuestion]:
        prompt_template_str = """
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
        """

        program = LLMTextCompletionProgram.from_defaults(
            output_cls=QuizList,
            llm=self.llm,
            prompt_template_str=prompt_template_str,
            verbose=True
        )

        output = program(transcript_text=transcript_text, language=language)
        return output.questions
