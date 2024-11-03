import unittest
from app.quiz_manager import QuizManager  # Supondo que você tenha uma classe QuizManager
from unittest.mock import MagicMock

class TestQuizManager(unittest.TestCase):

    def setUp(self):
        # Configuração inicial antes de cada teste
        self.quiz_manager = QuizManager()
        self.quiz_manager.redis_client = MagicMock()  # Mock do cliente Redis

    def test_create_quiz(self):
        # Testa a criação de um quiz
        quiz_id = '1'
        title = 'Quiz de Teste'
        description = 'Descrição do Quiz de Teste'
        
        self.quiz_manager.create_quiz(quiz_id, title, description)
        
        # Verifica se o método hmset foi chamado com os argumentos corretos
        self.quiz_manager.redis_client.hmset.assert_called_with(
            f"quiz:{quiz_id}",
            {
                "title": title,
                "description": description,
                "created_at": unittest.mock.ANY
            }
        )

    def test_add_question(self):
        # Testa a adição de uma pergunta
        quiz_id = '1'
        question_id = '101'
        text = 'Qual é a capital da França?'
        options = {'A': 'Paris', 'B': 'Londres', 'C': 'Berlim', 'D': 'Roma'}
        
        self.quiz_manager.add_question(quiz_id, question_id, text, options)
        
        # Verifica se o método hmset foi chamado para a pergunta
        self.quiz_manager.redis_client.hmset.assert_called_with(
            f"question:{question_id}",
            {
                "text": text,
                "option_A": options['A'],
                "option_B": options['B'],
                "option_C": options['C'],
                "option_D": options['D']
            }
        )
        
        # Verifica se a pergunta foi associada ao quiz
        self.quiz_manager.redis_client.sadd.assert_called_with(
            f"quiz:{quiz_id}:questions", question_id
        )

    def test_record_response(self):
        # Testa o registro de uma resposta
        quiz_id = '1'
        student_id = 'student_1'
        question_id = '101'
        selected_option = 'A'
        
        self.quiz_manager.record_response(quiz_id, student_id, question_id, selected_option)
        
        # Verifica se a resposta do aluno foi registrada
        self.quiz_manager.redis_client.hset.assert_called_with(
            f"student_responses:{quiz_id}:{student_id}", question_id, selected_option
        )
        
        # Verifica se o contador de votos foi atualizado
        self.quiz_manager.redis_client.hincrby.assert_called_with(
            f"votes:{question_id}", selected_option, 1
        )

if __name__ == '__main__':
    unittest.main()