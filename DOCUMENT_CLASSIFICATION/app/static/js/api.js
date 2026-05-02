/**
 * API Client - Fetch wrapper with JWT auth, error handling, and retries
 */
const API_BASE = '/api';
const TOKEN_KEY = 'smartdoc_token';
const USER_KEY  = 'smartdoc_user';

const api = {
  // ── Token helpers ──────────────────────────────
  getToken()         {
    const t = localStorage.getItem(TOKEN_KEY);
    // Guard against stale 'undefined' / 'null' strings stored by old code
    return (t && t !== 'undefined' && t !== 'null') ? t : null;
  },
  setToken(t)        { if (t && t !== 'undefined') localStorage.setItem(TOKEN_KEY, t); },
  clearToken()       { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY); },
  getUser()          { try { return JSON.parse(localStorage.getItem(USER_KEY)); } catch { return null; } },
  setUser(u)         { localStorage.setItem(USER_KEY, JSON.stringify(u)); },
  isAuthenticated()  { return !!this.getToken(); },

  // ── Core request ───────────────────────────────
  async request(method, path, body = null, isForm = false) {
    const headers = {};
    const token = this.getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (!isForm && body) headers['Content-Type'] = 'application/json';

    const opts = {
      method,
      headers,
      body: isForm ? body : (body ? JSON.stringify(body) : null),
    };

    const res = await fetch(API_BASE + path, opts);

    // Handle 401 / 422 – both mean the token is missing or invalid
    if (res.status === 401 || res.status === 422) {
      this.clearToken();
      app.showAuth();
      return { success: false, error: 'Session expired. Please sign in again.' };
    }

    try {
      return await res.json();
    } catch {
      return { success: false, error: `HTTP ${res.status}` };
    }
  },

  get(path)           { return this.request('GET', path); },
  post(path, body)    { return this.request('POST', path, body); },
  patch(path, body)   { return this.request('PATCH', path, body); },
  delete(path)        { return this.request('DELETE', path); },
  upload(path, form)  { return this.request('POST', path, form, true); },
  uploadWithSignal(path, form, signal) {
    const headers = {};
    const token = this.getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return fetch(API_BASE + path, { method: 'POST', headers, body: form, signal })
      .then(res => res.json())
      .catch(e => ({ success: false, error: e.message }));
  },

  // ── Auth endpoints ─────────────────────────────
  // Verify stored token is still valid against the server
  async verifyToken() {
    if (!this.getToken()) return false;
    const res = await this.get('/auth/verify');
    return res.success === true;
  },

  async login(email, password) {
    const res = await this.post('/auth/login', { email, password });
    if (res.success) { this.setToken(res.token); this.setUser(res.user); }    return res;
  },
  async register(email, password, full_name) {
    const res = await this.post('/auth/register', { email, password, full_name });
    if (res.success) { this.setToken(res.token); this.setUser(res.user); }
    return res;
  },
  async autoLogin() {
    const res = await this.post('/auth/auto-login', {});
    if (res.success) { this.setToken(res.token); this.setUser(res.user); }
    return res;
  },
  logout() { this.clearToken(); window.location.reload(); },

  // ── Document endpoints ─────────────────────────
  getDocuments(params = {}) {
    const q = new URLSearchParams(params).toString();
    return this.get(`/documents${q ? '?' + q : ''}`);
  },
  getDocument(id)            { return this.get(`/documents/${id}`); },
  deleteDocument(id, hard)   { return this.delete(`/documents/${id}${hard ? '?hard=true' : ''}`); },
  bulkDeleteDocuments(ids)   { return this.post('/documents/bulk/delete', { ids }); },
  updateDocument(id, data)   { return this.patch(`/documents/${id}`, data); },
  downloadUrl(id)            { return `${API_BASE}/documents/${id}/download?token=${this.getToken()}`; },

  // ── Search ─────────────────────────────────────
  search(params = {}) {
    const q = new URLSearchParams(params).toString();
    return this.get(`/search${q ? '?' + q : ''}`);
  },

  // ── Dashboard ──────────────────────────────────
  getStats()            { return this.get('/dashboard/stats'); },
  getRecent(limit = 8)  { return this.get(`/dashboard/recent?limit=${limit}`); },
  getActivity()         { return this.get('/dashboard/activity?limit=15'); },
  getChartData(days=30) { return this.get(`/dashboard/chart/uploads?days=${days}`); },

  // ── Folders ────────────────────────────────────
  suggestFolder(text)                     { return this.post('/folders/suggest', { text, return_all_predictions: true }); },
  confirmFolder(docId, folder)            { return this.post(`/folders/confirm/${docId}`, { folder }); },
  submitFeedback(docId, corrected, note)  { return this.post(`/folders/feedback/${docId}`, { corrected_label: corrected, feedback_text: note }); },
  getFolderStats()                        { return this.get('/folders/stats'); },

  // ── VFS Views ──────────────────────────────────
  getViews()                { return this.get('/views'); },
  getViewTree(viewName)     { return this.get(`/views/tree?view=${encodeURIComponent(viewName)}`); },
  browseView(viewName, path, page = 1, perPage = 50) {
    const q = new URLSearchParams({ view: viewName, path, page, per_page: perPage });
    return this.get(`/views/browse?${q}`);
  },
  getDocPaths(docId)        { return this.get(`/views/paths/${docId}`); },
  postViewTemplate(viewName, displayName, l1, l2, l3) {
    return this.post('/views/templates', {
      view_name: viewName, display_name: displayName,
      level1_attr: l1, level2_attr: l2 || null, level3_attr: l3 || null,
    });
  },
  deleteViewTemplate(viewName) {
    return this.delete(`/views/templates/${encodeURIComponent(viewName)}`);
  },
  reprocessDocument(docId, force = true) {
    return this.post(`/documents/${docId}/reprocess`, { force });
  },

  // ── Local Indexer (Phase A) ────────────────────
  indexerFolders()              { return this.get('/index/folders'); },
  indexerAddFolder(path, recursive = true) {
    return this.post('/index/folders', { folder_path: path, recursive });
  },
  indexerRemoveFolder(id)       { return this.delete(`/index/folders/${id}`); },
  indexerStartScan(path)        { return this.post('/index/scan', { folder_path: path }); },
  indexerScanProgress(taskId)   { return this.get(`/index/scan/${taskId}`); },
  indexerScanPC()               { return this.post('/index/scan-pc', {}); },
  indexerSearch(q, params = {}) {
    const p = new URLSearchParams({ q, ...params }).toString();
    return this.get(`/index/search?${p}`);
  },
  indexerFiles(params = {}) {
    const p = new URLSearchParams(params).toString();
    return this.get(`/index/files${p ? '?' + p : ''}`);
  },
  indexerFile(id)               { return this.get(`/index/files/${id}`); },
  indexerRecordOpen(id)         { return this.post(`/index/files/${id}/open`, {}); },
  indexerRecentlyOpened(limit=20){ return this.get(`/index/recently-opened?limit=${limit}`); },
  indexerStats()                { return this.get('/index/stats'); },
  indexerSemanticSearch(q, {ext, folder, limit=20}={}) {
    const p = new URLSearchParams({q});
    if (ext)    p.set('ext', ext);
    if (folder) p.set('folder', folder);
    p.set('limit', limit);
    return this.get(`/index/semantic-search?${p}`);
  },
  indexerEmbedStatus()          { return this.get('/index/embed-status'); },
  indexerAsk(question, top_k=5){ return this.post('/index/ask', {question, top_k}); },
  indexerOllamaStatus()         { return this.get('/index/ollama-status'); },
  // SSE streaming — returns an EventSource-like object via fetch
  indexerAskStream(question, top_k=5, model='') {
    const token = localStorage.getItem('smartdoc_token') || '';
    return fetch('/api/index/ask-stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ question, top_k, model }),
    });
  },
};
