// frontend/js/app.js
import { api } from './api.js';
import { AuthService } from './auth.js';
import { UIService } from './ui.js';
import { IMTCalculator, CaloriesCalculator, BloodPressureCalculator } from './calculators.js';
import { HistoryService } from './history.js';
import { ChartsService } from './charts.js';
import { CONFIG } from './config.js';

const imtCalc = new IMTCalculator();
const caloriesCalc = new CaloriesCalculator();
const bpCalc = new BloodPressureCalculator();

window.registerUser = () => {
    const userId = UIService.getInputValue('userId');
    if (AuthService.register(userId)) {
        HistoryService.loadHistory();
        if (window.ChartsService) ChartsService.loadCharts();
    }
};

window.resetUserId = () => {
    if (AuthService.resetUserId()) {
        HistoryService.loadHistory();
        if (window.ChartsService) ChartsService.loadCharts();
    }
};

window.logoutUser = () => {
    if (AuthService.logout()) {
        HistoryService.loadHistory();
        if (window.ChartsService) ChartsService.loadCharts();
    }
};

window.calculateIMT = () => imtCalc.calculate();
window.calculateCalories = () => caloriesCalc.calculate();
window.calculateBP = () => bpCalc.calculate();
window.loadHistory = (offset = 0) => HistoryService.loadHistory(offset);
window.deleteCalculation = (id) => HistoryService.deleteCalculation(id);
window.loadCharts = () => {
    if (window.ChartsService) {
        ChartsService.loadCharts();
    } else {
        console.warn('⚠️ ChartsService не загружен');
    }
};

window.selectGender = (gender) => {
    caloriesCalc.selectGender(gender);
};

// ========== СИНХРОНИЗАЦИЯ ПОЛЕЙ ВЕСА И РОСТА ==========
function setupFieldSync() {
    console.log('🔗 Настройка синхронизации полей...');

    const imtWeight = document.getElementById('imtWeight');
    const imtHeight = document.getElementById('imtHeight');
    const caloriesWeight = document.getElementById('caloriesWeight');
    const caloriesHeight = document.getElementById('caloriesHeight');

    if (!imtWeight || !imtHeight || !caloriesWeight || !caloriesHeight) {
        console.error('❌ Не все поля найдены для синхронизации');
        console.log('imtWeight:', imtWeight);
        console.log('imtHeight:', imtHeight);
        console.log('caloriesWeight:', caloriesWeight);
        console.log('caloriesHeight:', caloriesHeight);
        return;
    }

    // ИМТ Вес → Калории Вес
    imtWeight.addEventListener('input', (e) => {
        caloriesWeight.value = e.target.value;
        console.log('🔄 Синхронизация: ИМТ Вес → Калории Вес:', e.target.value);
    });

    // ИМТ Рост → Калории Рост
    imtHeight.addEventListener('input', (e) => {
        caloriesHeight.value = e.target.value;
        console.log('🔄 Синхронизация: ИМТ Рост → Калории Рост:', e.target.value);
    });

    // Калории Вес → ИМТ Вес
    caloriesWeight.addEventListener('input', (e) => {
        imtWeight.value = e.target.value;
        console.log('🔄 Синхронизация: Калории Вес → ИМТ Вес:', e.target.value);
    });

    // Калории Рост → ИМТ Рост
    caloriesHeight.addEventListener('input', (e) => {
        imtHeight.value = e.target.value;
        console.log('🔄 Синхронизация: Калории Рост → ИМТ Рост:', e.target.value);
    });

    console.log('✅ Синхронизация полей настроена');
}

