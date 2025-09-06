/**
 * IndexedDB wrapper for offline storage
 * Handles offline data storage and synchronization
 */

class IDBManager {
    constructor(dbName = 'GramOthiDB', version = 1) {
        this.dbName = dbName;
        this.version = version;
        this.db = null;
    }

    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.version);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Create object stores
                if (!db.objectStoreNames.contains('classes')) {
                    db.createObjectStore('classes', { keyPath: 'id' });
                }
                
                if (!db.objectStoreNames.contains('quizzes')) {
                    db.createObjectStore('quizzes', { keyPath: 'id' });
                }
                
                if (!db.objectStoreNames.contains('slides')) {
                    db.createObjectStore('slides', { keyPath: 'id' });
                }
                
                if (!db.objectStoreNames.contains('progress')) {
                    db.createObjectStore('progress', { keyPath: 'id' });
                }
                
                if (!db.objectStoreNames.contains('offlineQueue')) {
                    db.createObjectStore('offlineQueue', { keyPath: 'id', autoIncrement: true });
                }
            };
        });
    }

    async add(storeName, data) {
        if (!this.db) await this.init();
        
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        return store.add(data);
    }

    async get(storeName, key) {
        if (!this.db) await this.init();
        
        const transaction = this.db.transaction([storeName], 'readonly');
        const store = transaction.objectStore(storeName);
        return store.get(key);
    }

    async getAll(storeName) {
        if (!this.db) await this.init();
        
        const transaction = this.db.transaction([storeName], 'readonly');
        const store = transaction.objectStore(storeName);
        return store.getAll();
    }

    async update(storeName, data) {
        if (!this.db) await this.init();
        
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        return store.put(data);
    }

    async delete(storeName, key) {
        if (!this.db) await this.init();
        
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        return store.delete(key);
    }

    async clear(storeName) {
        if (!this.db) await this.init();
        
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        return store.clear();
    }
}

// Initialize global IDB manager
window.idb = new IDBManager();

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.idb.init().catch(console.error);
});
