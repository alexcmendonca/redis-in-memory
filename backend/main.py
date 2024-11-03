from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis

# Inicializa o aplicativo FastAPI
app = FastAPI()

# Configura a conexão com o Redis
redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, decode_responses=True)

# Configuração de CORS para permitir acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8001"],  # Permite o frontend local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de dados usando Pydantic
class Quiz(BaseModel):
    quiz_id: str
    title: str
    description: str

class Question(BaseModel):
    quiz_id: str
    question_id: str
    text: str
    options: dict

class ResponseModel(BaseModel):  # Renomeado para evitar conflito com Response do FastAPI
    quiz_id: str
    student_id: str
    question_id: str
    selected_option: str
    response_time: int

# Instancia o QuizManager
from app.quiz_manager import QuizManager
quiz_manager = QuizManager()

@app.get("/")
async def root():
    return {"message": "Bem-vindo ao Sistema Gamificado de Quiz com Redis"}

@app.post("/create_quiz/")
async def create_quiz(quiz: Quiz):
    try:
        quiz_key = f"quiz:{quiz.quiz_id}"
        redis_client.hset(quiz_key, mapping={
            "title": quiz.title,
            "description": quiz.description,
            "created_at": current_timestamp()
        })
        return {"message": "Quiz criado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add_question/")
async def add_question(question: Question):
    try:
        question_key = f"question:{question.question_id}"
        redis_client.hset(question_key, mapping={
            "text": question.text,
            "option_A": question.options.get('A', ''),
            "option_B": question.options.get('B', ''),
            "option_C": question.options.get('C', ''),
            "option_D": question.options.get('D', '')
        })
        redis_client.sadd(f"quiz:{question.quiz_id}:questions", question.question_id)
        return {"message": "Pergunta adicionada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_questions")
async def get_questions(quiz_id: str = Query(...)):
    try:
        question_ids = redis_client.smembers(f"quiz:{quiz_id}:questions")
        questions = []
        for question_id in question_ids:
            question_data = redis_client.hgetall(f"question:{question_id}")
            question = {
                "id": question_id,
                "pergunta": question_data.get("text", ""),
                "options": {
                    "A": question_data.get("option_A", ""),
                    "B": question_data.get("option_B", ""),
                    "C": question_data.get("option_C", ""),
                    "D": question_data.get("option_D", "")
                }
            }
            questions.append(question)
        return questions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/submit_response")
async def submit_response(response: ResponseModel):
    try:
        response_key = f"student_responses:{response.quiz_id}:{response.student_id}"
        redis_client.hset(response_key, response.question_id, response.selected_option)
        redis_client.hincrby(f"votes:{response.question_id}", response.selected_option, 1)
        return {"message": "Resposta registrada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de Estatísticas

@app.get("/quiz/{quiz_id}/questions/{question_id}/most_voted")
async def get_most_voted_option(quiz_id: str, question_id: str):
    try:
        most_voted_option, vote_count = quiz_manager.get_most_voted_option(quiz_id, question_id)
        return {"most_voted_option": most_voted_option, "vote_count": vote_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quiz/{quiz_id}/most_correct_questions")
async def get_most_correct_questions(quiz_id: str):
    try:
        question_id, correct_count = quiz_manager.get_most_correct_questions(quiz_id)
        return {"question_id": question_id, "correct_count": correct_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quiz/{quiz_id}/questions_with_most_abstentions")
async def get_questions_with_most_abstentions(quiz_id: str):
    try:
        question_id, abstentions = quiz_manager.get_questions_with_most_abstentions(quiz_id)
        return {"question_id": question_id, "abstentions": abstentions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quiz/{quiz_id}/average_response_time")
async def get_average_response_time(quiz_id: str):
    try:
        response_times = {question_id: quiz_manager.get_average_response_time(question_id) for question_id in quiz_manager.redis_client.smembers(f"quiz:{quiz_id}:questions")}
        return response_times
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quiz/{quiz_id}/students_with_most_correct_answers")
async def get_students_with_most_correct_answers(quiz_id: str):
    try:
        student_id, correct_count = quiz_manager.get_students_with_most_correct_answers(quiz_id)
        return {"student_id": student_id, "correct_count": correct_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quiz/{quiz_id}/fastest_students")
async def get_fastest_students(quiz_id: str):
    try:
        student_id, response_time = quiz_manager.get_fastest_students(quiz_id)
        return {"student_id": student_id, "response_time": response_time}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def current_timestamp():
    """Retorna o timestamp atual."""
    import time
    return int(time.time())