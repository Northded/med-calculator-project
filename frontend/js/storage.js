import { CONFIG } from './config.js';

export class StorageService {
    static getUserId() {
        return localStorage.getItem(CONFIG.STORAGE_KEY);
    }

    static setUserId(userId) {
        localStorage.setItem(CONFIG.STORAGE_KEY, userId);
    }

    static removeUserId() {
        localStorage.removeItem(CONFIG.STORAGE_KEY);
    }

    static hasUserId() {
        return !!this.getUserId();
    }

    static clear() {
        localStorage.clear();
    }
}