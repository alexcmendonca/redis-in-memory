# utils.py

import time

def current_timestamp():
    """Retorna o timestamp atual."""
    return int(time.time())

def calculate_average_response_time(response_times):
    """Calcula o tempo médio de resposta."""
    if not response_times:
        return 0
    return sum(response_times) / len(response_times)