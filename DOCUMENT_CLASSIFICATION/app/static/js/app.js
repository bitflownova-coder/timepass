/**
 * SmartDoc AI - Main Application
 * Single-Page Application handling all views and state
 */

// ─────────────────────────────────────────────────
// Utility helpers
// ─────────────────────────────────────────────────
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];
const esc = s => String(s ?? '').replace(/[<>"'&]/g,
  c => ({'<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;','&':'&amp;'}[c]));
const fmt_size = b => b > 1048576 ? (b/1048576).toFixed(1)+' MB'
                    : b > 1024    ? (b/1024).toFixed(0)+' KB'
                    :               b+' B';
const fmt_date = d => d ? new Date(d).toLocaleDateString('en-US',
  {month:'short',day:'numeric',year:'numeric'}) : '—';
const conf_class = c => c >= .80 ? 'conf-high' : c >= .60 ? 'conf-medium' : 'conf-low';
const conf_label = c => c >= .80 ? 'High'      : c >= .60 ? 'Medium'      : 'Low';

function _renderContinueReading(files) {
  if (!files || files.length === 0) return '';
  const items = files.map(f => {
    const name   = esc(f.filename || f.file_path?.split(/[/\\]/).pop() || 'Unknown');
    const folder = esc((f.file_path || '').replace(/[/\\][^/\\]+$/, ''));
    const label  = esc(f.predicted_label || 'Unknown');
    const ext    = esc((f.file_path || '').split('.').pop().toUpperCase());
    const when   = f.last_opened ? fmt_date(f.last_opened) : '—';
    const count  = f.open_count || 1;
    return `
      <div class="cr-item" onclick="app._localFileOpen(${f.id}, ${JSON.stringify(f.file_path || '')})">
        <div class="cr-icon">${ext}</div>
        <div class="cr-info">
          <div class="cr-name">${name}</div>
          <div class="cr-meta">${folder}</div>
        </div>
        <div class="cr-right">
          <span class="category-badge">${label}</span>
          <div class="cr-when">${when} &middot; ${count}×</div>
        </div>
      </div>`;
  }).join('');
  return `
    <div class="card" style="margin-bottom:1.5rem">
      <div class="card-header">
        <h3>&#128214; Continue Reading</h3>
        <button class="btn btn-sm btn-secondary" onclick="app.navigate('local-search')">Browse All</button>
      </div>
      <div class="card-body" style="padding:0">${items}</div>
    </div>`;
}
function _debounce(fn, ms) {
  let t;
  return function(...args) { clearTimeout(t); t = setTimeout(() => fn.apply(this, args), ms); };
}

function showAlert(msg, type = 'error', parent = null) {
  const el = document.createElement('div');
  el.className = `alert alert-${type}`;
  el.textContent = msg;
  const container = parent || $('#alert-container');
  if (!container) return;
  container.innerHTML = '';
  container.appendChild(el);
  setTimeout(() => el.remove(), 5000);
}

function showModal(html) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.innerHTML = html;
  overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
  return overlay;
}

// ─────────────────────────────────────────────────
// SVG Icons
// ─────────────────────────────────────────────────
const ICONS = {
  home:     `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z"/><path d="M9 21V12h6v9"/></svg>`,
  upload:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>`,
  docs:     `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`,
  search:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`,
  folder:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>`,
  logout:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>`,
  trash:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/></svg>`,
  download: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`,
  edit:     `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
  file:     `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`,
  chart:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
  open:     `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>`,
  views:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>`,
};

// ─────────────────────────────────────────────────
// File type helpers
// ─────────────────────────────────────────────────
function _docExt(name) {
  const e = (name || '').split('.').pop().toLowerCase();
  if (e === 'pdf')                              return 'pdf';
  if (['docx','doc'].includes(e))               return 'docx';
  if (e === 'txt')                              return 'txt';
  if (['jpg','jpeg','png','gif','bmp','webp'].includes(e)) return 'img';
  return 'other';
}

// ─────────────────────────────────────────────────
// Smart file opener — PDF/images/txt → browser tab
// Word/Excel/PPT → download (OS opens with installed app)
// ─────────────────────────────────────────────────
async function openFile(docId, filename) {
  // Ask the server to decrypt the file and open it with the OS default app
  // (PDF → Acrobat/Edge, docx → Word, image → Photos, etc.)
  try {
    const res = await api.post(`/documents/${docId}/open`);
    if (!res.success) alert('Could not open file: ' + (res.error || 'Unknown error'));
  } catch (err) {
    alert('Failed to open: ' + err.message);
  }
}



