// ─── ATOM Shared Module: Session Store & Backend Sync ───────────────
(function(window) {
  'use strict';

  class SessionStore {
    constructor(config) {
      this.storageKey = config.storageKey;
      this.activeKey = config.activeKey;
      this.apiEndpoint = config.apiEndpoint;
      this.legacyKey = config.legacyKey || null;
      this.defaultTitle = config.defaultTitle || 'Percakapan Baru';
      this.syncTimer = null;
    }

    loadLocal() {
      try {
        const raw = localStorage.getItem(this.storageKey);
        if (raw) return JSON.parse(raw);
        
        // Legacy migration
        if (this.legacyKey) {
          const old = localStorage.getItem(this.legacyKey);
          if (old) {
            const parsed = JSON.parse(old);
            if (Array.isArray(parsed) && parsed.length > 0) {
              const firstUser = parsed.find(m => m.role === 'user');
              const title = firstUser ? firstUser.content.slice(0, 32) : 'Percakapan Sebelumnya';
              const defaultSession = {
                id: 'sess_' + Date.now(),
                title: title,
                updatedAt: Date.now(),
                messages: parsed
              };
              this.saveLocal([defaultSession], defaultSession.id);
              return [defaultSession];
            }
          }
        }
      } catch (e) {
        console.warn(`[SESSION LOAD ERROR] ${this.storageKey}:`, e);
      }
      return [];
    }

    saveLocal(sessions, activeId) {
      try {
        localStorage.setItem(this.storageKey, JSON.stringify(sessions));
        if (activeId) {
          localStorage.setItem(this.activeKey, activeId);
        }
      } catch (e) {
        console.warn(`[SESSION SAVE LOCAL ERROR] ${this.storageKey}:`, e);
      }
    }

    getActiveId() {
      return localStorage.getItem(this.activeKey) || null;
    }

    setActiveId(id) {
      if (id) localStorage.setItem(this.activeKey, id);
    }

    async syncWithBackend(localSessions, currentActiveId) {
      try {
        const res = await fetch(this.apiEndpoint);
        if (!res.ok) return null;
        const data = await res.json();
        const serverSessions = (data && Array.isArray(data.sessions)) ? data.sessions : [];

        const isClientEmpty = !localSessions || localSessions.length === 0 ||
          (localSessions.length === 1 && (!localSessions[0].messages || localSessions[0].messages.length === 0));

        // Case 1: Client is empty, but server has sessions
        if (isClientEmpty && serverSessions.length > 0) {
          const serverHasMessages = serverSessions.some(s => s.messages && s.messages.length > 0);
          if (serverHasMessages) {
            const activeId = data.active_id || serverSessions[0].id;
            this.saveLocal(serverSessions, activeId);
            return { sessions: serverSessions, activeId: activeId };
          }
        }

        // Case 2: Client has data, sync up to server
        if (localSessions && localSessions.length > 0) {
          this.pushToBackend(localSessions, currentActiveId, true);
        }
      } catch (err) {
        console.warn(`[SESSION SYNC ERROR] ${this.apiEndpoint}:`, err);
      }
      return null;
    }

    pushToBackend(sessions, activeId, immediate = false) {
      if (this.syncTimer) {
        clearTimeout(this.syncTimer);
        this.syncTimer = null;
      }

      const doPush = async () => {
        try {
          await fetch(this.apiEndpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sessions, active_id: activeId })
          });
        } catch (err) {
          console.warn(`[SESSION PUSH ERROR] ${this.apiEndpoint}:`, err);
        }
      };

      if (immediate) {
        doPush();
      } else {
        this.syncTimer = setTimeout(doPush, 1000);
      }
    }
  }

  window.ATOM_SessionStore = SessionStore;
})(window);

