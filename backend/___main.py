from fastapi import FastAPI, HTTPException
import redis
from fastapi import APIRouter

# Configuração do Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

# Inicializa o aplicativo FastAPI
app = FastAPI()

# Define o roteador
quiz_router = APIRouter()

@quiz_router.get("/quizzes")
async def get_quizzes():
    # Exemplo de como você pode integrar o Redis
    try:
        quizzes = redis_client.keys("quiz:*")
        return {"quizzes": quizzes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@quiz_router.post("/quizzes")
async def create_quiz(quiz: dict):
    try:
        quiz_id = quiz.get("id")
        if not quiz_id:
            raise HTTPException(status_code=400, detail="Quiz ID is required")
        
        quiz_key = f"quiz:{quiz_id}"
        redis_client.hmset(quiz_key, quiz)
        return {"message": "Quiz created", "quiz": quiz}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Inclui o roteador no aplicativo FastAPI
app.include_router(quiz_router, prefix="/api")

# Função auxiliar para obter o timestamp atual
def _current_timestamp():
    import time
    return int(time.time())