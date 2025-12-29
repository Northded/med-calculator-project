let currentUser = null;
let selectedGender = null;

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.textContent = '❌ ' + message;
    document.body.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 3000);
}

function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-msg';
    successDiv.textContent = '✅ ' + message;
    document.body.appendChild(successDiv);
    setTimeout(() => successDiv.remove(), 3000);
}

function selectGender(gender) {
    selectedGender = gender;
    document.getElementById('genderM').classList.remove('active');
    document.getElementById('genderF').classList.remove('active');

    if (gender === 'м') {
        document.getElementById('genderM').classList.add('active');
    } else {
        document.getElementById('genderF').classList.add('active');
    }
}

function registerUser() {
    const userId = document.getElementById('userId').value.trim();

    if (!userId) {
        showError('Пожалуйста, введите ID пользователя');
        return;
    }

    currentUser = userId;
    showSuccess('Вы успешно вошли!');
    document.getElementById('userId').disabled = true;
}

function calculateIMT() {
    if (!currentUser) {
        showError('Пожалуйста, сначала войдите');
        return;
    }

    const weight = parseFloat(document.getElementById('imtWeight').value);
    const height = parseFloat(document.getElementById('imtHeight').value);

    if (!weight || !height || weight <= 0 || height <= 0) {
        showError('Введите корректные значения');
        return;
    }

    // Расчет ИМТ
    const heightM = height / 100;
    const imt = weight / (heightM * heightM);

    let interpretation = '';
    let resultClass = '';

    if (imt < 18.5) {
        interpretation = 'Недостаточный вес';
        resultClass = 'warning';
    } else if (imt < 25) {
        interpretation = 'Нормальный вес';
        resultClass = 'success';
    } else if (imt < 30) {
        interpretation = 'Избыточный вес';
        resultClass = 'warning';
    } else {
        interpretation = 'Ожирение';
        resultClass = 'danger';
    }

    const resultDiv = document.getElementById('imtResult');
    resultDiv.innerHTML = `
        <div class="result-value">${imt.toFixed(1)}</div>
        <div class="result-interpretation">${interpretation}</div>
        <div class="result-unit">кг/м²</div>
    `;
    resultDiv.className = 'result-box ' + resultClass;
    resultDiv.style.display = 'block';
    showSuccess('ИМТ рассчитан!');
}

function calculateCalories() {
    if (!currentUser) {
        showError('Пожалуйста, сначала войдите');
        return;
    }

    const age = parseInt(document.getElementById('caloriesAge').value);
    const weight = parseFloat(document.getElementById('caloriesWeight').value);
    const height = parseFloat(document.getElementById('caloriesHeight').value);
    const gender = selectedGender;
    const activity = parseFloat(document.getElementById('caloriesActivity').value);

    if (!age || !weight || !height || !gender) {
        showError('Заполните все поля и выберите пол');
        return;
    }

    // Формула Харриса-Бенедикта
    let bmr;
    if (gender === 'м') {
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age);
    } else {
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age);
    }

    const tdee = bmr * activity;

    const resultDiv = document.getElementById('caloriesResult');
    resultDiv.innerHTML = `
        <div style="font-weight: 600; color: var(--text-gray); margin-bottom: 8px; font-size: 0.9em;">Базовый метаболизм (БМО):</div>
        <div class="result-value">${bmr.toFixed(0)} ккал</div>
        <div style="font-weight: 600; color: var(--text-gray); margin-top: 16px; margin-bottom: 8px; font-size: 0.9em;">Суточные расходы (ТДЕЕ):</div>
        <div class="result-value">${tdee.toFixed(0)} ккал</div>
    `;
    resultDiv.className = 'result-box success';
    resultDiv.style.display = 'block';
    showSuccess('Калории рассчитаны!');
}

function calculateBP() {
    if (!currentUser) {
        showError('Пожалуйста, сначала войдите');
        return;
    }

    const systolic = parseInt(document.getElementById('bpSystolic').value);
    const diastolic = parseInt(document.getElementById('bpDiastolic').value);

    if (!systolic || !diastolic) {
        showError('Введите оба значения давления');
        return;
    }

    let category = '';
    let interpretation = '';
    let resultClass = '';

    if (systolic < 120 && diastolic < 80) {
        category = 'Нормальное';
        interpretation = 'Оптимальное артериальное давление';
        resultClass = 'success';
    } else if (systolic < 130 && diastolic < 80) {
        category = 'Повышенное';
        interpretation = 'Внимание: следите за давлением';
        resultClass = 'warning';
    } else if (systolic < 140 || diastolic < 90) {
        category = 'Гипертензия I степени';
        interpretation = 'Рекомендуется консультация врача';
        resultClass = 'warning';
    } else {
        category = 'Гипертензия II степени';
        interpretation = 'Требуется срочная консультация врача';
        resultClass = 'danger';
    }

    const resultDiv = document.getElementById('bpResult');
    resultDiv.innerHTML = `
        <div class="result-value">${systolic}/${diastolic}</div>
        <div style="font-weight: 600; color: var(--text-dark); margin-bottom: 10px; margin-top: 10px;">${category}</div>
        <div class="result-interpretation">${interpretation}</div>
        <div class="result-unit">мм рт.ст.</div>
    `;
    resultDiv.className = 'result-box ' + resultClass;
    resultDiv.style.display = 'block';
    showSuccess('Давление проверено!');
}

function loadHistory() {
    if (!currentUser) {
        showError('Пожалуйста, сначала войдите');
        return;
    }

    // TODO: Здесь будет API запрос к FastAPI
    showError('История будет доступна после подключения к FastAPI');
}

// Инициализация
console.log('🏥 Медицинский Калькулятор загружен');
console.log('💡 Frontend готов к подключению FastAPI');
