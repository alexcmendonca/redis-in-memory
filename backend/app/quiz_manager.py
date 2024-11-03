# app/quiz_manager.py

import redis
import time

class QuizManager:
    def __init__(self, redis_host='127.0.0.1', redis_port=6379):
        self.redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

    def create_quiz(self, quiz_id, title, description):
        """
        Cria um novo quiz com o ID fornecido, título e descrição.
        """
        try:
            quiz_key = f"quiz:{quiz_id}"
            self.redis_client.hset(quiz_key, mapping={
                "title": title,
                "description": description,
                "created_at": self._current_timestamp()
            })
        except redis.RedisError as e:
            raise Exception(f"Erro ao criar quiz: {str(e)}")

    def add_question(self, quiz_id, question_id, text, options):
        """
        Adiciona uma pergunta ao quiz especificado.
        """
        try:
            question_key = f"question:{question_id}"
            self.redis_client.hset(question_key, mapping={
                "text": text,
                "option_A": options['A'],
                "option_B": options['B'],
                "option_C": options['C'],
                "option_D": options['D']
            })
            self.redis_client.sadd(f"quiz:{quiz_id}:questions", question_id)
        except redis.RedisError as e:
            raise Exception(f"Erro ao adicionar pergunta: {str(e)}")

    def record_response(self, quiz_id, student_id, question_id, selected_option):
        """
        Registra a resposta de um aluno para uma pergunta específica.
        """
        try:
            response_key = f"student_responses:{quiz_id}:{student_id}"
            self.redis_client.hset(response_key, question_id, selected_option)
            self.redis_client.hincrby(f"votes:{question_id}", selected_option, 1)
        except redis.RedisError as e:
            raise Exception(f"Erro ao registrar resposta: {str(e)}")

    def get_most_voted_option(self, quiz_id, question_id):
        """
        Retorna a opção mais votada para uma pergunta específica.
        """
        try:
            votes = self.redis_client.hgetall(f"votes:{question_id}")
            if not votes:
                return None, 0
            most_voted_option = max(votes, key=votes.get)
            return most_voted_option, int(votes[most_voted_option])
        except redis.RedisError as e:
            raise Exception(f"Erro ao obter opção mais votada: {str(e)}")

    def get_most_correct_questions(self, quiz_id):
        """
        Retorna a questão com maior índice de acerto.
        """
        try:
            questions = self.redis_client.smembers(f"quiz:{quiz_id}:questions")
            correct_answers_key = f"quiz:{quiz_id}:respostas"
            correct_answers = self.redis_client.hgetall(correct_answers_key)
            
            correct_counts = {}
            for question_id in questions:
                responses_key = f"responses:{question_id}"
                responses = self.redis_client.hgetall(responses_key)
                correct_answer = correct_answers.get(question_id)
                correct_count = sum(1 for answer in responses.values() if answer == correct_answer)
                correct_counts[question_id] = correct_count
            
            most_correct_question = max(correct_counts, key=correct_counts.get)
            return most_correct_question, correct_counts[most_correct_question]
        except redis.RedisError as e:
            raise Exception(f"Erro ao obter questões mais acertadas: {str(e)}")

    def get_questions_with_most_abstentions(self, quiz_id, total_students):
        """
        Retorna a questão com mais abstenções.
        """
        try:
            questions = self.redis_client.smembers(f"quiz:{quiz_id}:questions")
            
            abstentions = {}
            for question_id in questions:
                responses_key = f"responses:{question_id}"
                response_count = self.redis_client.hlen(responses_key)
                abstentions[question_id] = total_students - response_count
            
            most_abstained_question = max(abstentions, key=abstentions.get)
            return most_abstained_question, abstentions[most_abstained_question]
        except redis.RedisError as e:
            raise Exception(f"Erro ao obter questões com mais abstenções: {str(e)}")

    def get_average_response_time(self, question_id):
        """
        Retorna o tempo médio de resposta para uma pergunta.
        """
        try:
            response_times_key = f"response_times:{question_id}"
            response_times = self.redis_client.hvals(response_times_key)
            total_time = sum(map(int, response_times))
            average_time = total_time / len(response_times) if response_times else 0
            return average_time
        except redis.RedisError as e:
            raise Exception(f"Erro ao obter tempo médio de resposta: {str(e)}")

    def get_top_students(self, quiz_id):
        """
        Retorna o aluno com maior acerto e mais rápido.
        """
        try:
            students = self.redis_client.smembers(f"quiz:{quiz_id}:students")
            correct_answers_key = f"quiz:{quiz_id}:respostas"
            correct_answers = self.redis_client.hgetall(correct_answers_key)
            
            student_scores = {}
            for student_id in students:
                responses_key = f"student_responses:{quiz_id}:{student_id}"
                responses = self.redis_client.hgetall(responses_key)
                correct_count = sum(1 for q, a in responses.items() if correct_answers.get(q) == a)
                
                response_times_key = f"student_response_times:{quiz_id}:{student_id}"
                response_times = self.redis_client.hvals(response_times_key)
                total_time = sum(map(int, response_times))
                
                student_scores[student_id] = (correct_count, -total_time)  # Negative time for sorting
            
            top_student = max(student_scores, key=student_scores.get)
            return top_student, student_scores[top_student]
        except redis.RedisError as e:
            raise Exception(f"Erro ao obter alunos com maior acerto e mais rápidos: {str(e)}")

    def get_students_with_most_correct_answers(self, quiz_id):
        """
        Retorna o aluno com maior número de acertos.
        """
        try:
            students = self.redis_client.smembers(f"quiz:{quiz_id}:students")
            correct_answers_key = f"quiz:{quiz_id}:respostas"
            correct_answers = self.redis_client.hgetall(correct_answers_key)
            
            student_correct_counts = {}
            for student_id in students:
                responses_key = f"student_responses:{quiz_id}:{student_id}"
                responses = self.redis_client.hgetall(responses_key)
                correct_count = sum(1 for q, a in responses.items() if correct_answers.get(q) == a)
                student_correct_counts[student_id] = correct_count
            
            top_student = max(student_correct_counts, key=student_correct_counts.get)
            return top_student, student_correct_counts[top_student]
        except redis.RedisError as e:
            raise Exception(f"Erro ao obter alunos com maior número de acertos: {str(e)}")

    def get_fastest_students(self, quiz_id):
        """
        Retorna o aluno mais rápido.
        """
        try:
            students = self.redis_client.smembers(f"quiz:{quiz_id}:students")
            
            student_times = {}
            for student_id in students:
                response_times_key = f"student_response_times:{quiz_id}:{student_id}"
                response_times = self.redis_client.hvals(response_times_key)
                total_time = sum(map(int, response_times))
                student_times[student_id] = total_time
            
            fastest_student = min(student_times, key=student_times.get)
            return fastest_student, student_times[fastest_student]
        except redis.RedisError as e:
            raise Exception(f"Erro ao obter alunos mais rápidos: {str(e)}")

    def _current_timestamp(self):
        """
        Retorna o timestamp atual.
        """
        return int(time.time())

# Exemplo de uso
# quiz_manager = QuizManager()
# Chame os métodos conforme necessário, por exemplo:
# most_voted_option = quiz_manager.get_most_voted_option('quiz_id', 'question_id')