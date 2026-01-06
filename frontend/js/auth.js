import { StorageService } from './storage.js';
import { UIService } from './ui.js';

export class AuthService {

    static generateUserId() {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substring(2, 9);
        return `user_${timestamp}_${random}`;
    }

    static autoInit() {
        let userId = StorageService.getUserId();

        if (!userId) {
            // Генерируем новый ID если его нет
            userId = this.generateUserId();
            StorageService.setUserId(userId);
            console.log('Создан новый пользователь:', userId);
            UIService.showSuccess(`Добро пожаловать! Ваш ID: ${userId}`);
        } else {
            console.log('Пользователь найден:', userId);
        }

        UIService.setInputValue('userId', userId);

        return userId;
    }


    static register(userId) {
        if (!userId || userId.trim() === '') {
            UIService.showError('Введите ID пользователя');
            return false;
        }

        const trimmedId = userId.trim();
        StorageService.setUserId(trimmedId);
        UIService.showSuccess(`ID изменён на: ${trimmedId}`);

        console.log('Пользователь обновлён:', trimmedId);
        return true;
    }

    static resetUserId() {
        const confirmed = confirm('Создать новый ID? Текущая история будет недоступна.');
        if (!confirmed) return false;

        const newUserId = this.generateUserId();
        StorageService.setUserId(newUserId);
        UIService.setInputValue('userId', newUserId);
        UIService.showSuccess(`Новый ID создан: ${newUserId}`);

        console.log('🔄 Создан новый ID:', newUserId);
        return true;
    }

    static logout() {
        const confirmed = confirm('Выйти? Вы потеряете доступ к истории.');
        if (!confirmed) return false;

        StorageService.removeUserId();
        UIService.showSuccess('Вы вышли из системы');
        UIService.setInputValue('userId', '');

        setTimeout(() => this.autoInit(), 500);

        console.log('👋 Пользователь вышел');
        return true;
    }

    static getCurrentUserId() {
        return StorageService.getUserId() || this.autoInit();
    }

    static isAuthenticated() {
        return StorageService.hasUserId();
    }

    static requireAuth() {
        if (!this.isAuthenticated()) {
            this.autoInit();
        }
        return true;
    }
}