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
        ChartsService.loadCharts();
    }
};

window.resetUserId = () => {
    if (AuthService.resetUserId()) {
        HistoryService.loadHistory();
        ChartsService.loadCharts();
    }
};

window.logoutUser = () => {
    if (AuthService.logout()) {
        HistoryService.loadHistory();
        ChartsService.loadCharts();
    }
};

window.calculateIMT = () => imtCalc.calculate();
window.calculateCalories = () => caloriesCalc.calculate();
window.calculateBP = () => bpCalc.calculate();
window.loadHistory = (offset = 0) => HistoryService.loadHistory(offset);
window.deleteCalculation = (id) => HistoryService.deleteCalculation(id);
window.loadCharts = () => ChartsService.loadCharts();

window.selectGender = (gender) => {
    caloriesCalc.selectGender(gender);
};

async function autofillFields() {
    try {
        const userId = AuthService.getCurrentUserId();
        if (!userId) return;

        const imtResponse = await fetch(`${CONFIG.API_URL}/calculations/history?user_id=${userId}&calc_type=imt&limit=1`);
        const imtData = await imtResponse.json();
        if (imtData.calculations && imtData.calculations.length > 0) {
            const lastIMT = JSON.parse(imtData.calculations[0].input_data);
            UIService.setInputValue('imtWeight', lastIMT.weight || '');
            UIService.setInputValue('imtHeight', lastIMT.height || '');
            console.log('✅ ИМТ: автозаполнение завершено', lastIMT);
        }

        const caloriesResponse = await fetch(`${CONFIG.API_URL}/calculations/history?user_id=${userId}&calc_type=calories&limit=1`);
        const caloriesData = await caloriesResponse.json();
        if (caloriesData.calculations && caloriesData.calculations.length > 0) {
            const lastCalories = JSON.parse(caloriesData.calculations[0].input_data);
            UIService.setInputValue('caloriesWeight', lastCalories.weight || '');
            UIService.setInputValue('caloriesHeight', lastCalories.height || '');
            UIService.setInputValue('caloriesAge', lastCalories.age || '');
            
            if (lastCalories.gender) {
                caloriesCalc.selectGender(lastCalories.gender);
            }
            if (lastCalories.activity_level) {
                UIService.setInputValue('caloriesActivity', lastCalories.activity_level);
            }
            console.log('✅ Калории: автозаполнение завершено', lastCalories);
        }

        const bpResponse = await fetch(`${CONFIG.API_URL}/calculations/history?user_id=${userId}&calc_type=blood_pressure&limit=1`);
        const bpData = await bpResponse.json();
        if (bpData.calculations && bpData.calculations.length > 0) {
            const lastBP = JSON.parse(bpData.calculations[0].input_data);
            UIService.setInputValue('bpSystolic', lastBP.systolic || '');
            UIService.setInputValue('bpDiastolic', lastBP.diastolic || '');
            console.log('✅ Давление: автозаполнение завершено', lastBP);
        }

    } catch (error) {
        console.error('Ошибка автозаполнения:', error);
    }
}

async function init() {
    console.log('Медицинский Калькулятор загружен');
    console.log('API URL:', CONFIG.API_URL);

    const userId = AuthService.autoInit();
    console.log('👤 Текущий пользователь:', userId);

    try {
        const health = await api.checkHealth();
        console.log('Backend доступен:', health);
    } catch (error) {
        console.warn('Backend недоступен:', error.message);
        UIService.showError('Backend недоступен. Проверьте что сервер запущен.');
    }

    setTimeout(() => {
        autofillFields();
    }, 300);

    setTimeout(() => {
        HistoryService.loadHistory();
    }, 500);

    setTimeout(() => {
        ChartsService.loadCharts();
    }, 1000);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
