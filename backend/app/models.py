# models.py

from pydantic import BaseModel, Field
from typing import Dict, Optional

class Question(BaseModel):
    id: str = Field(..., description="ID único da pergunta")
    text: str = Field(..., description="Texto da pergunta")
    options: Dict[str, str] = Field(..., description="Dicionário de opções de resposta")

class Response(BaseModel):
    student_id: str = Field(..., description="ID único do aluno")
    question_id: str = Field(..., description="ID da pergunta respondida")
    selected_option: Optional[str] = Field(None, description="Opção selecionada pelo aluno")
    response_time: int = Field(..., description="Tempo de resposta em segundos")
    answered_in_time: bool = Field(..., description="Indica se a resposta foi dada dentro do tempo limite")

# Exemplo de uso
response = Response(
    student_id="student_1",
    question_id="q1",
    selected_option=None,  # Nenhuma opção selecionada
    response_time=20,  # Tempo máximo atingido
    answered_in_time=False  # Indica que não foi respondido a tempo
)