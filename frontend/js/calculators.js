import { api } from './api.js';
import { AuthService } from './auth.js';
import { UIService } from './ui.js';

// ========== BASE CALCULATOR ==========
export class BaseCalculator {
    checkAuth() {
        return AuthService.requireAuth();
    }
    
    getUserId() {
        return AuthService.getCurrentUserId();
    }
}

// ========== IMT CALCULATOR ==========
export class IMTCalculator extends BaseCalculator {
    async calculate() {
        if (!this.checkAuth()) return;

        const weight = parseFloat(UIService.getInputValue('imtWeight'));
        const height = parseFloat(UIService.getInputValue('imtHeight'));

        if (!weight || !height || weight <= 0 || height <= 0) {
            UIService.showError('Введите корректные значения веса и роста');
            return;
        }

        try {
            console.log('Отправка запроса ИМТ:', { user_id: this.getUserId(), weight, height });
            
            const data = await api.calculateIMT({
                user_id: this.getUserId(),
                weight,
                height
            });

            console.log('Ответ backend (ИМТ):', data);

            if (!data || data.result === undefined) {
                console.error('Backend не вернул result!', data);
                UIService.showError('Ошибка: backend не вернул результат расчёта');
                return;
            }

            const imt = data.result;
            const category = this.getIMTCategory(imt);
            
            UIService.showResult('imtResult', {
                value: imt.toFixed(1),
                interpretation: data.interpretation || category.text,
                unit: 'кг/м²'
            }, category.class);
            
            UIService.showSuccess('Расчёт ИМТ сохранён!');
            
            setTimeout(() => {
                if (window.loadHistory) window.loadHistory();
            }, 500);
            
        } catch (error) {
            console.error('Ошибка расчёта ИМТ:', error);
            UIService.showError(error.message || 'Ошибка расчёта ИМТ');
        }
    }

    getIMTCategory(imt) {
        if (imt < 16) {
            return { class: 'danger', text: 'Выраженный дефицит массы тела' };
        } else if (imt < 18.5) {
            return { class: 'warning', text: 'Недостаточная масса тела' };
        } else if (imt < 25) {
            return { class: 'success', text: 'Нормальная масса тела' };
        } else if (imt < 30) {
            return { class: 'warning', text: 'Избыточная масса тела (предожирение)' };
        } else if (imt < 35) {
            return { class: 'danger', text: 'Ожирение I степени' };
        } else if (imt < 40) {
            return { class: 'danger', text: 'Ожирение II степени' };
        } else {
            return { class: 'danger', text: 'Ожирение III степени (морбидное)' };
        }
    }
}

// ========== CALORIES CALCULATOR ==========
export class CaloriesCalculator extends BaseCalculator {
    constructor() {
        super();
        this.selectedGender = null;
    }

    selectGender(gender) {
        this.selectedGender = gender;
        document.getElementById('genderM').classList.remove('active');
        document.getElementById('genderF').classList.remove('active');

        if (gender === 'м') {
            document.getElementById('genderM').classList.add('active');
        } else {
            document.getElementById('genderF').classList.add('active');
        }
    }

    async calculate() {
        if (!this.checkAuth()) return;

        const age = parseInt(UIService.getInputValue('caloriesAge'));
        const weight = parseFloat(UIService.getInputValue('caloriesWeight'));
        const height = parseFloat(UIService.getInputValue('caloriesHeight'));
        const activity = parseFloat(UIService.getInputValue('caloriesActivity'));

        if (!this.selectedGender) {
            UIService.showError('Выберите пол');
            return;
        }

        if (!age || !weight || !height || age <= 0 || weight <= 0 || height <= 0) {
            UIService.showError('Введите корректные значения');
            return;
        }

        try {
            console.log('Отправка запроса Калории:', {
                user_id: this.getUserId(),
                age,
                weight,
                height,
                gender: this.selectedGender,
                activity
            });
            
            const data = await api.calculateCalories({
                user_id: this.getUserId(),
                age,
                weight,
                height,
                gender: this.selectedGender,
                activity
            });

            console.log('Ответ backend (Калории):', data);

            if (!data || data.result === undefined) {
                console.error('Backend не вернул result!', data);
                UIService.showError('Ошибка: backend не вернул результат расчёта');
                return;
            }

            const tdee = data.result;

            UIService.showResult('caloriesResult', {
                value: Math.round(tdee),
                interpretation: data.interpretation || `Суточная калорийность: ${Math.round(tdee)} ккал`,
                unit: 'ккал/день'
            }, 'success');
            
            UIService.showSuccess('Расчёт калорий сохранён!');

            setTimeout(() => {
                if (window.loadHistory) window.loadHistory();
            }, 500);
            
        } catch (error) {
            console.error('Ошибка расчёта калорий:', error);
            UIService.showError(error.message || 'Ошибка расчёта калорий');
        }
    }
}

// ========== BLOOD PRESSURE CALCULATOR ==========
export class BloodPressureCalculator extends BaseCalculator {
    async calculate() {
        if (!this.checkAuth()) return;

        const systolic = parseInt(UIService.getInputValue('bpSystolic'));
        const diastolic = parseInt(UIService.getInputValue('bpDiastolic'));

        if (!systolic || !diastolic || systolic <= 0 || diastolic <= 0) {
            UIService.showError('Введите корректные значения давления');
            return;
        }

        if (systolic <= diastolic) {
            UIService.showError('Систолическое давление должно быть выше диастолического');
            return;
        }

        try {
            console.log('Отправка запроса Давление:', {
                user_id: this.getUserId(),
                systolic,
                diastolic
            });
            
            const data = await api.calculateBloodPressure({
                user_id: this.getUserId(),
                systolic,
                diastolic
            });

            console.log('📥 Ответ backend (Давление):', data);

            if (!data || data.result === undefined) {
                console.error('Backend не вернул result!', data);
                UIService.showError('Ошибка: backend не вернул результат расчёта');
                return;
            }

            let categoryClass = 'success';
            if (data.interpretation) {
                if (data.interpretation.includes('криз') || data.interpretation.includes('II')) {
                    categoryClass = 'danger';
                } else if (data.interpretation.includes('Гипертония') || 
                           data.interpretation.includes('Повышенное') ||
                           data.interpretation.includes('I степени')) {
                    categoryClass = 'warning';
                }
            }

            UIService.showResult('bpResult', {
                value: `${systolic}/${diastolic}`,
                interpretation: data.interpretation || 'Давление измерено',
                unit: 'мм рт.ст.'
            }, categoryClass);
            
            UIService.showSuccess('Анализ давления сохранён!');

            setTimeout(() => {
                if (window.loadHistory) window.loadHistory();
            }, 500);
            
        } catch (error) {
            console.error('Ошибка анализа давления:', error);
            UIService.showError(error.message || 'Ошибка анализа давления');
        }
    }
}