// Автозаполнение из последнего расчёта
async function autofillFromHistory() {
    console.log('📥 Автозаполнение из истории...');
    
    try {
        const userId = AuthService.getCurrentUserId();
        if (!userId) return;

        // Загружаем последний ИМТ
        const imtResponse = await fetch(`${CONFIG.API_URL}/calculations/history?user_id=${userId}&calc_type=imt&limit=1`);
        const imtData = await imtResponse.json();
        
        if (imtData.calculations && imtData.calculations.length > 0) {
            const lastIMT = JSON.parse(imtData.calculations[0].input_data);
            
            const imtWeight = document.getElementById('imtWeight');
            const imtHeight = document.getElementById('imtHeight');
            
            if (imtWeight && lastIMT.weight) {
                imtWeight.value = lastIMT.weight;
                // Триггерим событие input для синхронизации
                imtWeight.dispatchEvent(new Event('input'));
                console.log('✅ ИМТ вес заполнен из истории:', lastIMT.weight);
            }
            
            if (imtHeight && lastIMT.height) {
                imtHeight.value = lastIMT.height;
                // Триггерим событие input для синхронизации
                imtHeight.dispatchEvent(new Event('input'));
                console.log('✅ ИМТ рост заполнен из истории:', lastIMT.height);
            }
        }

        // Загружаем последние калории для возраста и пола
        const caloriesResponse = await fetch(`${CONFIG.API_URL}/calculations/history?user_id=${userId}&calc_type=calories&limit=1`);
        const caloriesData = await caloriesResponse.json();
        
        if (caloriesData.calculations && caloriesData.calculations.length > 0) {
            const lastCalories = JSON.parse(caloriesData.calculations[0].input_data);
            
            const ageInput = document.getElementById('caloriesAge');
            const activityInput = document.getElementById('caloriesActivity');
            
            if (ageInput && lastCalories.age) {
                ageInput.value = lastCalories.age;
                console.log('✅ Возраст заполнен из истории:', lastCalories.age);
            }
            
            if (lastCalories.gender) {
                caloriesCalc.selectGender(lastCalories.gender);
                console.log('✅ Пол заполнен из истории:', lastCalories.gender);
            }
            
            if (activityInput && lastCalories.activity_level) {
                activityInput.value = lastCalories.activity_level;
                console.log('✅ Активность заполнена из истории:', lastCalories.activity_level);
            }
        }

        // Загружаем последнее давление
        const bpResponse = await fetch(`${CONFIG.API_URL}/calculations/history?user_id=${userId}&calc_type=blood_pressure&limit=1`);
        const bpData = await bpResponse.json();
        
        if (bpData.calculations && bpData.calculations.length > 0) {
            const lastBP = JSON.parse(bpData.calculations[0].input_data);
            
            const systolicInput = document.getElementById('bpSystolic');
            const diastolicInput = document.getElementById('bpDiastolic');
            
            if (systolicInput && lastBP.systolic) {
                systolicInput.value = lastBP.systolic;
                console.log('✅ Систолическое заполнено из истории:', lastBP.systolic);
            }
            
            if (diastolicInput && lastBP.diastolic) {
                diastolicInput.value = lastBP.diastolic;
                console.log('✅ Диастолическое заполнено из истории:', lastBP.diastolic);
            }
        }

        console.log('✅ Автозаполнение из истории завершено');

    } catch (error) {
        console.error('❌ Ошибка автозаполнения из истории:', error);
    }
}

async function init() {
    console.log('🚀 Медицинский Калькулятор загружен');
    console.log('🌐 API URL:', CONFIG.API_URL);

    const userId = AuthService.autoInit();
    console.log('👤 Текущий пользователь:', userId);

    try {
        const health = await api.checkHealth();
        console.log('✅ Backend доступен:', health);
    } catch (error) {
        console.warn('⚠️ Backend недоступен:', error.message);
        UIService.showError('Backend недоступен. Проверьте что сервер запущен.');
    }

    // Настраиваем синхронизацию полей сразу
    setTimeout(() => {
        setupFieldSync();
    }, 100);

    // Автозаполнение из истории
    setTimeout(() => {
        autofillFromHistory();
    }, 500);

    // История
    setTimeout(() => {
        HistoryService.loadHistory();
    }, 800);

    // Графики
    setTimeout(() => {
        if (window.ChartsService) {
            ChartsService.loadCharts();
            console.log('📊 ChartsService.loadCharts() вызван');
        }
    }, 1200);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
