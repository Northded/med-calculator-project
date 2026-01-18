import { api } from './api.js';
import { AuthService } from './auth.js';
import { UIService } from './ui.js';
import { CONFIG } from './config.js';

export class HistoryService {
    static currentOffset = 0;
    static currentLimit = CONFIG.DEFAULT_LIMIT || 10;
    static totalRecords = 0;

    static async loadHistory(offset = 0) {
        if (!AuthService.requireAuth()) return;

        const userId = AuthService.getCurrentUserId();
        this.currentOffset = offset;

        try {
            const data = await api.getHistory(userId, this.currentLimit, offset);
            console.log('История загружена:', data);
            console.log('Первый элемент:', data.calculations?.[0]);
            
            this.totalRecords = data.total || 0;
            
            this.renderHistory(data);
            this.renderPagination();

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
    }

    static renderPagination() {
        const container = document.getElementById('paginationContainer');
        if (!container) {
            console.warn('⚠️ paginationContainer не найден в HTML!');
            return;
        }

        const totalPages = Math.ceil(this.totalRecords / this.currentLimit);
        const currentPage = Math.floor(this.currentOffset / this.currentLimit) + 1;

        console.log('Пагинация:', { totalRecords: this.totalRecords, totalPages, currentPage });

        if (totalPages <= 1) {
            container.innerHTML = `
                <p style="text-align: center; color: #666; margin-top: 10px;">
                    Всего записей: ${this.totalRecords}
                </p>
            `;
            return;
        }

        let html = '<div class="pagination-controls">';

        const prevOffset = (currentPage - 2) * this.currentLimit;
        html += `
            <button 
                class="btn-pagination" 
                onclick="window.loadHistory(${prevOffset})" 
                ${currentPage === 1 ? 'disabled' : ''}>
                ← Назад
            </button>
        `;

        html += '<div class="pagination-numbers">';
        
        const maxVisible = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
        let endPage = Math.min(totalPages, startPage + maxVisible - 1);
        
        if (endPage - startPage < maxVisible - 1) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }

        if (startPage > 1) {
            html += `
                <button 
                    class="btn-page" 
                    onclick="window.loadHistory(0)">
                    1
                </button>
            `;
            if (startPage > 2) {
                html += '<span class="pagination-dots">...</span>';
            }
        }

        for (let page = startPage; page <= endPage; page++) {
            const offset = (page - 1) * this.currentLimit;
            html += `
                <button 
                    class="btn-page ${page === currentPage ? 'active' : ''}" 
                    onclick="window.loadHistory(${offset})">
                    ${page}
                </button>
            `;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                html += '<span class="pagination-dots">...</span>';
            }
            const lastOffset = (totalPages - 1) * this.currentLimit;
            html += `
                <button 
                    class="btn-page" 
                    onclick="window.loadHistory(${lastOffset})">
                    ${totalPages}
                </button>
            `;
        }

        html += '</div>';

        const nextOffset = currentPage * this.currentLimit;
        html += `
            <button 
                class="btn-pagination" 
                onclick="window.loadHistory(${nextOffset})" 
                ${currentPage === totalPages ? 'disabled' : ''}>
                Вперёд →
            </button>
        `;

        html += '</div>';

        const from = this.currentOffset + 1;
        const to = Math.min(this.currentOffset + this.currentLimit, this.totalRecords);
        html += `
            <div class="pagination-info">
                Показано ${from}–${to} из ${this.totalRecords} записей
            </div>
        `;

        container.innerHTML = html;
    }

    static createHistoryItem(calc) {
        console.log('Создание карточки для:', calc);
        
        const rawCalcType = calc.type || calc.calc_type || 'unknown';
        
        const calcType = typeof rawCalcType === 'string' 
            ? rawCalcType.replace(/_/g, '-') 
            : 'unknown';
        
        const icon = CONFIG.CALC_TYPE_ICONS[calcType] 
            || CONFIG.CALC_TYPE_ICONS[rawCalcType] 
            || '📊';
            
        const typeName = CONFIG.CALC_TYPE_LABELS[calcType] 
            || CONFIG.CALC_TYPE_LABELS[rawCalcType] 
            || rawCalcType;
        
        const date = new Date(calc.created_at).toLocaleString('ru-RU');

        console.log('Карточка:', { 
            rawCalcType, 
            calcType, 
            icon, 
            typeName 
        });

        return `
            <div class="history-item">
                <div class="history-icon">${icon}</div>
                <div class="history-content">
                    <div class="history-title">${typeName}</div>
                    <div class="history-date">${date}</div>
                    <div class="history-result">Результат: ${calc.result}</div>
                    ${calc.interpretation ? `<div class="history-interpretation">${calc.interpretation}</div>` : ''}
                </div>
                <button class="history-delete" onclick="window.deleteCalculation(${calc.id})" title="Удалить">
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
            
            await this.loadHistory(this.currentOffset);

        } catch (error) {
            UIService.showError('Ошибка удаления');
            console.error('Delete error:', error);
        }
    }
}

window.HistoryService = HistoryService;
