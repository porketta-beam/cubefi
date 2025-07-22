"""Question generation management module"""

from typing import List
from langchain_openai import ChatOpenAI


class QuestionGenerationManager:
    """Question generation and management class"""
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.9):
        self.model_name = model_name
        self.temperature = temperature
        self.llm = None
        self.questions = []
        
    def set_llm(self, model_name: str, temperature: float = 0.9):
        """Set LLM"""
        self.model_name = model_name
        self.temperature = temperature
        self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)
        
    def generate_questions(self, db, num_questions: int = 5) -> List[str]:
        """Generate questions based on documents in DB"""
        try:
            if self.llm is None:
                self.set_llm(self.model_name, self.temperature)
            
            # Get sample documents from DB
            collection = db._collection
            sample_results = collection.get(limit=min(num_questions * 2, 20), include=['documents'])
            
            if not sample_results['documents']:
                raise ValueError("No documents in DB.")
            
            sample_documents = sample_results['documents']
            questions = []
            
            for i in range(num_questions):
                # Rotate through documents
                doc_content = sample_documents[i % len(sample_documents)]
                
                prompt_text = f"""
Generate 1 question based on the following document.
Please output only the question sentence. Write only a complete Korean question format without the expression 'Question:'.

Document content:
{doc_content[:1000]}...
"""
                question = self.llm.invoke(prompt_text).content
                questions.append(question)
            
            self.questions = questions
            return questions
            
        except Exception as e:
            raise Exception(f"Question generation failed: {str(e)}")
    
    def add_question(self, question: str):
        """Add question"""
        self.questions.append(question)
        
    def remove_question(self, index: int):
        """Remove question"""
        if 0 <= index < len(self.questions):
            self.questions.pop(index)
            
    def update_question(self, index: int, question: str):
        """Update question"""
        if 0 <= index < len(self.questions):
            self.questions[index] = question
            
    def get_questions(self) -> List[str]:
        """Get current question list"""
        return self.questions.copy()
    
    def clear_questions(self):
        """Clear all questions"""
        self.questions = []