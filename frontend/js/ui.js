export class UIService {
    static showError(message) {
        this.showNotification(message, 'error');
    }

    static showSuccess(message) {
        this.showNotification(message, 'success-msg');
    }

    static showNotification(message, type) {
        const existing = document.querySelector(`.${type}`);
        if (existing) existing.remove();

        const notification = document.createElement('div');
        notification.className = type;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => notification.remove(), 3000);
    }

    static showResult(containerId, data, className) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="result-value">${data.value}</div>
            <div class="result-interpretation">${data.interpretation}</div>
            ${data.unit ? `<div class="result-unit">${data.unit}</div>` : ''}
        `;

        container.className = `result-box ${className}`;
        container.style.display = 'block';
    }

    static hideResult(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.style.display = 'none';
        }
    }

    static setInputValue(inputId, value) {
        const input = document.getElementById(inputId);
        if (input) input.value = value;
    }

    static getInputValue(inputId) {
        const input = document.getElementById(inputId);
        return input ? input.value : null;
    }

    static clearInput(inputId) {
        this.setInputValue(inputId, '');
    }

    static disableButton(buttonId, disabled = true) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.disabled = disabled;
            button.style.opacity = disabled ? '0.6' : '1';
        }
    }
}
