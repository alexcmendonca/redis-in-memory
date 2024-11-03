from fastapi import APIRouter, HTTPException
from app.quiz_manager import QuizManager
import redis

quiz_router = APIRouter()
quiz_manager = QuizManager()

# Configuração explícita para Redis em 127.0.0.1:6379
redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, decode_responses=True)

# Criação e gerenciamento de quizzes
@quiz_router.post("/quizzes/")
async def create_quiz(quiz_id: str, title: str, description: str):
    try:
        quiz_manager.create_quiz(quiz_id, title, description)
        return {"message": "Quiz created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@quiz_router.post("/quizzes/{quiz_id}/questions/")
async def add_question(quiz_id: str, question_id: str, text: str, options: dict):
    try:
        quiz_manager.add_question(quiz_id, question_id, text, options)
        return {"message": "Question added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@quiz_router.post("/quizzes/{quiz_id}/responses/")
async def record_response(quiz_id: str, student_id: str, question_id: str, selected_option: str):
    try:
        quiz_manager.record_response(quiz_id, student_id, question_id, selected_option)
        return {"message": "Response recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Consulta de perguntas
@quiz_router.get("/quizzes/{quiz_id}/questions/")
def get_questions(quiz_id: str):
    try:
        question_keys = redis_client.keys(f"quiz:{quiz_id}:questions:*")
        questions = []
        for key in question_keys:
            question_data = redis_client.hgetall(key)
            question_id = key.split(":")[-1]
            options = {k: question_data[k] for k in ['option_A', 'option_B', 'option_C', 'option_D'] if k in question_data}
            questions.append({
                "id": question_id,
                "text": question_data.get("text", ""),
                "options": options
            })
        return questions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Rankings
@quiz_router.get("/quizzes/{quiz_id}/questions/{question_id}/most_voted/")
async def get_most_voted_option(quiz_id: str, question_id: str):
    try:
        most_voted_option, vote_count = quiz_manager.get_most_voted_option(quiz_id, question_id)
        if most_voted_option is None:
            return {"message": "No votes recorded"}
        return {"most_voted_option": most_voted_option, "vote_count": vote_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@quiz_router.get("/rankings/most_correct_questions")
def most_correct_questions(quiz_id: str):
    try:
        cursor = '0'
        rankings = {}
        while cursor != '0':
            cursor, question_keys = redis_client.scan(cursor=cursor, match=f"quiz:{quiz_id}:questions:*", count=100)
            for key in question_keys:
                correct_count = redis_client.get(f"correct_count:{key}")
                if correct_count is not None:
                    rankings[key] = int(correct_count)
        return sorted(rankings.items(), key=lambda x: x[1], reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@quiz_router.get("/rankings/average_response_time")
def average_response_time(quiz_id: str):
    try:
        cursor = '0'
        rankings = {}
        while cursor != '0':
            cursor, question_keys = redis_client.scan(cursor=cursor, match=f"quiz:{quiz_id}:questions:*", count=100)
            for key in question_keys:
                response_times = redis_client.lrange(f"response_times:{key}", 0, -1)
                if response_times:
                    average_time = sum(map(int, response_times)) / len(response_times)
                    rankings[key] = average_time
        return rankings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@quiz_router.get("/rankings/top_students")
def top_students(quiz_id: str):
    try:
        students = redis_client.zrange(f"rankings:accuracy_speed:{quiz_id}", 0, -1, withscores=True)
        return students
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@quiz_router.get("/rankings/fastest_students")
def fastest_students(quiz_id: str):
    try:
        students = redis_client.zrange(f"rankings:speed:{quiz_id}", 0, -1, withscores=True)
        return students
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@quiz_router.get("/rankings/most_accurate_students")
def most_accurate_students(quiz_id: str):
    try:
        students = redis_client.zrange(f"rankings:accuracy:{quiz_id}", 0, -1, withscores=True)
        return students
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))