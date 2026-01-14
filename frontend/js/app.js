import { api } from './api.js';
import { AuthService } from './auth.js';
import { UIService } from './ui.js';
import { IMTCalculator, CaloriesCalculator, BloodPressureCalculator } from './calculators.js';
import { HistoryService } from './history.js';
import { CONFIG } from './config.js';

const imtCalc = new IMTCalculator();
const caloriesCalc = new CaloriesCalculator();
const bpCalc = new BloodPressureCalculator();

window.registerUser = () => {
    const userId = UIService.getInputValue('userId');
    if (AuthService.register(userId)) {
        HistoryService.loadHistory();
    }
};

window.resetUserId = () => {
    if (AuthService.resetUserId()) {
        HistoryService.loadHistory();
    }
};

window.logoutUser = () => {
    if (AuthService.logout()) {
        HistoryService.loadHistory();
    }
};

window.calculateIMT = () => imtCalc.calculate();
window.calculateCalories = () => caloriesCalc.calculate();
window.calculateBP = () => bpCalc.calculate();

// ВАЖНО: функция должна быть в window
window.loadHistory = (offset = 0) => HistoryService.loadHistory(offset);
window.deleteCalculation = (id) => HistoryService.deleteCalculation(id);

window.selectGender = (gender) => {
    caloriesCalc.selectGender(gender);
};

async function init() {
    console.log('🏥 Медицинский Калькулятор загружен');
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

    setTimeout(() => {
        HistoryService.loadHistory();
    }, 500);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
