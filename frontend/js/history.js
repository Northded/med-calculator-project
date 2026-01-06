import { api } from './api.js';
import { AuthService } from './auth.js';
import { UIService } from './ui.js';
import { CONFIG } from './config.js';

export class HistoryService {
    static async loadHistory() {
        if (!AuthService.requireAuth()) return;

        const userId = AuthService.getCurrentUserId();

        try {
            const data = await api.getHistory(userId, CONFIG.DEFAULT_LIMIT, 0);

            this.renderHistory(data);

        } catch (error) {
            UIService.showError('Ошибка загрузки истории');
            console.error('History load error:', error);
        }
    }

    static renderHistory(data) {
        const container = document.getElementById('historyContainer');

        if (!data.calculations || data.calculations.length === 0) {
            container.innerHTML = `
                <div class="history-empty">
                    <div class="history-empty-icon">📊</div>
                    <p>История расчётов пуста</p>
                    <p style="font-size: 0.85em;">Используйте калькуляторы выше для начала работы</p>
                </div>
            `;
            return;
        }

        const items = data.calculations.map(calc => this.createHistoryItem(calc)).join('');

        container.innerHTML = items;

        if (data.total > data.limit) {
            container.innerHTML += `
                <div style="text-align: center; margin-top: 20px; color: var(--text-gray);">
                    Показано ${data.calculations.length} из ${data.total} записей
                </div>
            `;
        }
    }

    static createHistoryItem(calc) {
        const icon = CONFIG.CALC_TYPE_ICONS[calc.calc_type] || '📊';
        const typeName = CONFIG.CALC_TYPE_LABELS[calc.calc_type] || calc.calc_type;
        const date = new Date(calc.created_at).toLocaleString('ru-RU');

        return `
            <div class="history-item">
                <div class="history-icon">${icon}</div>
                <div class="history-content">
                    <div class="history-title">${typeName}</div>
                    <div class="history-date">${date}</div>
                    <div class="history-result">Результат: ${calc.result}</div>
                    ${calc.interpretation ? `<div class="history-interpretation">${calc.interpretation}</div>` : ''}
                </div>
                <button class="history-delete" onclick="deleteCalculation(${calc.id})" title="Удалить">
                    🗑️
                </button>
            </div>
        `;
    }

    static async deleteCalculation(calcId) {
        if (!AuthService.requireAuth()) return;

        const confirmed = confirm('Удалить этот расчёт?');
        if (!confirmed) return;

        const userId = AuthService.getCurrentUserId();

        try {
            await api.deleteCalculation(calcId, userId);

            UIService.showSuccess('Расчёт удалён');

            await this.loadHistory();

        } catch (error) {
            UIService.showError('Ошибка удаления');
            console.error('Delete error:', error);
        }
    }
}