// ─────────────────────────────────────────────────
// App Controller
// ─────────────────────────────────────────────────
const app = {
  currentView: null,
  uploadQueue: [],
  docsPage: 1,
  searchPage: 1,
  vfsState: {
    viewName: 'by_type',
    expanded: new Set(),
    browsePath: null,
  },

  async init() {
    // Single-user local mode: silently auto-login. No login screen.
    if (api.isAuthenticated()) {
      const valid = await api.verifyToken();
      if (valid) { this.showApp(); return; }
      api.clearToken();
    }
    const res = await api.autoLogin();
    if (res && res.success) {
      this.showApp();
    } else {
      // Last-resort fallback: show auth UI if auto-login failed
      this.showAuth();
    }
  },

  // ── Auth ──────────────────────────────────────
  showAuth() {
    $('#auth-view').classList.remove('hidden');
    $('#app-view').classList.add('hidden');
    this._bindAuth();
  },

  _bindAuth() {
    $$('.auth-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        $$('.auth-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        $('#login-form').classList.toggle('hidden', tab.dataset.tab !== 'login');
        $('#register-form').classList.toggle('hidden', tab.dataset.tab !== 'register');
        $('#auth-alert').innerHTML = '';
      });
    });

    $('#login-form').addEventListener('submit', async e => {
      e.preventDefault();
      const btn = e.target.querySelector('button[type=submit]');
      btn.disabled = true; btn.textContent = 'Signing in…';
      const res = await api.login(
        $('#login-email').value.trim(),
        $('#login-password').value,
      );
      btn.disabled = false; btn.textContent = 'Sign In';
      if (res.success) { this.showApp(); }
      else { showAlert(res.error || 'Login failed', 'error', $('#auth-alert')); }
    });

    $('#register-form').addEventListener('submit', async e => {
      e.preventDefault();
      const btn = e.target.querySelector('button[type=submit]');
      btn.disabled = true; btn.textContent = 'Creating account…';
      const res = await api.register(
        $('#reg-email').value.trim(),
        $('#reg-password').value,
        $('#reg-name').value.trim(),
      );
      btn.disabled = false; btn.textContent = 'Create Account';
      if (res.success) { this.showApp(); }
      else { showAlert(res.error || 'Registration failed', 'error', $('#auth-alert')); }
    });
  },

  // ── App Shell ─────────────────────────────────
  showApp() {
    $('#auth-view').classList.add('hidden');
    $('#app-view').classList.remove('hidden');

    const user = api.getUser();
    if (user) {
      $('#user-name').textContent  = user.full_name || user.email;
      $('#user-email').textContent = user.email;
      $('#user-avatar').textContent = (user.full_name || user.email)[0].toUpperCase();
    }

    this._bindNav();
    this.navigate('dashboard');
  },

  _bindNav() {
    $$('.nav-item[data-view]').forEach(item => {
      item.addEventListener('click', () => this.navigate(item.dataset.view));
    });
    $('#logout-btn').addEventListener('click', () => api.logout());
  },

  navigate(view) {
    $$('.nav-item[data-view]').forEach(i => {
      i.classList.toggle('active', i.dataset.view === view);
    });
    this.currentView = view;
    const c = $('#content');
    switch (view) {
      case 'dashboard': this.renderDashboard(c); break;
      case 'upload':    this.renderUpload(c);    break;
      case 'documents': this.renderDocuments(c); break;
      case 'search':    this.renderSearch(c);    break;
      case 'folders':   this.renderFolders(c);   break;
      case 'views':     this.renderViews(c);     break;
      case 'indexer':   this.renderIndexer(c);   break;
      case 'local-search': this.renderLocalSearch(c); break;
      case 'ask':          this.renderAsk(c);         break;
    }
    const titles = { dashboard: 'Dashboard', upload: 'Upload Documents',
                     documents: 'My Documents', search: 'Search', folders: 'Folders',
                     views: 'Smart Views', indexer: 'File Indexer',
                     'local-search': 'Search My PC', ask: 'Ask My Files' };
    $('#topbar-title').textContent = titles[view] || view;
  },

  // ─────────────────────────────────────────────
  // Dashboard View
  // ─────────────────────────────────────────────
  async renderDashboard(c) {
    c.innerHTML = `<div class="spinner" style="margin:3rem auto"></div>`;
    const [stats, recent, activity, recentlyOpened] = await Promise.all([
      api.getStats(), api.getRecent(8), api.getActivity(),
      api.indexerRecentlyOpened(5).catch(() => ({ files: [] })),
    ]);

    if (!stats.success) {
      c.innerHTML = `<div class="alert alert-error">${esc(stats.error)}</div>`; return;
    }

    const catBars = (stats.categories || []).slice(0, 6).map(cat => {
      const pct = stats.total_documents > 0
        ? Math.round(cat.count / stats.total_documents * 100) : 0;
      return `
        <div style="margin-bottom:.75rem">
          <div class="flex items-center" style="justify-content:space-between;margin-bottom:.25rem">
            <span style="font-weight:600;font-size:.82rem">${esc(cat.name)}</span>
            <span style="font-size:.75rem;color:var(--text-muted)">${cat.count}</span>
          </div>
          <div class="progress-bar" style="height:8px">
            <div class="progress-fill" style="width:${pct}%"></div>
          </div>
        </div>`;
    }).join('');

    const recentRows = (recent.documents || []).map(d => `
      <tr>
        <td><span class="filename">${esc(d.original_filename)}</span></td>
        <td><span class="category-badge">${esc(d.predicted_label || 'Unknown')}</span></td>
        <td class="${conf_class(d.confidence_score)}">${Math.round((d.confidence_score||0)*100)}%</td>
        <td class="text-muted">${fmt_date(d.uploaded_at)}</td>
        <td>${fmt_size(d.file_size)}</td>
      </tr>`).join('') || `<tr><td colspan="5" class="text-center text-muted" style="padding:2rem">No documents yet</td></tr>`;

    const activityRows = (activity.activity || []).slice(0, 8).map(a => `
      <div class="flex items-center gap-2" style="padding:.5rem 0;border-bottom:1px solid var(--border)">
        <span class="category-badge" style="font-size:.68rem">${esc(a.action)}</span>
        <span style="flex:1;font-size:.8rem">${esc(a.resource_name || a.resource_type || '')}</span>
        <span class="text-muted" style="font-size:.72rem">${fmt_date(a.created_at)}</span>
      </div>`).join('') || '<div class="text-muted" style="padding:1rem 0">No activity yet</div>';

    c.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card">
          <div class="label">Total Documents</div>
          <div class="value">${stats.total_documents}</div>
          <span class="badge badge-blue">${stats.documents_this_week} this week</span>
        </div>
        <div class="stat-card">
          <div class="label">Storage Used</div>
          <div class="value">${stats.storage_used_mb} MB</div>
          <span class="badge badge-purple">${(stats.categories||[]).length} categories</span>
        </div>
        <div class="stat-card">
          <div class="label">High Confidence</div>
          <div class="value">${stats.confidence?.high ?? 0}</div>
          <span class="badge badge-green">≥ 80%</span>
        </div>
        <div class="stat-card">
          <div class="label">Needs Review</div>
          <div class="value">${(stats.confidence?.medium ?? 0) + (stats.confidence?.low ?? 0)}</div>
          <span class="badge badge-yellow">< 80%</span>
        </div>
      </div>

      ${_renderContinueReading(recentlyOpened.files || [])}

      <div class="grid-2">
        <div class="card">
          <div class="card-header"><h3>${ICONS.chart} Categories</h3></div>
          <div class="card-body">${catBars || '<p class="text-muted">No documents yet</p>'}</div>
        </div>
        <div class="card">
          <div class="card-header"><h3>Recent Activity</h3></div>
          <div class="card-body">${activityRows}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3>Recent Documents</h3>
          <button class="btn btn-sm btn-secondary" onclick="app.navigate('upload')">
            ${ICONS.upload} Upload
          </button>
        </div>
        <div class="table-wrap">
          <table>
            <thead><tr>
              <th>Filename</th><th>Category</th><th>Confidence</th>
              <th>Uploaded</th><th>Size</th>
            </tr></thead>
            <tbody>${recentRows}</tbody>
          </table>
        </div>
      </div>`;
  },

  // ─────────────────────────────────────────────
  // Upload View  — redesigned
  // ─────────────────────────────────────────────
  renderUpload(c) {
    this.uploadQueue = [];
    c.innerHTML = `
      <div id="alert-container"></div>
      <div class="upload-page">

        <p style="color:var(--text-muted);font-size:.875rem;margin-bottom:1.5rem">
          Upload documents and let AI classify them automatically into the right folders.
        </p>

        <!-- Drop zone -->
        <div class="drop-zone-wrapper" id="drop-zone">
          <input type="file" id="file-input" multiple
            accept=".pdf,.docx,.doc,.txt,.jpg,.jpeg,.png"
            style="display:none">
          <input type="file" id="folderUpload" name="files" multiple webkitdirectory
            style="display:none">

          <div class="drop-zone-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
          </div>

          <h3>Drag &amp; drop files or folders here</h3>
          <p>Drop files or an entire folder, or use the buttons below</p>

          <div class="file-type-chips">
            <span class="file-type-chip">📄 PDF</span>
            <span class="file-type-chip">📝 DOCX</span>
            <span class="file-type-chip">📃 TXT</span>
            <span class="file-type-chip">🖼 JPG / PNG</span>
            <span class="file-type-chip">📁 Folders</span>
            <span class="file-type-chip">⚡ Max 50 MB</span>
          </div>

          <div class="browse-btn-row">
            <button class="browse-btn" id="browse-btn" type="button">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              Browse Files
            </button>
            <button class="browse-btn folder-btn" id="folder-btn" type="button"
              title="Select a folder — all supported files inside will be queued for upload">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
              </svg>
              Upload Folder
            </button>
          </div>
        </div>

        <!-- Options -->
        <div class="upload-options">
          <div class="form-group" style="margin-bottom:0">
            <label>📁 Category Override <span style="font-weight:400;color:var(--text-muted)">(optional)</span></label>
            <input type="text" id="upload-category" placeholder="Leave blank — AI will classify">
            <div class="form-hint">Force a specific folder name instead of AI prediction.</div>
          </div>
          <div class="form-group" style="margin-bottom:0">
            <label>🏷 Tags <span style="font-weight:400;color:var(--text-muted)">(optional)</span></label>
            <input type="text" id="upload-tags" placeholder="e.g. 2024, invoice, q1">
            <div class="form-hint">Comma-separated tags for easier searching.</div>
          </div>
        </div>

        <!-- File queue -->
        <div class="file-queue" id="file-queue"></div>

        <!-- Summary + action -->
        <div id="upload-footer" style="display:none">
          <div class="upload-summary" id="upload-summary">
            <span class="count" id="summary-count">0 files ready</span>
            <span class="size"  id="summary-size">0 KB total</span>
          </div>
          <button class="btn btn-primary btn-block" id="upload-btn"
            style="margin-top:.75rem;padding:.75rem;font-size:.95rem;border-radius:10px">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
              style="width:18px;height:18px">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Upload &amp; Classify All
          </button>
        </div>
      </div>`;

    this._bindUpload();
  },

  _fileTypeIcon(name) {
    const ext = (name.split('.').pop() || '').toLowerCase();
    if (ext === 'pdf')                     return { cls: 'pdf',  label: 'PDF'  };
    if (['docx','doc'].includes(ext))      return { cls: 'docx', label: 'DOC'  };
    if (ext === 'txt')                     return { cls: 'txt',  label: 'TXT'  };
    if (['jpg','jpeg','png','gif','bmp','webp'].includes(ext))
                                           return { cls: 'img',  label: 'IMG'  };
    return { cls: 'other', label: ext.toUpperCase().slice(0,4) || 'FILE' };
  },

  _bindUpload() {
    const zone        = $('#drop-zone');
    const input       = $('#file-input');
    const folderInput = $('#folderUpload');

    $('#browse-btn').addEventListener('click', e => { e.stopPropagation(); input.click(); });
    $('#folder-btn').addEventListener('click', async e => {
      e.stopPropagation();
      // Use modern File System Access API when available (shows proper "Select Folder" dialog)
      if (window.showDirectoryPicker) {
        try {
          const dirHandle = await window.showDirectoryPicker({ mode: 'read' });
          const files = [];
          const readDir = async (handle) => {
            try {
              for await (const entry of handle.values()) {
                try {
                  if (entry.kind === 'file') {
                    const f = await entry.getFile();
                    files.push(f);
                  } else if (entry.kind === 'directory') {
                    await readDir(entry);
                  }
                } catch (_) { /* skip locked/inaccessible entry */ }
              }
            } catch (_) { /* skip inaccessible sub-directory */ }
          };
          await readDir(dirHandle);
          if (files.length > 0) {
            this._addFiles(files);
          }
        } catch (err) {
          // AbortError = user cancelled; any other error = fall back to webkitdirectory silently
          if (err.name !== 'AbortError') folderInput.click();
        }
      } else {
        // Fallback: webkitdirectory
        folderInput.click();
      }
    });

    // Clicking the zone itself opens the file picker (not folder)
    zone.addEventListener('click', ev => {
      if (ev.target.closest('button')) return;
      input.click();
    });

    zone.addEventListener('dragover',  e => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', e => { if (!zone.contains(e.relatedTarget)) zone.classList.remove('drag-over'); });
    zone.addEventListener('drop', e => {
      e.preventDefault(); zone.classList.remove('drag-over');
      // Use DataTransferItemList to support dropped folders
      if (e.dataTransfer.items && e.dataTransfer.items.length) {
        this._readDropItems([...e.dataTransfer.items]);
      } else {
        this._addFiles([...e.dataTransfer.files]);
      }
    });

    input.addEventListener('change', () => { this._addFiles([...input.files]); input.value = ''; });
    folderInput.addEventListener('change', () => { this._addFiles([...folderInput.files]); folderInput.value = ''; });
    $('#upload-btn')?.addEventListener('click', () => this._uploadAll());
  },

  // Recursively read dropped items (files + folders) via FileSystem API
  _readDropItems(items) {
    const entries = items
      .filter(i => i.kind === 'file')
      .map(i => i.webkitGetAsEntry ? i.webkitGetAsEntry() : null)
      .filter(Boolean);

    const collected = [];
    let pending = 0;

    const done = () => { if (pending === 0) this._addFiles(collected); };

    const readEntry = (entry) => {
      if (entry.isFile) {
        pending++;
        entry.file(f => { collected.push(f); pending--; done(); });
      } else if (entry.isDirectory) {
        const reader = entry.createReader();
        const readAll = () => {
          pending++;
          reader.readEntries(batch => {
            pending--;
            if (!batch.length) { done(); return; }
            batch.forEach(readEntry);
            readAll(); // read more (browsers return ≤100 at a time)
          });
        };
        readAll();
      }
    };

    if (!entries.length) return;
    entries.forEach(readEntry);
    // fallback if all entries resolved synchronously
    done();
  },

  _addFiles(files) {
    const ALLOWED = new Set(['pdf','docx','doc','txt','jpg','jpeg','png','gif','bmp','webp']);
    let skipped = 0;
    files.forEach(f => {
      const ext = (f.name.split('.').pop() || '').toLowerCase();
      if (!ALLOWED.has(ext)) { skipped++; return; }
      if (this.uploadQueue.find(q => q.file.name === f.name && q.file.size === f.size)) return;
      this.uploadQueue.push({ file: f, status: 'pending', progress: 0, result: null });
    });
    if (skipped > 0) showAlert(`${skipped} file${skipped > 1 ? 's' : ''} skipped (unsupported type). Accepted: PDF, DOCX, DOC, TXT, JPG, PNG, GIF, BMP, WEBP`, 'error');
    this._renderQueue();
  },

  _renderQueue() {
    const queue  = $('#file-queue');
    const footer = $('#upload-footer');
    const countEl = $('#summary-count');
    const sizeEl  = $('#summary-size');
    if (!queue) return;

    queue.innerHTML = this.uploadQueue.map((item, i) => {
      const { file, status, progress } = item;
      const icon = this._fileTypeIcon(file.name);
      const statusHtml = status === 'done'
        ? `<div class="file-status done">✔ Classified as <strong>${esc(item.result?.predicted_label || 'Unknown')}</strong> → saved to <strong>${esc(item.result?.predicted_label || 'General')}</strong></div>`
        : status === 'duplicate'
        ? `<div class="file-status done" style="color:#D97706">⚠ Already exists in <strong>${esc(item.result?.existing_folder || item.result?.predicted_label || 'existing folder')}</strong></div>`
        : status === 'error'
        ? `<div class="file-status err">✖ ${esc(item.errorMsg || 'Upload failed')}</div>`
        : status === 'uploading'
        ? `<div class="file-status uploading">⟳ Uploading…</div>`
        : `<div class="file-status pending">Ready to upload</div>`;

      return `
        <div class="file-item ${status === 'done' || status === 'duplicate' ? 'success' : status === 'uploading' ? 'uploading' : ''}" id="fitem-${i}">
          <div class="file-type-icon ${icon.cls}">${icon.label}</div>
          <div class="file-details">
            <div class="file-name" title="${esc(file.name)}">${esc(file.name)}</div>
            <div class="file-meta">${fmt_size(file.size)}</div>
            <div class="progress-wrap">
              <div class="progress-bar"><div class="progress-fill" id="fprog-${i}" style="width:${progress}%"></div></div>
            </div>
            ${statusHtml}
          </div>
          ${status === 'pending' ? `
            <button class="btn-remove" onclick="app._removeFile(${i})" title="Remove">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>` : ''}
        </div>`;
    }).join('');

    const pending = this.uploadQueue.filter(q => q.status === 'pending');
    if (footer) footer.style.display = this.uploadQueue.length ? '' : 'none';
    if (countEl) countEl.textContent = `${pending.length} file${pending.length !== 1 ? 's' : ''} ready`;
    if (sizeEl)  sizeEl.textContent  = fmt_size(pending.reduce((s, q) => s + q.file.size, 0)) + ' total';
  },

  _removeFile(i) {
    this.uploadQueue.splice(i, 1);
    this._renderQueue();
  },

  async _uploadAll() {
    const btn      = $('#upload-btn');
    const category = $('#upload-category')?.value.trim() || '';
    const tags     = $('#upload-tags')?.value.trim() || '';
    btn.disabled   = true;

    this._uploadCancelled = false;

    // Cancel button
    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn btn-secondary btn-block';
    cancelBtn.style.cssText = 'margin-top:.5rem;padding:.5rem;font-size:.85rem;border-radius:8px;background:#6b7280;color:#fff;border:none;cursor:pointer';
    cancelBtn.textContent = '✖ Cancel';
    cancelBtn.onclick = () => { this._uploadCancelled = true; cancelBtn.remove(); };
    btn.parentNode.insertBefore(cancelBtn, btn.nextSibling);

    const CONCURRENCY = 3;
    const TIMEOUT_MS  = 30000;
    let successCount  = 0;
    let doneCount     = 0;
    const pending     = this.uploadQueue.filter(q => q.status === 'pending');
    const total       = pending.length;

    const updateBtn = () => {
      btn.innerHTML = `<div class="spinner" style="margin:0 auto;width:16px;height:16px;display:inline-block;vertical-align:middle;margin-right:8px"></div>Uploading ${doneCount}/${total}…`;
    };
    updateBtn();

    const uploadOne = async (item) => {
      if (this._uploadCancelled) { item.status = 'pending'; return; }

      item.status   = 'uploading';
      item.progress = 15;
      this._renderQueue();

      const tryUpload = async () => {
        const form = new FormData();
        form.append('file', item.file);
        if (category) form.append('category', category);
        if (tags)     form.append('tags', tags);

        const controller = new AbortController();
        const tid = setTimeout(() => controller.abort(), TIMEOUT_MS);
        try {
          const res = await api.uploadWithSignal('/upload', form, controller.signal);
          clearTimeout(tid);
          return res;
        } catch (e) {
          clearTimeout(tid);
          return { success: false, error: e.name === 'AbortError' ? 'Timed out after 30s' : e.message };
        }
      };

      let res = await tryUpload();

      // 1 auto-retry on failure
      if (!res.success && !this._uploadCancelled) {
        item.errorMsg = `Retrying… (${res.error})`;
        this._renderQueue();
        await new Promise(r => setTimeout(r, 1500));
        res = await tryUpload();
      }

      item.progress = 100;
      if (res.success) {
        item.status   = res.is_duplicate ? 'duplicate' : 'done';
        item.result   = res;
        successCount++;
      } else {
        item.status   = 'error';
        item.errorMsg = res.error || 'Upload failed';
      }
      doneCount++;
      updateBtn();
      this._renderQueue();
    };

    // Concurrent worker pool
    let idx = 0;
    const runWorker = async () => {
      while (idx < pending.length && !this._uploadCancelled) {
        await uploadOne(pending[idx++]);
      }
    };
    await Promise.all(Array.from({ length: Math.min(CONCURRENCY, pending.length) }, runWorker));

    cancelBtn.remove();
    btn.disabled  = false;
    btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:18px;height:18px"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg> Upload &amp; Classify All`;

    const errCount = pending.filter(q => q.status === 'error').length;
    if (successCount > 0) {
      showAlert(`${successCount} document${successCount !== 1 ? 's' : ''} uploaded and classified!${errCount ? ` (${errCount} failed — shown in red below)` : ''}`, 'success');
    } else if (errCount > 0) {
      showAlert(`All ${errCount} uploads failed. Check your connection and try again.`, 'error');
    }
  },

  // ─────────────────────────────────────────────
  // Documents View
  // ─────────────────────────────────────────────
  async renderDocuments(c, page = 1) {
    this.docsPage   = page;
    this.docsFilter = this.docsFilter || { search: '', type: '', sort: 'uploaded_at', dir: 'desc' };
    this.docsSelected = new Set();
    c.innerHTML = `<div class="spinner" style="margin:3rem auto"></div>`;

    // build query params
    const f = this.docsFilter;
    const params = { page, per_page: 20, sort: f.sort, dir: f.dir };
    if (f.search) params.search = f.search;
    if (f.type)   params.doc_type = f.type;

    const res = await api.getDocuments(params);
    if (!res.success) {
      c.innerHTML = `<div class="alert alert-error">${esc(res.error)}</div>`; return;
    }

    const { documents, pagination } = res;

    // collect distinct types for the filter dropdown
    const allTypes = [...new Set(documents.map(d => d.predicted_label).filter(Boolean))].sort();

    const sortIcon = (col) => {
      if (f.sort !== col) return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sort-icon"><path d="M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4"/></svg>`;
      return f.dir === 'asc'
        ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sort-icon active"><path d="M5 15l7-7 7 7"/></svg>`
        : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sort-icon active"><path d="M19 9l-7 7-7-7"/></svg>`;
    };

    const rows = documents.map(d => `
      <tr class="doc-row" data-id="${d.id}">
        <td class="td-check">
          <input type="checkbox" class="doc-check" data-id="${d.id}">
        </td>
        <td>
          <div class="doc-name-cell">
            <div class="doc-type-dot ${_docExt(d.original_filename)}"></div>
            <span class="filename" title="${esc(d.original_filename)}">${esc(d.original_filename)}</span>
          </div>
        </td>
        <td><span class="category-badge">${esc(d.predicted_label || 'Unknown')}</span></td>
        <td><span class="${conf_class(d.confidence_score)}">${Math.round((d.confidence_score||0)*100)}%</span></td>
        <td class="text-muted">${fmt_date(d.uploaded_at)}</td>
        <td class="text-muted">${fmt_size(d.file_size)}</td>
        <td>
          <div class="action-btns">
            <button class="action-btn open"  onclick="openFile(${d.id},'${esc(d.original_filename)}')" title="Open">${ICONS.open}</button>
            <button class="action-btn edit"  onclick="app.openEditModal(${d.id},'${esc(d.predicted_label||'')}','${esc(d.tags||'')}')" title="Edit">${ICONS.edit}</button>
            <button class="action-btn del"   onclick="app.deleteDoc(${d.id},this)" title="Delete">${ICONS.trash}</button>
          </div>
        </td>
      </tr>`).join('');

    const emptyState = !documents.length ? `
      <div class="empty-state">
        ${ICONS.file}
        <h3>No documents found</h3>
        <p>${f.search || f.type ? 'Try adjusting your filters.' : 'Upload your first document to get started.'}</p>
        ${!f.search && !f.type ? `<button class="btn btn-primary mt-2" onclick="app.navigate('upload')">Upload Now</button>` : ''}
      </div>` : '';

    const pages = Array.from({length: pagination.pages}, (_, i) => i+1).map(p =>
      `<button class="page-btn ${p===page?'active':''}" onclick="app._docsGo(${p})">${p}</button>`
    ).join('');

    c.innerHTML = `
      <div id="alert-container"></div>

      <!-- Filter / sort bar -->
      <div class="docs-toolbar">
        <div class="docs-search-wrap">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="docs-search-icon">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input id="docs-search" class="docs-search-input" placeholder="Search by filename…"
            value="${esc(f.search)}" oninput="app._docsSearch(this.value)">
        </div>
        <select id="docs-type-filter" class="docs-filter-select" onchange="app._docsTypeFilter(this.value)">
          <option value="">All types</option>
          ${allTypes.map(t => `<option value="${esc(t)}" ${f.type===t?'selected':''}>${esc(t)}</option>`).join('')}
        </select>
        <button class="btn btn-sm btn-secondary" onclick="app._docsClearFilters()" title="Clear filters"
          style="${f.search||f.type?'':'visibility:hidden'}">✕ Clear</button>
        <span class="docs-total">${pagination.total} document${pagination.total!==1?'s':''}</span>
        <button class="btn btn-sm btn-primary" onclick="app.navigate('upload')" style="margin-left:auto">
          ${ICONS.upload} Upload
        </button>
      </div>

      <!-- Bulk-action bar (hidden until selection) -->
      <div class="bulk-toolbar" id="bulk-toolbar" style="display:none">
        <label class="bulk-count" id="bulk-count">0 selected</label>
        <button class="btn btn-sm btn-danger" id="bulk-delete-btn" onclick="app._bulkDelete()">
          ${ICONS.trash} Delete selected
        </button>
        <button class="btn btn-sm btn-secondary" onclick="app._clearSelection()">Deselect all</button>
      </div>

      <div class="card" style="margin-top:.5rem">
        ${emptyState || `
        <div class="table-wrap">
          <table>
            <thead><tr>
              <th class="td-check">
                <input type="checkbox" id="check-all" title="Select all">
              </th>
              <th class="sortable" onclick="app._docsSort('original_filename')">
                Filename ${sortIcon('original_filename')}
              </th>
              <th class="sortable" onclick="app._docsSort('predicted_label')">
                Category ${sortIcon('predicted_label')}
              </th>
              <th class="sortable" onclick="app._docsSort('confidence_score')">
                Confidence ${sortIcon('confidence_score')}
              </th>
              <th class="sortable" onclick="app._docsSort('uploaded_at')">
                Uploaded ${sortIcon('uploaded_at')}
              </th>
              <th class="sortable" onclick="app._docsSort('file_size')">
                Size ${sortIcon('file_size')}
              </th>
              <th>Actions</th>
            </tr></thead>
            <tbody id="docs-tbody">${rows}</tbody>
          </table>
        </div>
        ${pagination.pages > 1 ? `<div class="pagination" style="padding:1rem">${pages}</div>` : ''}`}
      </div>`;

    // wire up checkboxes
    this._bindDocsSelection();
  },

  _bindDocsSelection() {
    const all = $('#check-all');
    if (!all) return;

    all.addEventListener('change', () => {
      $$('.doc-check').forEach(cb => { cb.checked = all.checked; });
      this._syncSelection();
    });
    $$('.doc-check').forEach(cb => {
      cb.addEventListener('change', () => this._syncSelection());
    });
  },

  _syncSelection() {
    this.docsSelected = new Set(
      [...$$('.doc-check')].filter(cb => cb.checked).map(cb => +cb.dataset.id)
    );
    const n = this.docsSelected.size;
    const bar = $('#bulk-toolbar');
    if (bar) bar.style.display = n ? '' : 'none';
    const cnt = $('#bulk-count');
    if (cnt) cnt.textContent = `${n} selected`;
    const all = $('#check-all');
    if (all) {
      const total = $$('.doc-check').length;
      all.indeterminate = n > 0 && n < total;
      all.checked = n === total && total > 0;
    }
  },

  _clearSelection() {
    $$('.doc-check').forEach(cb => cb.checked = false);
    const all = $('#check-all');
    if (all) { all.checked = false; all.indeterminate = false; }
    this._syncSelection();
  },

  async _bulkDelete() {
    const ids = [...this.docsSelected];
    if (!ids.length) return;
    if (!confirm(`Delete ${ids.length} document${ids.length!==1?'s':''}? This cannot be undone.`)) return;

    const btn = $('#bulk-delete-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Deleting…'; }

    const res = await api.bulkDeleteDocuments(ids);
    if (res.success) {
      showAlert(`${res.deleted} document${res.deleted!==1?'s':''} deleted.`, 'success');
      this.renderDocuments($('#content'), this.docsPage);
    } else {
      if (btn) { btn.disabled = false; btn.innerHTML = `${ICONS.trash} Delete selected`; }
      showAlert(res.error || 'Bulk delete failed', 'error');
    }
  },

  _docsGo(page) { this.renderDocuments($('#content'), page); },

  _docsSearch: _debounce(function(val) {
    this.docsFilter.search = val.trim();
    this.docsPage = 1;
    this.renderDocuments($('#content'), 1);
  }, 350),

  _docsTypeFilter(val) {
    this.docsFilter.type = val;
    this.docsPage = 1;
    this.renderDocuments($('#content'), 1);
  },

  _docsClearFilters() {
    this.docsFilter.search = '';
    this.docsFilter.type   = '';
    this.docsPage = 1;
    this.renderDocuments($('#content'), 1);
  },

  _docsSort(col) {
    if (this.docsFilter.sort === col) {
      this.docsFilter.dir = this.docsFilter.dir === 'asc' ? 'desc' : 'asc';
    } else {
      this.docsFilter.sort = col;
      this.docsFilter.dir  = 'desc';
    }
    this.renderDocuments($('#content'), this.docsPage);
  },

  async deleteDoc(id, btn) {
    if (!confirm('Delete this document?')) return;
    btn.disabled = true;
    const res = await api.deleteDocument(id);
    if (res.success) {
      showAlert('Document deleted.', 'success', $('#alert-container'));
      this.renderDocuments($('#content'), this.docsPage);
    } else {
      btn.disabled = false;
      showAlert(res.error || 'Delete failed', 'error', $('#alert-container'));
    }
  },

  openEditModal(id, category, tags) {
    const overlay = showModal(`
      <div class="modal">
        <div class="modal-header">
          <h3>Edit Document</h3>
          <span class="modal-close" onclick="this.closest('.modal-overlay').remove()">✕</span>
        </div>
        <div id="modal-alert"></div>
        <div class="form-group">
          <label>Category / Folder</label>
          <input type="text" id="m-category" value="${esc(category)}">
        </div>
        <div class="form-group">
          <label>Tags</label>
          <input type="text" id="m-tags" value="${esc(tags)}" placeholder="comma-separated">
        </div>
        <div class="flex gap-2" style="justify-content:flex-end">
          <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
          <button class="btn btn-primary" id="m-save-btn">Save</button>
        </div>
      </div>`);

    $('#m-save-btn', overlay).addEventListener('click', async () => {
      const btn = $('#m-save-btn', overlay);
      btn.disabled = true; btn.textContent = 'Saving…';
      const res = await api.updateDocument(id, {
        category: $('#m-category', overlay).value.trim(),
        tags:     $('#m-tags', overlay).value.trim(),
      });
      if (res.success) {
        overlay.remove();
        this.renderDocuments($('#content'), this.docsPage);
      } else {
        btn.disabled = false; btn.textContent = 'Save';
        showAlert(res.error || 'Update failed', 'error', $('#modal-alert', overlay));
      }
    });
  },

  // ─────────────────────────────────────────────
  // Search View
  // ─────────────────────────────────────────────
  renderSearch(c) {
    c.innerHTML = `
      <div id="alert-container"></div>

      <!-- Hero search bar -->
      <div class="search-hero">
        <div class="search-hero-bar">
          <span class="search-hero-icon">${ICONS.search}</span>
          <input type="text" id="search-input" placeholder="Search filenames, content, tags…" autocomplete="off">
          <button class="btn btn-primary" id="search-btn" style="border-radius:8px;padding:.5rem 1.2rem">Search</button>
        </div>
        <!-- Filters row -->
        <div class="search-filters">
          <div class="search-filter-group">
            <label>Category</label>
            <input type="text" id="f-category" placeholder="e.g. Invoice">
          </div>
          <div class="search-filter-group">
            <label>From date</label>
            <input type="date" id="f-date-from">
          </div>
          <div class="search-filter-group">
            <label>To date</label>
            <input type="date" id="f-date-to">
          </div>
          <button class="btn btn-secondary" id="clear-btn" style="align-self:flex-end">Clear</button>
        </div>
      </div>

      <div id="search-results"></div>`;

    const doSearch = () => {
      const q         = $('#search-input').value.trim();
      const category  = $('#f-category').value.trim();
      const date_from = $('#f-date-from').value;
      const date_to   = $('#f-date-to').value;
      if (!q && !category && !date_from && !date_to) {
        showAlert('Enter a search term or filter.', 'warning', $('#alert-container')); return;
      }
      this._execSearch({ q, category, date_from, date_to }, 1);
    };

    $('#search-btn').addEventListener('click', doSearch);
    $('#search-input').addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });
    $('#clear-btn').addEventListener('click', () => {
      $$('#search-input,#f-category,#f-date-from,#f-date-to').forEach(el => el.value = '');
      $('#search-results').innerHTML = '';
    });
  },

  async _execSearch(params, page) {
    const container = $('#search-results');
    container.innerHTML = `<div class="spinner" style="margin:2.5rem auto"></div>`;

    const res = await api.search({ ...params, page, per_page: 20 });
    if (!res.success) {
      container.innerHTML = `<div class="alert alert-error">${esc(res.error)}</div>`; return;
    }

    const { results, pagination, interpreted_as } = res;

    // Show what the query was interpreted as (NL time parsing hint)
    let interpretedHint = '';
    if (interpreted_as) {
      const parts = [];
      if (interpreted_as.keywords) parts.push(`keywords: "<strong>${esc(interpreted_as.keywords)}</strong>"`);
      if (interpreted_as.date_from) {
        const d = new Date(interpreted_as.date_from);
        parts.push(`from: <strong>${d.toLocaleString()}</strong>`);
      }
      if (interpreted_as.date_to) {
        const d = new Date(interpreted_as.date_to);
        parts.push(`to: <strong>${d.toLocaleString()}</strong>`);
      }
      if (parts.length) interpretedHint = `<div class="search-interpreted">🔍 Interpreted as: ${parts.join(' · ')}</div>`;
    }

    if (!results.length) {
      container.innerHTML = interpretedHint + `
        <div class="empty-state">
          ${ICONS.search}
          <h3>No results found</h3>
          <p>Try different keywords or remove filters.</p>
        </div>`;
      return;
    }

    const cards = results.map(d => {
      const ext = _docExt(d.original_filename);
      const extLabel = {'pdf':'PDF','docx':'DOC','txt':'TXT','img':'IMG','other':'FILE'}[ext] || 'FILE';
      return `
        <div class="search-result-card">
          <div class="src-icon ${ext}">${extLabel}</div>
          <div class="src-body">
            <div class="src-name" title="${esc(d.original_filename)}">${esc(d.original_filename)}</div>
            <div class="src-meta">
              <span class="category-badge" style="font-size:.7rem">${esc(d.predicted_label||'Unknown')}</span>
              <span class="${conf_class(d.confidence_score)}" style="font-size:.75rem">${Math.round((d.confidence_score||0)*100)}% confidence</span>
              <span class="text-muted" style="font-size:.75rem">${fmt_date(d.uploaded_at)}</span>
              <span class="text-muted" style="font-size:.75rem">${fmt_size(d.file_size)}</span>
            </div>
          </div>
          <div class="action-btns">
            <button class="action-btn open" onclick="openFile(${d.id},'${esc(d.original_filename)}')" title="Open">${ICONS.open}</button>
          </div>
        </div>`;
    }).join('');

    container.innerHTML = interpretedHint + `
      <div class="search-results-header">
        <span>${pagination.total} result${pagination.total !== 1 ? 's' : ''}</span>
        ${pagination.pages > 1 ? `<span class="text-muted" style="font-size:.8rem">Page ${page} of ${pagination.pages}</span>` : ''}
      </div>
      <div class="search-results-list">${cards}</div>`;
  },

  // ─────────────────────────────────────────────
  // Folders View
  // ─────────────────────────────────────────────
  async renderFolders(c) {
    c.innerHTML = `<div class="spinner" style="margin:3rem auto"></div>`;
    const res = await api.getFolderStats();
    if (!res.success) {
      c.innerHTML = `<div class="alert alert-error">${esc(res.error)}</div>`; return;
    }

    const folders = res.folders || [];

    // Assign a colour per folder deterministically
    const FOLDER_COLORS = [
      '#6366F1','#8B5CF6','#EC4899','#10B981','#F59E0B',
      '#3B82F6','#EF4444','#14B8A6','#F97316','#84CC16',
    ];
    const folderCards = folders.map((f, i) => {
      const color = FOLDER_COLORS[i % FOLDER_COLORS.length];
      return `
        <div class="folder-card" style="--fc:${color}">
          <div class="folder-card-icon" onclick="app._filterByFolder('${esc(f)}')" style="cursor:pointer">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
            </svg>
          </div>
          <div class="folder-card-name" onclick="app._filterByFolder('${esc(f)}')" style="cursor:pointer">${esc(f)}</div>
          <div class="folder-card-actions">
            <button class="folder-card-open" onclick="app._filterByFolder('${esc(f)}')">Open →</button>
          </div>
        </div>`;
    }).join('');

    c.innerHTML = `
      <!-- Stats strip -->
      <div class="folder-stats-strip">
        <div class="fstat">
          <div class="fstat-val">${res.total_documents}</div>
          <div class="fstat-lbl">Total Documents</div>
        </div>
        <div class="fstat">
          <div class="fstat-val">${res.folder_count}</div>
          <div class="fstat-lbl">Folders</div>
        </div>
        <div class="fstat">
          <div class="fstat-val">${res.total_corrections}</div>
          <div class="fstat-lbl">AI Corrections</div>
        </div>
      </div>

      <!-- Folder grid -->
      <div class="folders-section-header">
        <h3>${ICONS.folder} All Folders</h3>
        <button class="btn btn-primary btn-sm" onclick="app.navigate('upload')">${ICONS.upload} Upload</button>
      </div>

      ${folders.length
        ? `<div class="folder-grid">${folderCards}</div>`
        : `<div class="empty-state">${ICONS.folder}<h3>No folders yet</h3><p>Upload documents and AI will create folders automatically.</p><button class="btn btn-primary" onclick="app.navigate('upload')">${ICONS.upload} Upload Now</button></div>`
      }

      <!-- Correct AI card -->
      <div class="card" style="margin-top:1.5rem">
        <div class="card-header">
          <h3>✏️ Correct AI Prediction</h3>
        </div>
        <div class="card-body">
          <p class="text-muted" style="font-size:.84rem;margin-bottom:1rem">
            Improve accuracy by correcting a wrong classification. Used during retraining.
          </p>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:.75rem">
            <div class="form-group" style="margin:0">
              <label>Document ID</label>
              <input type="number" id="fb-doc-id" placeholder="e.g. 42">
            </div>
            <div class="form-group" style="margin:0">
              <label>Correct Label</label>
              <input type="text" id="fb-label" placeholder="e.g. Invoice">
            </div>
            <div class="form-group" style="margin:0">
              <label>Note (optional)</label>
              <input type="text" id="fb-note" placeholder="Why is this right?">
            </div>
          </div>
          <div id="fb-alert" style="margin-top:.75rem"></div>
          <button class="btn btn-primary" id="fb-submit" style="margin-top:.75rem">Submit Correction</button>
        </div>
      </div>`;

    $('#fb-submit').addEventListener('click', async () => {
      const docId = parseInt($('#fb-doc-id').value);
      const label = $('#fb-label').value.trim();
      if (!docId || !label) {
        showAlert('Document ID and label are required.', 'warning', $('#fb-alert')); return;
      }
      const res = await api.submitFeedback(docId, label, $('#fb-note').value.trim());
      if (res.success) showAlert('Correction saved! Thank you.', 'success', $('#fb-alert'));
      else showAlert(res.error || 'Failed', 'error', $('#fb-alert'));
    });
  },

  _filterByFolder(folder) {
    this.navigate('documents');
    setTimeout(async () => {
      const c = $('#content');
      c.innerHTML = `<div class="spinner" style="margin:3rem auto"></div>`;
      const res = await api.getDocuments({ category: folder, per_page: 50 });
      if (!res.success) { c.innerHTML = `<div class="alert alert-error">${esc(res.error)}</div>`; return; }
      const { documents } = res;
      const rows = documents.map(d => `
        <tr>
          <td>
            <div class="doc-name-cell">
              <div class="doc-type-dot ${_docExt(d.original_filename)}"></div>
              <span class="filename">${esc(d.original_filename)}</span>
            </div>
          </td>
          <td><span class="${conf_class(d.confidence_score)}">${Math.round((d.confidence_score||0)*100)}%</span></td>
          <td class="text-muted">${fmt_date(d.uploaded_at)}</td>
          <td class="text-muted">${fmt_size(d.file_size)}</td>
          <td>
            <div class="action-btns">
              <button class="action-btn open" onclick="openFile(${d.id},'${esc(d.original_filename)}')" title="Open">${ICONS.open}</button>
            </div>
          </td>
        </tr>`).join('');
      c.innerHTML = `
        <div class="folder-view-header">
          <button class="btn btn-secondary btn-sm" onclick="app.navigate('folders')">← Back to Folders</button>
          <h3>📁 ${esc(folder)} <span class="text-muted" style="font-weight:400;font-size:.85rem">(${documents.length} file${documents.length !== 1 ? 's' : ''})</span></h3>
        </div>
        <div class="card" style="margin-top:1rem">
          ${documents.length ? `
          <div class="table-wrap">
            <table>
              <thead><tr><th>Filename</th><th>Confidence</th><th>Uploaded</th><th>Size</th><th></th></tr></thead>
              <tbody>${rows}</tbody>
            </table>
          </div>` : `<div class="empty-state" style="padding:2rem">${ICONS.file}<h3>Empty folder</h3></div>`}
        </div>`;
    }, 50);
  },

  // ─────────────────────────────────────────────
  // Smart Views — VFS multi-dimensional browser
  // ─────────────────────────────────────────────
  async renderViews(c) {
    c.innerHTML = `<div class="spinner" style="margin:3rem auto"></div>`;
    const viewsRes = await api.getViews();
    if (!viewsRes.success) {
      c.innerHTML = `<div class="alert alert-error">${esc(viewsRes.error)}</div>`; return;
    }

    const views = viewsRes.views;
    const activeView = this.vfsState.viewName || views[0]?.view_name || 'by_type';
    const builtIn = new Set(['by_type', 'by_client', 'by_time']);

    const tabs = views.map(v => {
      const delBtn = !builtIn.has(v.view_name)
        ? `<span class="vfs-tab-del" data-del-view="${esc(v.view_name)}" title="Delete view">×</span>`
        : '';
      return `<button class="vfs-tab ${v.view_name === activeView ? 'active' : ''}" data-view="${esc(v.view_name)}">${esc(v.display_name)}${delBtn}</button>`;
    }).join('');

    const noDocsHint = `
      <div class="empty-state" style="padding:3rem 1rem">
        ${ICONS.folder}
        <h3>Select a folder</h3>
        <p>Click any folder in the tree to browse its documents.</p>
      </div>`;

    // New View modal (hidden by default)
    const newViewModal = `
      <div id="new-view-modal" class="modal-overlay" style="display:none">
        <div class="modal-box" style="max-width:400px">
          <h3 style="margin-top:0">Add New View</h3>
          <div id="new-view-error" class="alert alert-error" style="display:none"></div>
          <label class="form-label">View Name (snake_case)</label>
          <input id="nv-name" class="form-input" placeholder="e.g. by_vendor" />
          <label class="form-label" style="margin-top:.75rem">Display Label</label>
          <input id="nv-display" class="form-input" placeholder="e.g. By Vendor" />
          <label class="form-label" style="margin-top:.75rem">Level 1 Attribute</label>
          <select id="nv-l1" class="form-input">
            <option value="doc_type">doc_type</option>
            <option value="client_name">client_name</option>
            <option value="doc_year">doc_year</option>
          </select>
          <label class="form-label" style="margin-top:.75rem">Level 2 Attribute</label>
          <select id="nv-l2" class="form-input">
            <option value="client_name">client_name</option>
            <option value="doc_type">doc_type</option>
            <option value="doc_year">doc_year</option>
          </select>
          <label class="form-label" style="margin-top:.75rem">Level 3 Attribute</label>
          <select id="nv-l3" class="form-input">
            <option value="doc_year">doc_year</option>
            <option value="doc_type">doc_type</option>
            <option value="client_name">client_name</option>
          </select>
          <div style="display:flex;gap:.5rem;justify-content:flex-end;margin-top:1.25rem">
            <button class="btn btn-secondary" id="nv-cancel">Cancel</button>
            <button class="btn btn-primary" id="nv-submit">Create View</button>
          </div>
        </div>
      </div>`;

    c.innerHTML = `
      ${newViewModal}
      <div id="alert-container"></div>
      <div class="vfs-tabs-bar">
        <div class="vfs-tabs">${tabs}</div>
        <button class="btn btn-sm btn-secondary" id="btn-new-view" title="Add a new view">+ New View</button>
      </div>
      <div class="vfs-layout">
        <div class="vfs-tree-panel" id="vfs-tree-panel">
          <div class="spinner" style="margin:2rem auto"></div>
        </div>
        <div class="vfs-docs-panel" id="vfs-docs-panel">${noDocsHint}</div>
      </div>`;

    // Tab click → switch view
    $$('.vfs-tab').forEach(tab => {
      tab.addEventListener('click', e => {
        if (e.target.classList.contains('vfs-tab-del')) return; // handled below
        this.vfsState.viewName = tab.dataset.view;
        this.vfsState.expanded = new Set();
        this.vfsState.browsePath = null;
        $$('.vfs-tab').forEach(t => t.classList.toggle('active', t.dataset.view === tab.dataset.view));
        $('#vfs-docs-panel').innerHTML = noDocsHint;
        this._loadVfsTree(tab.dataset.view);
      });
    });

    // Tab delete button
    $$('.vfs-tab-del').forEach(btn => {
      btn.addEventListener('click', async e => {
        e.stopPropagation();
        const viewName = btn.dataset.delView;
        if (!confirm(`Delete view "${viewName}"? This removes all virtual paths for this view.`)) return;
        const res = await api.deleteViewTemplate(viewName);
        if (res.success) {
          if (this.vfsState.viewName === viewName) this.vfsState.viewName = 'by_type';
          this.renderViews(c);
        } else {
          alert(`Delete failed: ${res.error}`);
        }
      });
    });

    // New View modal
    $('#btn-new-view').addEventListener('click', () => {
      $('#new-view-modal').style.display = 'flex';
    });
    $('#nv-cancel').addEventListener('click', () => {
      $('#new-view-modal').style.display = 'none';
    });
    $('#nv-submit').addEventListener('click', async () => {
      const name    = $('#nv-name').value.trim();
      const display = $('#nv-display').value.trim();
      const l1      = $('#nv-l1').value;
      const l2      = $('#nv-l2').value;
      const l3      = $('#nv-l3').value;
      const errBox  = $('#new-view-error');
      errBox.style.display = 'none';

      if (!name || !display) {
        errBox.textContent = 'View name and display label are required.';
        errBox.style.display = '';
        return;
      }
      if (!/^[a-z][a-z0-9_]*$/.test(name)) {
        errBox.textContent = 'View name must be snake_case (lowercase letters, digits, underscores).';
        errBox.style.display = '';
        return;
      }

      const btn = $('#nv-submit');
      btn.disabled = true;
      btn.textContent = 'Creating…';

      const res = await api.postViewTemplate(name, display, l1, l2, l3);
      btn.disabled = false;
      btn.textContent = 'Create View';

      if (res.success) {
        $('#new-view-modal').style.display = 'none';
        this.vfsState.viewName = name;
        this.renderViews(c);
      } else {
        errBox.textContent = res.error || 'Failed to create view.';
        errBox.style.display = '';
      }
    });

    this._loadVfsTree(activeView);
  },

  async _loadVfsTree(viewName) {
    const panel = $('#vfs-tree-panel');
    if (!panel) return;
    panel.innerHTML = `<div class="spinner" style="margin:2rem auto"></div>`;

    const res = await api.getViewTree(viewName);
    if (!res.success) {
      panel.innerHTML = `<div class="alert alert-error">${esc(res.error)}</div>`; return;
    }

    if (!res.tree?.length) {
      panel.innerHTML = `<div class="empty-state" style="padding:2rem">${ICONS.folder}<h3>No documents</h3><p>Upload some documents first.</p></div>`;
      return;
    }

    panel.innerHTML = `
      <div class="vfs-tree-header">
        <span class="vfs-tree-title">${esc(res.display_name)}</span>
        <span class="vfs-tree-meta">${esc(res.level1_attr)} › ${esc(res.level2_attr)} › ${esc(res.level3_attr)}</span>
      </div>
      <div class="vfs-tree" id="vfs-tree">
        ${this._renderTreeNodes(res.tree, viewName, 0)}
      </div>`;

    this._bindTreeEvents(panel, viewName);
  },

  _renderTreeNodes(nodes, viewName, depth) {
    return nodes.map(node => {
      const hasChildren = node.children?.length > 0;
      const nodeKey = `${viewName}::${node.path}`;
      const isExpanded = this.vfsState.expanded.has(nodeKey);
      const isSelected = this.vfsState.browsePath === node.path;

      const childrenHtml = hasChildren
        ? `<div class="vfs-tree-children" style="${isExpanded ? '' : 'display:none'}">${this._renderTreeNodes(node.children, viewName, depth + 1)}</div>`
        : '';

      return `
        <div class="vfs-tree-node">
          <div class="vfs-tree-row${isSelected ? ' selected' : ''}"
              data-path="${esc(node.path)}" data-view="${esc(viewName)}"
              data-has-children="${hasChildren}">
            <span class="vfs-indent" style="width:${depth * 16}px"></span>
            <span class="vfs-chevron ${hasChildren ? '' : 'invisible'}${isExpanded ? ' open' : ''}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
            </span>
            <span class="vfs-node-icon">${hasChildren ? ICONS.folder : ICONS.file}</span>
            <span class="vfs-node-label" title="${esc(node.label)}">${esc(node.label)}</span>
            <span class="vfs-node-count">${node.count}</span>
          </div>
          ${childrenHtml}
        </div>`;
    }).join('');
  },

  _bindTreeEvents(panel, viewName) {
    panel.querySelectorAll('.vfs-tree-row').forEach(row => {
      row.addEventListener('click', () => {
        const path = row.dataset.path;
        const hasChildren = row.dataset.hasChildren === 'true';
        const nodeKey = `${viewName}::${path}`;

        // Mark selection
        panel.querySelectorAll('.vfs-tree-row').forEach(r => r.classList.remove('selected'));
        row.classList.add('selected');
        this.vfsState.browsePath = path;

        // Toggle expand / collapse
        if (hasChildren) {
          const nodeEl = row.parentElement;
          const childrenDiv = row.nextElementSibling;
          const chevron = row.querySelector('.vfs-chevron');
          if (this.vfsState.expanded.has(nodeKey)) {
            this.vfsState.expanded.delete(nodeKey);
            if (childrenDiv) childrenDiv.style.display = 'none';
            if (chevron) chevron.classList.remove('open');
          } else {
            this.vfsState.expanded.add(nodeKey);
            if (childrenDiv) childrenDiv.style.display = '';
            if (chevron) chevron.classList.add('open');
          }
        }

        // Browse docs at this path
        this._vfsBrowse(viewName, path);
      });
    });
  },

  async _vfsBrowse(viewName, path) {
    const panel = $('#vfs-docs-panel');
    if (!panel) return;
    panel.innerHTML = `<div class="spinner" style="margin:2rem auto"></div>`;

    const res = await api.browseView(viewName, path, 1, 50);
    if (!res.success) {
      panel.innerHTML = `<div class="alert alert-error">${esc(res.error)}</div>`; return;
    }

    const docs = res.documents || [];
    const breadcrumb = path.split('/').map(seg =>
      `<span class="vfs-crumb">${esc(seg)}</span>`
    ).join('<span class="vfs-crumb-sep">/</span>');

    if (!docs.length) {
      panel.innerHTML = `
        <div class="vfs-docs-header">
          <div class="vfs-breadcrumb">${breadcrumb}</div>
          <span class="text-muted" style="font-size:.8rem">0 documents</span>
        </div>
        <div class="empty-state" style="padding:2rem">${ICONS.file}<h3>No documents here</h3></div>`;
      return;
    }

    const rows = docs.map(d => `
      <tr>
        <td>
          <div class="doc-name-cell">
            <div class="doc-type-dot ${_docExt(d.original_filename)}"></div>
            <span class="filename" title="${esc(d.original_filename)}">${esc(d.original_filename)}</span>
          </div>
        </td>
        <td><span class="category-badge">${esc(d.doc_type || 'Unknown')}</span></td>
        <td class="text-muted">${d.client_name ? esc(d.client_name) : '—'}</td>
        <td class="text-muted">${d.doc_year || '—'}</td>
        <td class="text-muted">${fmt_date(d.uploaded_at)}</td>
        <td class="text-muted">${fmt_size(d.file_size)}</td>
        <td>
          <div class="action-btns">
            <button class="action-btn open" onclick="openFile(${d.id},'${esc(d.original_filename)}')" title="Open">${ICONS.open}</button>
          </div>
        </td>
      </tr>`).join('');

    panel.innerHTML = `
      <div class="vfs-docs-header">
        <div class="vfs-breadcrumb">${breadcrumb}</div>
        <span class="text-muted" style="font-size:.8rem">${res.total} document${res.total !== 1 ? 's' : ''}</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th>Filename</th><th>Type</th><th>Client</th>
            <th>Year</th><th>Uploaded</th><th>Size</th><th></th>
          </tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      ${res.total > 50 ? `<div style="padding:.75rem 1rem;font-size:.8rem;color:var(--text-muted)">Showing first 50 of ${res.total}</div>` : ''}`;
  },

  // ─────────────────────────────────────────────
  // File Indexer View  (Phase A)
  // ─────────────────────────────────────────────
  async renderIndexer(c) {
    c.innerHTML = `<div class="spinner" style="margin:3rem auto"></div>`;
    const [foldersRes, statsRes] = await Promise.all([api.indexerFolders(), api.indexerStats()]);
    const folders = foldersRes.folders || [];
    const stats   = statsRes || {};

    c.innerHTML = `
      <div id="alert-container"></div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem;margin-bottom:1.5rem">
        <div class="stat-card"><div class="stat-value">${(stats.total_files||0).toLocaleString()}</div><div class="stat-label">Files Indexed</div></div>
        <div class="stat-card"><div class="stat-value">${stats.watched_folders||0}</div><div class="stat-label">Watched Folders</div></div>
        <div class="stat-card"><div class="stat-value">${Object.keys(stats.by_extension||{}).length}</div><div class="stat-label">File Types</div></div>
      </div>

      <div class="card" style="margin-bottom:1.25rem">
        <div class="card-header" style="font-weight:600">Add Folder to Watch</div>
        <div class="card-body" style="display:flex;gap:.75rem;align-items:flex-end;flex-wrap:wrap">
          <div style="flex:1;min-width:250px">
            <label style="font-size:.8rem;color:var(--text-muted);margin-bottom:.3rem;display:block">Folder path on this PC</label>
            <input type="text" id="idx-folder-input" placeholder="e.g. C:\\Users\\you\\Documents"
              style="width:100%;padding:.55rem .75rem;border:1px solid var(--border);border-radius:8px;font-size:.9rem;background:var(--surface);color:var(--text)">
          </div>
          <label style="display:flex;align-items:center;gap:.4rem;font-size:.85rem;cursor:pointer;padding-bottom:.1rem">
            <input type="checkbox" id="idx-recursive" checked> Include sub-folders
          </label>
          <button class="btn btn-primary" id="idx-add-btn" style="padding:.55rem 1.1rem">Add Folder</button>
        </div>
      </div>

      <div class="card" style="margin-bottom:1.25rem;border:2px dashed var(--primary-light,#6c8ebf)">
        <div class="card-body" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.75rem">
          <div>
            <div style="font-weight:600;font-size:.95rem">&#128187; Scan Entire PC</div>
            <div style="font-size:.82rem;color:var(--text-muted);margin-top:.2rem">
              Auto-detects all drives (C:, D:, …) and indexes every document, PDF, image and spreadsheet found.
              System folders (Windows, Program Files, AppData…) are automatically skipped.
              This may take several minutes depending on the number of files.
            </div>
          </div>
          <button class="btn btn-primary" id="idx-scan-pc-btn" style="padding:.6rem 1.3rem;white-space:nowrap">&#128269; Scan Entire PC</button>
        </div>
      </div>

      <div class="card" style="margin-bottom:1.25rem">
        <div class="card-header" style="font-weight:600">Watched Folders</div>
        <div id="idx-folders-list">
          ${folders.length === 0
            ? `<div class="empty-state" style="padding:2rem"><p>No folders added yet.</p></div>`
            : folders.map(f => `
              <div class="idx-folder-row" id="idr-${f.id}">
                <div class="idx-folder-icon">📁</div>
                <div class="idx-folder-info">
                  <div class="idx-folder-path">${esc(f.folder_path)}</div>
                  <div class="idx-folder-meta">
                    ${f.file_count} files
                    ${f.last_scan_at ? ' · last scanned ' + fmt_date(f.last_scan_at) : ' · not scanned yet'}
                  </div>
                </div>
                <div class="idx-folder-actions">
                  <button class="btn btn-secondary btn-sm" onclick="app._indexerScan('${esc(f.folder_path)}', ${f.id})">▶ Scan</button>
                  <button class="btn btn-danger btn-sm" onclick="app._indexerRemoveFolder(${f.id})">Remove</button>
                </div>
              </div>`).join('')
          }
        </div>
      </div>

      <div id="idx-scan-status" style="display:none" class="card">
        <div class="card-body">
          <div style="display:flex;align-items:center;gap:.75rem">
            <div class="spinner" style="width:18px;height:18px;flex-shrink:0"></div>
            <div>
              <div id="idx-scan-msg" style="font-weight:500">Scanning…</div>
              <div id="idx-scan-detail" style="font-size:.8rem;color:var(--text-muted);margin-top:.15rem"></div>
            </div>
          </div>
          <div class="progress-bar" style="margin-top:.75rem">
            <div class="progress-fill" id="idx-scan-bar" style="width:0%;transition:width .3s"></div>
          </div>
        </div>
      </div>`;

    // Add folder
    $('#idx-add-btn').addEventListener('click', async () => {
      const path = $('#idx-folder-input').value.trim();
      if (!path) { showAlert('Enter a folder path.', 'error'); return; }
      const recursive = $('#idx-recursive').checked;
      const res = await api.indexerAddFolder(path, recursive);
      if (res.success) {
        showAlert('Folder added! Click "Scan" to index it.', 'success');
        this.renderIndexer(c);
      } else {
        showAlert(res.error || 'Failed to add folder', 'error');
      }
    });

    // Scan entire PC
    $('#idx-scan-pc-btn').addEventListener('click', () => this._indexerScanPC());
  },

  async _indexerRemoveFolder(id) {
    if (!confirm('Remove this folder from watching? (files on disk are NOT deleted)')) return;
    const res = await api.indexerRemoveFolder(id);
    if (res.success) this.renderIndexer($('#content'));
    else showAlert(res.error || 'Failed', 'error');
  },

  _indexerScanPC() {
    if (!confirm(
      'Scan Entire PC?\n\n' +
      'This will index all documents, PDFs, images and spreadsheets found on every drive.\n' +
      'System folders (Windows, Program Files, AppData…) are skipped automatically.\n\n' +
      'This may take several minutes. You can continue using the app while it runs.'
    )) return;

    const status = $('#idx-scan-status');
    const msg    = $('#idx-scan-msg');
    const detail = $('#idx-scan-detail');
    const bar    = $('#idx-scan-bar');
    if (!status) return;
    status.style.display = '';
    msg.textContent = 'Starting full-PC scan…';
    detail.textContent = 'Discovering drives…';

    api.indexerScanPC().then(res => {
      if (!res.success) {
        showAlert(res.error || 'Scan failed to start', 'error');
        status.style.display = 'none';
        return;
      }
      showAlert(`${res.message || 'Scan started'}`, 'info');
      const taskId = res.task_id;
      let viewsRefreshed = false;
      const poll = setInterval(async () => {
        const p = await api.indexerScanProgress(taskId);
        const isCode = (p.current || '').match(/\.(py|js|jsx|ts|tsx|java|go|rs|cs|rb|php|c|cpp|h|hpp|swift|kt|vue|html|css|sql|sh|ps1|json|yaml|yml|toml|md)$/i);
        const icon = isCode ? '💻 ' : '📄 ';

        if (p.phase === 'discovery') {
          bar.style.width = '0%';
          msg.textContent = '🔍 Discovering files across all drives…';
          detail.textContent = p.current || '';
        } else if (p.phase === 'indexing' && p.total > 0) {
          const pct = Math.round(p.done / p.total * 100);
          bar.style.width = pct + '%';
          msg.textContent = `⚡ Indexing in parallel… ${(p.done||0).toLocaleString()} / ${(p.total||0).toLocaleString()} files (${pct}%)`;
          detail.textContent = p.current ? icon + p.current.split(/[\\/]/).pop() : '';
        } else if (p.phase === 'embedding') {
          if (!viewsRefreshed) {
            viewsRefreshed = true;
            showAlert('Files indexed and visible in views. Building AI search index in background…', 'info');
          }
          const et = p.embed_total || 0;
          const ed = p.embed_done  || 0;
          const pct = et > 0 ? Math.round(ed / et * 100) : 0;
          bar.style.width = pct + '%';
          msg.textContent = `🧠 Building AI search index… ${ed.toLocaleString()} / ${et.toLocaleString()} (${pct}%)`;
          detail.textContent = p.current || 'You can keep using the app.';
        }

        if (p.status === 'done') {
          clearInterval(poll);
          status.style.display = 'none';
          bar.style.width = '100%';
          const r = p.result || {};
          showAlert(
            `Scan complete — ${(r.indexed||0).toLocaleString()} indexed, ` +
            `${(r.unchanged||0).toLocaleString()} unchanged, ` +
            `${(r.skipped||0).toLocaleString()} skipped, ${r.error||0} errors. ` +
            `AI search index ready.`,
            'success'
          );
          this.renderIndexer($('#content'));
        }
      }, 1200);
    });
  },

  _indexerScan(folderPath, folderId) {
    const status = $('#idx-scan-status');
    const msg    = $('#idx-scan-msg');
    const detail = $('#idx-scan-detail');
    const bar    = $('#idx-scan-bar');
    if (!status) return;
    status.style.display = '';
    msg.textContent = 'Starting scan…';

    api.indexerStartScan(folderPath).then(res => {
      if (!res.success) { showAlert(res.error || 'Scan failed', 'error'); status.style.display = 'none'; return; }
      const taskId = res.task_id;
      const poll = setInterval(async () => {
        const p = await api.indexerScanProgress(taskId);
        if (p.total > 0) {
          const pct = Math.round(p.done / p.total * 100);
          bar.style.width = pct + '%';
          msg.textContent = `Indexing… ${p.done} / ${p.total} files (${pct}%)`;
          detail.textContent = p.current ? '📄 ' + p.current.split(/[\\/]/).pop() : '';
        }
        if (p.status === 'done') {
          clearInterval(poll);
          status.style.display = 'none';
          const r = p.result || {};
          showAlert(`Scan complete — ${r.indexed||0} indexed, ${r.unchanged||0} unchanged, ${r.skipped||0} skipped, ${r.error||0} errors.`, 'success');
          this.renderIndexer($('#content'));
        }
      }, 800);
    });
  },

  // ─────────────────────────────────────────────
  // Ask My Files View  (Phase D — RAG retrieval)
  // ─────────────────────────────────────────────
  renderAsk(c) {
    c.innerHTML = `
      <div id="alert-container"></div>
      <div class="ask-hero">
        <div class="ask-hero-inner">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.75rem">
            <div class="ask-tagline" style="margin:0">&#129504; Ask a question — your documents will answer</div>
            <div id="ollama-badge" class="ollama-badge ollama-checking">&#9679; Checking Ollama…</div>
          </div>
          <div class="ask-bar">
            <textarea id="ask-input" rows="2"
              placeholder="e.g. What are the payment terms in my contracts?&#10;e.g. Summarise the Q3 report findings"
              maxlength="1000"></textarea>
            <div class="ask-bar-foot">
              <span id="ask-char-count" class="ask-char">0 / 1000</span>
              <div style="display:flex;gap:.5rem;align-items:center;flex-wrap:wrap">
                <label style="font-size:.78rem;color:var(--text-muted)">Sources</label>
                <select id="ask-topk" style="padding:.3rem .5rem;border:1px solid var(--border);border-radius:6px;background:var(--surface);color:var(--text);font-size:.8rem">
                  <option value="3">3</option>
                  <option value="5" selected>5</option>
                  <option value="8">8</option>
                  <option value="10">10</option>
                </select>
                <label style="font-size:.78rem;color:var(--text-muted)">Model</label>
                <select id="ask-model" style="padding:.3rem .5rem;border:1px solid var(--border);border-radius:6px;background:var(--surface);color:var(--text);font-size:.8rem">
                  <option value="llama3.2">llama3.2</option>
                  <option value="mistral">mistral</option>
                  <option value="phi3">phi3</option>
                  <option value="llama3">llama3</option>
                  <option value="gemma2">gemma2</option>
                </select>
                <button class="btn btn-primary" id="ask-btn">Ask</button>
              </div>
            </div>
          </div>
          <div class="ask-examples">
            <span style="color:var(--text-muted);font-size:.75rem">Try: </span>
            ${['What are the key findings?','Show me budget information','What deadlines are mentioned?','Summarise the main topics']
              .map(q => `<button class="ask-example-chip" onclick="app._askSetExample(${JSON.stringify(q)})">${q}</button>`)
              .join('')}
          </div>
          <details style="margin-top:.75rem;font-size:.78rem;color:var(--text-muted)">
            <summary style="cursor:pointer;user-select:none">&#8505;&#65039; How does this work? Will it really use my files?</summary>
            <div style="padding:.6rem .25rem;line-height:1.55">
              <strong>Yes — answers are grounded in your indexed files only.</strong>
              <ol style="margin:.4rem 0 .4rem 1.1rem;padding:0">
                <li>Your question is converted to a vector and matched against every indexed document/code chunk on this PC.</li>
                <li>The top <em>N</em> most relevant excerpts are retrieved (you control N via the Sources selector).</li>
                <li>Those excerpts are passed to a <strong>local Ollama LLM</strong> running on your machine — nothing leaves the PC.</li>
                <li>The answer cites the file path of every source it used, so you can verify it.</li>
              </ol>
              <strong>Setup:</strong>
              <ul style="margin:.3rem 0 0 1.1rem;padding:0">
                <li>Install Ollama from <a href="https://ollama.com" target="_blank" rel="noopener">ollama.com</a></li>
                <li>Run <code>ollama serve</code> (usually starts automatically)</li>
                <li>Pull a model: <code>ollama pull llama3.2</code></li>
                <li>If Ollama is offline, you'll still get the most relevant excerpts — just no AI summary.</li>
              </ul>
            </div>
          </details>
        </div>
      </div>
      <div id="ask-results" style="margin-top:1.5rem"></div>`;

    const input = $('#ask-input');
    const counter = $('#ask-char-count');
    input.addEventListener('input', () => {
      counter.textContent = `${input.value.length} / 1000`;
    });
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); this._askExec(); }
    });
    $('#ask-btn').addEventListener('click', () => this._askExec());

    // Check Ollama status asynchronously
    api.indexerOllamaStatus().then(res => {
      const badge = $('#ollama-badge');
      if (!badge) return;
      if (res.running) {
        const models = (res.models || []).join(', ') || 'no models';
        badge.className = 'ollama-badge ollama-online';
        badge.textContent = `● Ollama online · ${models}`;
        // Populate model dropdown with installed models
        const sel = $('#ask-model');
        if (sel && res.models && res.models.length) {
          sel.innerHTML = res.models
            .map(m => `<option value="${esc(m)}"${m.includes('llama3.2') ? ' selected' : ''}>${esc(m)}</option>`)
            .join('');
        }
      } else {
        badge.className = 'ollama-badge ollama-offline';
        badge.innerHTML = '&#9679; Ollama offline &mdash; <a href="https://ollama.com" target="_blank" rel="noopener">install</a> &amp; run <code>ollama serve</code>';
      }
    }).catch(() => {
      const badge = $('#ollama-badge');
      if (badge) { badge.className = 'ollama-badge ollama-offline'; badge.textContent = '● Ollama offline'; }
    });
  },

  _askSetExample(q) {
    const input = $('#ask-input');
    if (!input) return;
    input.value = q;
    $('#ask-char-count').textContent = `${q.length} / 1000`;
    input.focus();
  },

  async _askExec() {
    const question = $('#ask-input')?.value.trim();
    const top_k    = parseInt($('#ask-topk')?.value || '5');
    const model    = $('#ask-model')?.value || 'llama3.2';
    const res_el   = $('#ask-results');
    if (!question) { showAlert('Type a question first.', 'error'); return; }

    // Disable button while running
    const btn = $('#ask-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Thinking…'; }

    const ollamaBadge = $('#ollama-badge');
    const ollamaOnline = ollamaBadge && ollamaBadge.classList.contains('ollama-online');

    if (ollamaOnline) {
      await this._askExecStream(question, top_k, model, res_el);
    } else {
      await this._askExecRetrieval(question, top_k, res_el);
    }

    if (btn) { btn.disabled = false; btn.textContent = 'Ask'; }
  },

  // ── Streaming (Phase E — Ollama online) ──────────────────
  async _askExecStream(question, top_k, model, res_el) {
    res_el.innerHTML = `
      <div style="display:flex;align-items:center;gap:.75rem;padding:1rem 0;color:var(--text-muted)">
        <div class="spinner" style="width:22px;height:22px;margin:0"></div>
        <span>Retrieving documents and asking ${esc(model)}…</span>
      </div>`;

    let fetchResp;
    try {
      fetchResp = await api.indexerAskStream(question, top_k, model);
    } catch (e) {
      res_el.innerHTML = `<div class="alert alert-error">Network error: ${esc(String(e))}</div>`;
      return;
    }

    if (!fetchResp.ok) {
      let errMsg = 'Request failed';
      try { const j = await fetchResp.json(); errMsg = j.error || errMsg; } catch {}
      res_el.innerHTML = `<div class="alert alert-error">${esc(errMsg)}</div>`;
      return;
    }

    // Render skeleton immediately
    res_el.innerHTML = `
      <div class="rag-answer-header">
        <div class="rag-question-echo">&#129504; "${esc(question)}"</div>
        <div class="rag-source-count" id="rag-src-count">…</div>
      </div>
      <div class="rag-llm-box" id="rag-llm-box">
        <div class="rag-llm-label">&#129504; ${esc(model)}</div>
        <div class="rag-llm-answer" id="rag-llm-answer"><span class="rag-cursor">▋</span></div>
      </div>
      <div class="rag-sources" id="rag-sources-area"></div>`;

    const answerEl  = $('#rag-llm-answer');
    const sourcesEl = $('#rag-sources-area');
    const countEl   = $('#rag-src-count');
    let   answerText = '';
    let   sourcesRendered = false;

    const reader = fetchResp.body.getReader();
    const decoder = new TextDecoder();
    let   buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();   // keep incomplete line
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          let evt;
          try { evt = JSON.parse(line.slice(6)); } catch { continue; }

          if (evt.type === 'sources' && !sourcesRendered) {
            sourcesRendered = true;
            const srcs = evt.sources || [];
            if (countEl) countEl.textContent = `${srcs.length} source${srcs.length !== 1 ? 's' : ''}`;
            if (sourcesEl) sourcesEl.innerHTML = this._buildCitationCards(srcs);
          } else if (evt.type === 'token') {
            answerText += evt.text;
            if (answerEl) answerEl.innerHTML = this._mdToHtml(answerText) + '<span class="rag-cursor">▋</span>';
          } else if (evt.type === 'done') {
            if (answerEl) answerEl.innerHTML = this._mdToHtml(answerText);
          } else if (evt.type === 'error') {
            if (answerEl) answerEl.innerHTML = `<span style="color:var(--error)">${esc(evt.message)}</span>`;
          }
        }
      }
    } catch (e) {
      if (answerEl) answerEl.innerHTML += `<br><span style="color:var(--error)">Stream error: ${esc(String(e))}</span>`;
    }
    // Remove cursor if still there
    if (answerEl) answerEl.innerHTML = answerEl.innerHTML.replace(/<span class="rag-cursor">▋<\/span>/g, '');
  },

  // ── Retrieval-only fallback (Ollama offline) ──────────────
  async _askExecRetrieval(question, top_k, res_el) {
    res_el.innerHTML = `
      <div style="display:flex;align-items:center;gap:.75rem;padding:1rem 0;color:var(--text-muted)">
        <div class="spinner" style="width:22px;height:22px;margin:0"></div>
        <span>Searching your documents…</span>
      </div>`;

    const res = await api.indexerAsk(question, top_k);
    if (!res.success) {
      res_el.innerHTML = `<div class="alert alert-error">${esc(res.error)}</div>`; return;
    }
    if (!res.sources || !res.sources.length) {
      res_el.innerHTML = `
        <div class="empty-state">
          <h3>No relevant documents found</h3>
          <p>${esc(res.answer_hint || 'Try scanning more folders or rephrasing your question.')}</p>
          <button class="btn btn-secondary" onclick="app.navigate('indexer')">Go to File Indexer</button>
        </div>`; return;
    }
    res_el.innerHTML = `
      <div class="rag-answer-header">
        <div class="rag-question-echo">&#129504; "${esc(question)}"</div>
        <div class="rag-source-count">${res.sources.length} source${res.sources.length !== 1 ? 's' : ''}</div>
      </div>
      <div class="rag-phase-note">
        &#128161; Ollama is offline — showing retrieved excerpts only.
        Start Ollama (<code>ollama serve</code>) and reload this page to get AI answers.
      </div>
      <div class="rag-sources">${this._buildCitationCards(res.sources)}</div>`;
  },

  // ── Shared helpers ────────────────────────────────────────
  _buildCitationCards(sources) {
    return sources.map((src, i) => {
      const extClass = src.extension === '.pdf' ? 'pdf'
        : ['.jpg','.jpeg','.png','.gif','.bmp','.webp'].includes(src.extension||'') ? 'img'
        : ['.docx','.doc'].includes(src.extension||'') ? 'docx' : 'txt';
      const excerptHtml = (src.excerpts || []).map(ex =>
        `<blockquote class="rag-excerpt">${esc(ex)}</blockquote>`).join('');
      const score = src.score != null ? Math.round(src.score * 100) : null;
      return `
        <div class="rag-source-card">
          <div class="rag-source-head">
            <div class="rag-source-num">${i + 1}</div>
            <div class="src-icon ${extClass}" style="flex-shrink:0">
              ${(src.extension||'FILE').replace('.','').toUpperCase().slice(0,4)}
            </div>
            <div style="flex:1;min-width:0">
              <div class="rag-source-name">${esc(src.filename)}</div>
              <div class="rag-source-path">${esc(src.folder_path || src.file_path || '')}</div>
            </div>
            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:.3rem;flex-shrink:0">
              ${src.predicted_label ? `<span class="category-badge">${esc(src.predicted_label)}</span>` : ''}
              ${score != null ? `<span class="ls-score-badge">${score}% relevant</span>` : ''}
            </div>
          </div>
          <div class="rag-excerpts">${excerptHtml}</div>
          <div class="rag-source-foot">
            <button class="btn btn-sm btn-secondary"
              onclick="app._localFileOpen(${src.id}, ${JSON.stringify(src.file_path||'')})">
              &#128194; Open file location
            </button>
          </div>
        </div>`;
    }).join('');
  },

  // Minimal markdown → HTML: bold, italic, inline code, newlines
  _mdToHtml(text) {
    return esc(text)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/`(.+?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  },

  // ─────────────────────────────────────────────
  // Local Search View  (Phase A)
  // ─────────────────────────────────────────────
  renderLocalSearch(c) {
    this._lsQuery  = '';
    this._lsMode   = 'keyword';  // 'keyword' | 'semantic'
    c.innerHTML = `
      <div id="alert-container"></div>
      <div class="search-hero">
        <!-- Mode toggle -->
        <div class="ls-mode-bar">
          <button class="ls-mode-btn active" id="ls-mode-kw"   onclick="app._lsSetMode('keyword')">&#128269; Keyword</button>
          <button class="ls-mode-btn"        id="ls-mode-sem"  onclick="app._lsSetMode('semantic')">&#129504; Semantic AI</button>
          <span class="ls-mode-hint" id="ls-mode-hint">Exact word match &mdash; fast</span>
        </div>
        <div class="search-hero-bar">
          <span class="search-hero-icon" style="font-size:1.3rem">🔍</span>
          <input type="text" id="ls-input" placeholder="Search all your indexed files…" autocomplete="off">
          <button class="btn btn-primary" id="ls-btn" style="border-radius:8px;padding:.5rem 1.2rem">Search</button>
        </div>
        <div class="search-filters" style="gap:.75rem;flex-wrap:wrap">
          <div class="search-filter-group">
            <label>File type</label>
            <select id="ls-ext" style="padding:.4rem .6rem;border:1px solid var(--border);border-radius:6px;background:var(--surface);color:var(--text)">
              <option value="">All types</option>
              <option value=".pdf">PDF</option>
              <option value=".docx">DOCX</option>
              <option value=".txt">TXT</option>
              <option value=".md">Markdown</option>
              <option value=".xlsx">Excel</option>
              <option value=".jpg">JPG</option>
              <option value=".png">PNG</option>
            </select>
          </div>
          <div class="search-filter-group">
            <label>Folder contains</label>
            <input type="text" id="ls-folder" placeholder="e.g. Documents">
          </div>
        </div>
      </div>
      <div id="ls-results" style="margin-top:1rem"></div>`;

    const doSearch = () => {
      const q = $('#ls-input').value.trim();
      if (!q) { showAlert('Enter a search term.', 'error'); return; }
      this._localSearchExec(q);
    };
    $('#ls-btn').addEventListener('click', doSearch);
    $('#ls-input').addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });
  },

  _lsSetMode(mode) {
    this._lsMode = mode;
    const kwBtn  = $('#ls-mode-kw');
    const semBtn = $('#ls-mode-sem');
    const hint   = $('#ls-mode-hint');
    if (!kwBtn) return;
    if (mode === 'keyword') {
      kwBtn.classList.add('active');
      semBtn.classList.remove('active');
      hint.textContent = 'Exact word match — fast';
    } else {
      semBtn.classList.add('active');
      kwBtn.classList.remove('active');
      hint.textContent = 'Meaning-based AI search — finds related concepts too';
    }
  },

  async _localSearchExec(q) {
    const ext    = $('#ls-ext')?.value    || '';
    const folder = $('#ls-folder')?.value.trim() || '';
    const res_el = $('#ls-results');
    res_el.innerHTML = `<div class="spinner" style="margin:2rem auto"></div>`;

    const params = {};
    if (ext)    params.ext    = ext;
    if (folder) params.folder = folder;

    let res;
    if (this._lsMode === 'semantic') {
      res = await api.indexerSemanticSearch(q, params);
    } else {
      res = await api.indexerSearch(q, params);
    }

    if (!res.success) {
      res_el.innerHTML = `<div class="alert alert-error">${esc(res.error)}</div>`; return;
    }
    if (!res.results || !res.results.length) {
      const hint = this._lsMode === 'semantic'
        ? 'Semantic search uses AI embeddings. Scan your folders first to build the index.'
        : 'Try different keywords or add more folders to index.';
      res_el.innerHTML = `<div class="empty-state"><h3>No results for "${esc(q)}"</h3><p>${hint}</p></div>`;
      return;
    }

    const isSemantic = this._lsMode === 'semantic';
    const cards = res.results.map(f => {
      const extClass = f.extension === '.pdf' ? 'pdf'
        : ['.jpg','.jpeg','.png','.gif','.bmp','.webp'].includes(f.extension||'') ? 'img'
        : ['.docx','.doc'].includes(f.extension||'') ? 'docx' : 'txt';
      const snippetHtml = isSemantic
        ? (f.chunk_text ? `<div class="ls-snippet">${esc(f.chunk_text)}</div>` : '')
        : (f.snippet    ? `<div class="ls-snippet">${f.snippet}</div>` : '');
      const scoreBadge = isSemantic && f.score != null
        ? `<span class="ls-score-badge">${Math.round(f.score * 100)}% match</span>` : '';
      return `
        <div class="search-result-card" onclick="app._localFileOpen(${f.id}, ${JSON.stringify(f.file_path||'')})">
          <div class="src-icon ${extClass}">${(f.extension||'FILE').replace('.','').toUpperCase().slice(0,4)}</div>
          <div class="src-body">
            <div class="src-name" title="${esc(f.file_path)}">${esc(f.filename)}</div>
            <div class="src-meta">
              <span class="text-muted" style="font-size:.75rem">${esc(f.folder_path||'')}</span>
              ${f.predicted_label ? `<span class="category-badge" style="font-size:.7rem">${esc(f.predicted_label)}</span>` : ''}
              ${f.file_size ? `<span class="text-muted" style="font-size:.75rem">${fmt_size(f.file_size)}</span>` : ''}
              ${scoreBadge}
            </div>
            ${snippetHtml}
          </div>
          <div class="action-btns">
            <button class="action-btn open" title="Open file location"
              onclick="event.stopPropagation();app._localFileOpen(${f.id},${JSON.stringify(f.file_path||'')})">${ICONS.open}</button>
          </div>
        </div>`;
    }).join('');

    const modeLabel = isSemantic ? ' (semantic AI)' : ' (keyword)';
    res_el.innerHTML = `
      <div class="search-results-header">
        <span>${res.count} result${res.count !== 1 ? 's' : ''} for "<strong>${esc(q)}</strong>"${modeLabel}</span>
      </div>
      <div class="search-results-list">${cards}</div>`;
  },

  async _localFileOpen(id, filePath) {
    await api.indexerRecordOpen(id);
    showAlert(`📂 ${filePath}`, 'success');
  },
};

// Boot on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => app.init());
