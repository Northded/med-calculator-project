import { CONFIG } from './config.js';
import { StorageService } from './storage.js';

export class ChartsService {
    static charts = {};

    static async loadCharts() {
        const userId = StorageService.getUserId();
        if (!userId) {
            console.warn('Нет userId для загрузки графиков');
            return;
        }

        await this.loadIMTChart(userId);
        await this.loadCaloriesChart(userId);
        await this.loadPressureChart(userId);
    }

    static async loadIMTChart(userId) {
        try {
            const response = await fetch(
                `${CONFIG.API_URL}/calculations/history?user_id=${userId}&calc_type=imt&limit=30`
            );
            const data = await response.json();

            if (!data.calculations || data.calculations.length === 0) {
                this.showNoData('imtChart', '📊 Нет данных по ИМТ');
                return;
            }

            const sortedData = data.calculations.sort((a, b) => 
                new Date(a.created_at) - new Date(b.created_at)
            );

            const labels = sortedData.map(c => 
                new Date(c.created_at).toLocaleDateString('ru-RU', {day: '2-digit', month: '2-digit'})
            );
            const values = sortedData.map(c => c.result);

            this.createChart('imtChart', {
                labels,
                datasets: [{
                    label: 'ИМТ',
                    data: values,
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            }, {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: { display: true, text: 'ИМТ' }
                    },
                    x: {
                        title: { display: true, text: 'Дата' }
                    }
                }
            });
        } catch (err) {
            console.error('Ошибка загрузки графика ИМТ:', err);
            this.showNoData('imtChart', '⚠️ Ошибка загрузки');
        }
    }

    static async loadCaloriesChart(userId) {
        try {
            const response = await fetch(
                `${CONFIG.API_URL}/calculations/history?user_id=${userId}&calc_type=calories&limit=30`
            );
            const data = await response.json();

            if (!data.calculations || data.calculations.length === 0) {
                this.showNoData('caloriesChart', '🔥 Нет данных по калориям');
                return;
            }

            const sortedData = data.calculations.sort((a, b) => 
                new Date(a.created_at) - new Date(b.created_at)
            );

            const labels = sortedData.map(c => 
                new Date(c.created_at).toLocaleDateString('ru-RU', {day: '2-digit', month: '2-digit'})
            );
            const values = sortedData.map(c => c.result);

            this.createChart('caloriesChart', {
                labels,
                datasets: [{
                    label: 'TDEE (ккал)',
                    data: values,
                    borderColor: '#2196F3',
                    backgroundColor: 'rgba(33, 150, 243, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            }, {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: { display: true, text: 'ккал/день' }
                    },
                    x: {
                        title: { display: true, text: 'Дата' }
                    }
                }
            });
        } catch (err) {
            console.error('Ошибка загрузки графика калорий:', err);
            this.showNoData('caloriesChart', '⚠️ Ошибка загрузки');
        }
    }

    static async loadPressureChart(userId) {
        try {
            const response = await fetch(
                `${CONFIG.API_URL}/calculations/history?user_id=${userId}&calc_type=blood_pressure&limit=30`
            );
            const data = await response.json();

            if (!data.calculations || data.calculations.length === 0) {
                this.showNoData('pressureChart', '❤️ Нет данных по давлению');
                return;
            }

            const sortedData = data.calculations.sort((a, b) => 
                new Date(a.created_at) - new Date(b.created_at)
            );

            const labels = sortedData.map(c => 
                new Date(c.created_at).toLocaleDateString('ru-RU', {day: '2-digit', month: '2-digit'})
            );
            
            const systolicData = sortedData.map(c => {
                const input = JSON.parse(c.input_data);
                return input.systolic;
            });
            
            const diastolicData = sortedData.map(c => {
                const input = JSON.parse(c.input_data);
                return input.diastolic;
            });

            this.createChart('pressureChart', {
                labels,
                datasets: [
                    {
                        label: 'Систолическое',
                        data: systolicData,
                        borderColor: '#f44336',
                        backgroundColor: 'rgba(244, 67, 54, 0.1)',
                        tension: 0.3,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'Диастолическое',
                        data: diastolicData,
                        borderColor: '#FF9800',
                        backgroundColor: 'rgba(255, 152, 0, 0.1)',
                        tension: 0.3,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }
                ]
            }, {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: { display: true, text: 'мм рт. ст.' }
                    },
                    x: {
                        title: { display: true, text: 'Дата' }
                    }
                }
            });
        } catch (err) {
            console.error('Ошибка загрузки графика давления:', err);
            this.showNoData('pressureChart', '⚠️ Ошибка загрузки');
        }
    }

    static createChart(canvasId, data, options) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.warn(`Canvas ${canvasId} не найден`);
            return;
        }

        const container = canvas.parentElement;
        container.innerHTML = '';
        
        const newCanvas = document.createElement('canvas');
        newCanvas.id = canvasId;
        container.appendChild(newCanvas);

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        this.charts[canvasId] = new Chart(newCanvas, {
            type: 'line',
            data,
            options
        });
    }

    static showNoData(canvasId, message) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const container = canvas.parentElement;
        container.innerHTML = `
            <div class="chart-no-data">
                <div class="chart-no-data-icon">📊</div>
                <div class="chart-no-data-text">${message}</div>
                <p style="font-size: 0.85em; color: #999; margin-top: 10px;">
                    Выполните расчёты для отображения графика
                </p>
            </div>
        `;
    }
}

window.loadCharts = () => ChartsService.loadCharts();
