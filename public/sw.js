/**
 * A.T.O.M. — Background Chat Service Worker
 * Keeps in-flight /api/chat requests alive across page navigation,
 * tab switches, and session switches, persisting results in IndexedDB.
 */

const DB_NAME = 'atom_bg_db';
const DB_VERSION = 1;
const STORE_NAME = 'chat_jobs';
const CHANNEL_NAME = 'atom_chat_bg';

const activeControllers = new Map();
const bgChannel = typeof BroadcastChannel !== 'undefined' ? new BroadcastChannel(CHANNEL_NAME) : null;

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'jobId' });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function putJob(job) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    tx.objectStore(STORE_NAME).put(job);
    tx.oncomplete = () => {
      db.close();
      resolve();
    };
    tx.onerror = () => {
      db.close();
      reject(tx.error);
    };
  });
}

async function getJob(jobId) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const req = tx.objectStore(STORE_NAME).get(jobId);
    req.onsuccess = () => {
      db.close();
      resolve(req.result || null);
    };
    req.onerror = () => {
      db.close();
      reject(req.error);
    };
  });
}

async function getAllJobs() {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const req = tx.objectStore(STORE_NAME).getAll();
    req.onsuccess = () => {
      db.close();
      resolve(Array.isArray(req.result) ? req.result : []);
    };
    req.onerror = () => {
      db.close();
      reject(req.error);
    };
  });
}

async function deleteJob(jobId) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    tx.objectStore(STORE_NAME).delete(jobId);
    tx.oncomplete = () => {
      db.close();
      resolve();
    };
    tx.onerror = () => {
      db.close();
      reject(tx.error);
    };
  });
}

async function notifyAllClients(payload) {
  try {
    bgChannel?.postMessage(payload);
  } catch {
    // Ignore BroadcastChannel errors
  }
  try {
    const clientList = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const client of clientList) {
      client.postMessage(payload);
    }
  } catch {
    // Ignore matchAll errors
  }
}

async function handleChatStart(job, sourceClient) {
  if (!job || !job.jobId || !job.body) return;

  const controller = new AbortController();
  activeControllers.set(job.jobId, controller);

  const runningRecord = {
    ...job,
    status: 'running',
    committed: false,
    startedAt: job.startedAt || Date.now()
  };

  try {
    await putJob(runningRecord);
  } catch {
    // Continue even if IDB fails transiently
  }

  if (sourceClient && typeof sourceClient.postMessage === 'function') {
    try {
      sourceClient.postMessage({ type: 'CHAT_JOB_ACK', jobId: job.jobId });
    } catch {
      // Ignore
    }
  }

  await notifyAllClients({ type: 'CHAT_JOB_STARTED', job: runningRecord });

  let finishedRecord;
  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(job.body),
      signal: controller.signal
    });

    if (!resp.ok) {
      const errJson = await resp.json().catch(() => ({}));
      throw new Error(errJson.detail || errJson.error || errJson.message || `HTTP ${resp.status}`);
    }

    const result = await resp.json();
    finishedRecord = {
      ...runningRecord,
      status: 'completed',
      result,
      committed: false,
      finishedAt: Date.now()
    };
  } catch (err) {
    if (err && err.name === 'AbortError') {
      finishedRecord = {
        ...runningRecord,
        status: 'aborted',
        committed: false,
        finishedAt: Date.now()
      };
    } else {
      finishedRecord = {
        ...runningRecord,
        status: 'error',
        error: (err && err.message) ? err.message : 'Gagal menghubungi API. Periksa koneksi.',
        committed: false,
        finishedAt: Date.now()
      };
    }
  } finally {
    activeControllers.delete(job.jobId);
  }

  try {
    await putJob(finishedRecord);
  } catch {
    // Ignore IDB failure
  }

  await notifyAllClients({ type: 'CHAT_JOB_DONE', job: finishedRecord });
}

async function handleChatAbort(jobId) {
  if (!jobId) return;
  const controller = activeControllers.get(jobId);
  if (controller) {
    controller.abort();
    return;
  }

  // Fallback: if worker restarted and record is still marked running, mark aborted
  try {
    const existing = await getJob(jobId);
    if (existing && existing.status === 'running') {
      const abortedRecord = {
        ...existing,
        status: 'aborted',
        committed: false,
        finishedAt: Date.now()
      };
      await putJob(abortedRecord);
      await notifyAllClients({ type: 'CHAT_JOB_DONE', job: abortedRecord });
    }
  } catch {
    // Ignore
  }
}

async function handleChatPing(event) {
  try {
    const allJobs = await getAllJobs();
    const now = Date.now();
    for (const rec of allJobs) {
      if (rec && rec.status === 'running' && !activeControllers.has(rec.jobId)) {
        if (now - (rec.startedAt || 0) > 2000) {
          const failedRecord = {
            ...rec,
            status: 'error',
            error: 'Koneksi background worker terputus saat memproses pesan.',
            committed: false,
            finishedAt: now
          };
          await putJob(failedRecord);
          await notifyAllClients({ type: 'CHAT_JOB_DONE', job: failedRecord });
        }
      }
    }
  } catch {
    // Ignore
  }

  const reply = {
    type: 'CHAT_PONG',
    activeJobIds: Array.from(activeControllers.keys())
  };

  if (event.ports && event.ports[0]) {
    event.ports[0].postMessage(reply);
  } else if (event.source && typeof event.source.postMessage === 'function') {
    event.source.postMessage(reply);
  }
}

self.addEventListener('message', (event) => {
  const data = event.data || {};
  if (data.type === 'CHAT_START') {
    const p = handleChatStart(data.job, event.source);
    if (typeof event.waitUntil === 'function') {
      event.waitUntil(p);
    }
  } else if (data.type === 'CHAT_ABORT') {
    const p = handleChatAbort(data.jobId);
    if (typeof event.waitUntil === 'function') {
      event.waitUntil(p);
    }
  } else if (data.type === 'CHAT_PING') {
    const p = handleChatPing(event);
    if (typeof event.waitUntil === 'function') {
      event.waitUntil(p);
    }
  } else if (data.type === 'CHAT_MARK_COMMITTED') {
    if (data.jobId) {
      const p = deleteJob(data.jobId).catch(() => {});
      if (typeof event.waitUntil === 'function') {
        event.waitUntil(p);
      }
    }
  }
});
