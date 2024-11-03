let currentQuestionIndex = 0;
let studentName = '';
let questions = [];
const quizId = '1';

async function startQuiz() {
    studentName = document.getElementById('student-name').value.trim();
    if (!studentName) {
        alert('Por favor, insira seu nome.');
        return;
    }
    try {
        // Use o endereço completo do backend
        const response = await fetch('http://127.0.0.1:8000/get_questions?quiz_id=${quizId}');
        if (!response.ok) throw new Error('Erro ao buscar perguntas');
        questions = await response.json();
        document.getElementById('start-screen').style.display = 'none';
        document.getElementById('quiz-screen').style.display = 'block';
        showQuestion();
    } catch (error) {
        console.error('Erro ao buscar perguntas:', error);
        document.getElementById('feedback').innerText = 'Erro ao carregar perguntas. Tente novamente mais tarde.';
        document.getElementById('feedback').style.display = 'block';
    }
}

function showQuestion() {
    if (currentQuestionIndex >= questions.length) {
        alert('Quiz concluído!');
        showRankings();
        return;
    }
    const question = questions[currentQuestionIndex];
    const questionContainer = document.getElementById('question-container');
    questionContainer.innerHTML = `
        <div class="question">
            <h2>${question.pergunta}</h2>
            <ul class="options">
                ${Object.entries(question.options).map(([key, value]) => `
                    <li>
                        <label>
                            <input type="radio" name="option" value="${key}">
                            ${key}: ${value}
                        </label>
                    </li>
                `).join('')}
            </ul>
        </div>
    `;
}

async function showRankings() {
    try {
        const response = await fetch('http://127.0.0.1:8000/get_rankings?quiz_id=${quizId}');
        if (!response.ok) throw new Error('Erro ao buscar rankings');
        const rankings = await response.json();
        displayRankings(rankings);
    } catch (error) {
        console.error('Erro ao buscar rankings:', error);
        document.getElementById('feedback').innerText = 'Erro ao carregar rankings. Tente novamente mais tarde.';
        document.getElementById('feedback').style.display = 'block';
    }
}

async function submitAnswer() {
    const selectedOption = document.querySelector('input[name="option"]:checked');
    if (!selectedOption) {
        alert('Por favor, selecione uma resposta.');
        return;
    }
    const answer = selectedOption.value;
    const questionId = questions[currentQuestionIndex].id;
    const responseTime = 20; // Simulação do tempo de resposta

    try {
        const response = await fetch('http://127.0.0.1:8000/submit_response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                student_id: studentName,
                question_id: questionId,
                selected_option: answer,
                response_time: responseTime
            })
        });
        if (!response.ok) throw new Error('Erro ao enviar resposta');
        const data = await response.json();
        console.log(data);
        currentQuestionIndex++;
        showQuestion();
    } catch (error) {
        console.error('Erro ao enviar resposta:', error);
        document.getElementById('feedback').innerText = 'Erro ao enviar resposta. Tente novamente.';
        document.getElementById('feedback').style.display = 'block';
    }
}