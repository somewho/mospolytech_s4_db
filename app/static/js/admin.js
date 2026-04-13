/* ================================================================
   FilmDB Admin — Vanilla JS SPA
   ================================================================ */

// ── Auth guard ────────────────────────────────────────────────────────────────
(async () => {
  const token = localStorage.getItem('filmdb_token');
  if (!token) { window.location.href = '/?need_login=1'; return; }
  try {
    const res = await fetch('/api/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    if (!data.can_admin) {
      document.body.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:center;height:100vh;
                    background:#0f172a;color:#f8fafc;font-family:sans-serif;flex-direction:column;gap:16px">
          <div style="font-size:48px">🔒</div>
          <div style="font-size:20px">Нет прав доступа к панели управления</div>
          <a href="/" style="color:#3b82f6">← На главную</a>
        </div>`;
    }
  } catch {
    window.location.href = '/?need_login=1';
  }
})();

// ── API Client ───────────────────────────────────────────────────────────────
const API = {
  async request(method, url, body = null) {
    const token = localStorage.getItem('filmdb_token');
    const opts = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    };
    if (body !== null) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try { const j = await res.json(); detail = j.detail || JSON.stringify(j); } catch {}
      throw new Error(detail);
    }
    if (res.status === 204) return null;
    return res.json();
  },
  get:    (url)        => API.request('GET',    url),
  post:   (url, body)  => API.request('POST',   url, body),
  put:    (url, body)  => API.request('PUT',    url, body),
  delete: (url, body)  => API.request('DELETE', url, body ?? undefined),

  meta:       ()                      => API.get('/api/meta/tables'),
  tableMeta:  (t)                     => API.get(`/api/meta/tables/${t}`),
  fkOptions:  (t, col)  => API.get(`/api/meta/fk/${t}/${encodeURIComponent(col)}`),
  list:       (t, o, l, s, sc)       => {
    let url = `/api/tables/${t}?offset=${o}&limit=${l}`;
    if (s && sc) url += `&search=${encodeURIComponent(s)}&search_column=${sc}`;
    return API.get(url);
  },
  getOne:     (t, pk)                 => API.get(`/api/tables/${t}/${pk}`),
  create:     (t, data)               => API.post(`/api/tables/${t}`, data),
  update:     (t, pk, data)           => API.put(`/api/tables/${t}/${pk}`, data),
  deleteOne:  (t, pk)                 => API.delete(`/api/tables/${t}/${pk}`),
  deleteComp: (t, data)               => API.delete(`/api/tables/${t}`, data),
};

// ── Toast ────────────────────────────────────────────────────────────────────
const Toast = {
  show(type, title, msg = '', duration = 3500) {
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.innerHTML = `
      <div class="toast-icon">${icons[type] || 'ℹ️'}</div>
      <div class="toast-body">
        <div class="toast-title">${title}</div>
        ${msg ? `<div class="toast-msg">${msg}</div>` : ''}
      </div>`;
    document.getElementById('toast-container').appendChild(el);
    setTimeout(() => {
      el.style.animation = 'fadeOut .3s ease forwards';
      setTimeout(() => el.remove(), 300);
    }, duration);
  },
  success: (t, m) => Toast.show('success', t, m),
  error:   (t, m) => Toast.show('error',   t, m),
  info:    (t, m) => Toast.show('info',    t, m),
};

// ── Confirm dialog ───────────────────────────────────────────────────────────
const Confirm = {
  show(title, text) {
    return new Promise(resolve => {
      document.getElementById('confirm-title').textContent = title;
      document.getElementById('confirm-text').textContent  = text;
      const modal = document.getElementById('confirm-modal');
      modal.classList.remove('hidden');
      const ok     = document.getElementById('confirm-ok');
      const cancel = document.getElementById('confirm-cancel');
      const close = (val) => {
        modal.classList.add('hidden');
        ok.replaceWith(ok.cloneNode(true));
        cancel.replaceWith(cancel.cloneNode(true));
        resolve(val);
      };
      document.getElementById('confirm-ok').addEventListener('click',     () => close(true));
      document.getElementById('confirm-cancel').addEventListener('click', () => close(false));
    });
  }
};

// ── State ─────────────────────────────────────────────────────────────────────
const State = {
  groups:    [],       // sidebar nav
  tableMeta: {},       // cache: tableName → meta
  fkCache:   {},       // cache: "table/col" → [{value,label}]
  current: {
    table:   null,
    page:    1,
    limit:   50,
    search:  '',
    searchCol: null,
  },
};

// ── Helpers ──────────────────────────────────────────────────────────────────
function esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function formatCell(val) {
  if (val === null || val === undefined) return '<span style="color:var(--text-muted)">—</span>';
  const s = String(val);
  if (s.length > 60) return `<span title="${esc(s)}">${esc(s.slice(0, 60))}…</span>`;
  return esc(s);
}

async function getTableMeta(name) {
  if (!State.tableMeta[name]) {
    State.tableMeta[name] = await API.tableMeta(name);
  }
  return State.tableMeta[name];
}

async function getFkOptions(refTable, refLabel) {
  const key = `${refTable}/${refLabel}`;
  if (!State.fkCache[key]) {
    State.fkCache[key] = await API.fkOptions(refTable, refLabel);
  }
  return State.fkCache[key];
}

function getNavIcon(group) {
  const icons = {
    'Справочники': '🌍',
    'Фильмы':      '🎬',
    'Персоны':     '🎭',
    'Пользователи':'👥',
    'Активность':  '📊',
    'Фестивали и награды': '🏆',
    'RBAC':        '🔐',
  };
  return icons[group] || '📋';
}

// ── Sidebar ───────────────────────────────────────────────────────────────────
async function initSidebar() {
  State.groups = await API.meta();
  const nav = document.getElementById('sidebar-nav');
  nav.innerHTML = State.groups.map(g => `
    <div class="nav-group">
      <div class="group-label">${esc(g.group)}</div>
      ${g.tables.map(t => `
        <div class="nav-item" data-table="${t.name}" title="${esc(t.label)}">
          <span class="nav-icon">${getNavIcon(g.group)}</span>
          <span>${esc(t.label)}</span>
        </div>`).join('')}
    </div>`).join('');

  nav.addEventListener('click', e => {
    const item = e.target.closest('.nav-item');
    if (!item) return;
    openTable(item.dataset.table);
  });
}

function setActiveNav(tableName) {
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.table === tableName);
  });
}

function setBreadcrumb(parts) {
  const bc = document.getElementById('breadcrumb');
  bc.innerHTML = parts.map((p, i) =>
    i < parts.length - 1
      ? `<span>${esc(p)}</span><span class="sep">/</span>`
      : `<span class="crumb">${esc(p)}</span>`
  ).join('');
}

// ── Table List View ──────────────────────────────────────────────────────────
async function openTable(tableName) {
  State.current.table     = tableName;
  State.current.page      = 1;
  State.current.search    = '';
  State.current.searchCol = null;
  setActiveNav(tableName);

  const meta = await getTableMeta(tableName);
  setBreadcrumb([meta.label]);
  await renderList(meta);
}

async function renderList(meta) {
  const content = document.getElementById('content');
  content.innerHTML = `<div class="spinner"></div>`;

  const { table, page, limit, search, searchCol } = State.current;
  const offset = (page - 1) * limit;
  let result;
  try {
    result = await API.list(table, offset, limit, search, searchCol);
  } catch (e) {
    content.innerHTML = `<div class="card card-body" style="color:var(--danger)">Ошибка загрузки: ${esc(e.message)}</div>`;
    return;
  }

  const { data, total } = result;
  const listCols = meta.list_columns || meta.columns.map(c => c.name);
  const colMeta  = Object.fromEntries(meta.columns.map(c => [c.name, c]));

  // Предзагрузить FK-метки для всех FK-колонок в list_columns
  const fkMaps = {};
  await Promise.all(
    listCols
      .filter(c => colMeta[c]?.type === 'fk')
      .map(async c => {
        const col = colMeta[c];
        try {
          const opts = await getFkOptions(col.ref_table, col.ref_label);
          fkMaps[c] = Object.fromEntries(opts.map(o => [String(o.value), String(o.label)]));
        } catch { fkMaps[c] = {}; }
      })
  );
  const cellHtml = (c, val) => {
    if (colMeta[c]?.type === 'fk' && fkMaps[c]) {
      const label = fkMaps[c][String(val)];
      if (label) return `<span title="ID ${esc(String(val))}">${esc(label)}</span>`;
    }
    return formatCell(val);
  };

  // searchable string/str columns
  const searchableCols = meta.columns.filter(c =>
    ['str','int','decimal','date','datetime','enum'].includes(c.type) && !c.readonly
  );

  const totalPages = Math.ceil(total / limit);
  const pk = meta.pk;
  const compPk = meta.composite_pk;

  content.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h2>${esc(meta.label)}
          <span class="badge badge-gray" style="margin-left:8px;font-size:12px">${total}</span>
        </h2>
        ${(pk || compPk) ? `<button class="btn btn-primary btn-sm" id="btn-new">+ Добавить</button>` : ''}
      </div>

      <div class="toolbar">
        <div class="search-wrap">
          <span class="search-icon">🔍</span>
          <input type="text" id="search-input" placeholder="Поиск…" value="${esc(search)}" />
        </div>
        <select id="search-col-select" class="search-col-select">
          <option value="">— колонка —</option>
          ${searchableCols.map(c =>
            `<option value="${c.name}" ${searchCol === c.name ? 'selected' : ''}>${esc(c.label)}</option>`
          ).join('')}
        </select>
      </div>

      <div class="table-wrap">
        ${data.length === 0 ? `
          <div class="empty-state">
            <div class="empty-icon">🗄️</div>
            <p>Записи не найдены</p>
          </div>
        ` : `
          <table>
            <thead>
              <tr>
                ${listCols.map(c => `<th>${esc(colMeta[c]?.label || c)}</th>`).join('')}
                <th style="width:100px">Действия</th>
              </tr>
            </thead>
            <tbody>
              ${data.map(row => `
                <tr>
                  ${listCols.map(c => `<td>${cellHtml(c, row[c])}</td>`).join('')}
                  <td>
                    <div class="td-actions">
                      ${pk ? `<button class="btn-edit" data-pk="${esc(row[pk])}">Изм.</button>` : ''}
                      <button class="btn-delete"
                        ${pk ? `data-pk="${esc(row[pk])}"` : ''}
                        ${compPk ? `data-comp="${esc(JSON.stringify(Object.fromEntries(compPk.map(k => [k, row[k]]))))}"` : ''}
                      >Удал.</button>
                    </div>
                  </td>
                </tr>`).join('')}
            </tbody>
          </table>
        `}
      </div>

      <div class="pagination">
        <span>Показано ${offset + 1}–${Math.min(offset + limit, total)} из ${total}</span>
        <div class="pagination-controls">
          ${renderPagination(page, totalPages)}
        </div>
      </div>
    </div>`;

  // Events
  document.getElementById('btn-new')?.addEventListener('click', () => openForm(meta, null));

  document.querySelectorAll('.btn-edit').forEach(btn => {
    btn.addEventListener('click', () => openForm(meta, btn.dataset.pk));
  });

  document.querySelectorAll('.btn-delete').forEach(btn => {
    btn.addEventListener('click', () => {
      const pkVal  = btn.dataset.pk;
      const comp   = btn.dataset.comp ? JSON.parse(btn.dataset.comp) : null;
      handleDelete(meta, pkVal, comp);
    });
  });

  document.querySelectorAll('.page-btn').forEach(btn => {
    if (!btn.disabled) {
      btn.addEventListener('click', () => {
        State.current.page = parseInt(btn.dataset.page);
        renderList(meta);
      });
    }
  });

  const searchInput  = document.getElementById('search-input');
  const searchSelect = document.getElementById('search-col-select');
  let searchTimer;
  searchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      State.current.search    = searchInput.value.trim();
      State.current.searchCol = searchSelect.value || null;
      State.current.page      = 1;
      renderList(meta);
    }, 400);
  });
  searchSelect.addEventListener('change', () => {
    State.current.searchCol = searchSelect.value || null;
    if (State.current.search) renderList(meta);
  });
}

function renderPagination(page, totalPages) {
  if (totalPages <= 1) return '';
  const pages = [];
  const range = [];
  // always show first, last, current ±2
  const add = (p) => { if (p >= 1 && p <= totalPages && !range.includes(p)) range.push(p); };
  add(1); add(totalPages);
  for (let p = page - 2; p <= page + 2; p++) add(p);
  range.sort((a,b)=>a-b);

  let prev = 0;
  for (const p of range) {
    if (p - prev > 1) pages.push(`<span style="padding:0 4px;color:var(--text-muted)">…</span>`);
    pages.push(`<button class="page-btn ${p===page?'active':''}" data-page="${p}">${p}</button>`);
    prev = p;
  }

  return `
    <button class="page-btn" data-page="${page-1}" ${page<=1?'disabled':''}>‹</button>
    ${pages.join('')}
    <button class="page-btn" data-page="${page+1}" ${page>=totalPages?'disabled':''}>›</button>`;
}

// ── Delete ────────────────────────────────────────────────────────────────────
async function handleDelete(meta, pkVal, comp) {
  const confirmed = await Confirm.show(
    'Удалить запись',
    `Вы уверены, что хотите удалить запись ${pkVal ? '#' + pkVal : ''}? Это действие необратимо.`
  );
  if (!confirmed) return;
  try {
    if (comp) {
      await API.deleteComp(meta.__name || State.current.table, comp);
    } else {
      await API.deleteOne(State.current.table, pkVal);
    }
    Toast.success('Запись удалена');
    renderList(meta);
  } catch (e) {
    Toast.error('Ошибка удаления', e.message);
  }
}

// ── Form View ─────────────────────────────────────────────────────────────────
async function openForm(meta, pkValue) {
  const isEdit = pkValue !== null && pkValue !== undefined;
  const content = document.getElementById('content');
  content.innerHTML = `<div class="spinner"></div>`;
  setBreadcrumb([meta.label, isEdit ? `Редактировать #${pkValue}` : 'Создать']);

  let record = {};
  if (isEdit) {
    try {
      record = await API.getOne(State.current.table, pkValue);
    } catch (e) {
      Toast.error('Ошибка загрузки', e.message);
      return;
    }
  }

  // Preload FK options
  const fkCols = meta.columns.filter(c => c.type === 'fk');
  await Promise.all(fkCols.map(c => getFkOptions(c.ref_table, c.ref_label)));

  content.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h2>${isEdit ? `Редактировать: ${meta.label} #${pkValue}` : `Создать: ${meta.label}`}</h2>
        <button class="btn btn-ghost btn-sm" id="btn-back">← Назад</button>
      </div>
      <div class="card-body">
        <form id="record-form" autocomplete="off">
          <div class="form-grid">
            ${meta.columns.map(col => renderField(col, record[col.name], isEdit)).join('')}
          </div>
          <div class="form-actions">
            <button type="submit" class="btn btn-primary" id="btn-submit">
              ${isEdit ? '💾 Сохранить' : '➕ Создать'}
            </button>
            <button type="button" class="btn btn-ghost" id="btn-cancel">Отмена</button>
            <span id="form-error" style="color:var(--danger);font-size:13px"></span>
          </div>
        </form>
      </div>
    </div>`;

  document.getElementById('btn-back').addEventListener('click', () => renderList(meta));
  document.getElementById('btn-cancel').addEventListener('click', () => renderList(meta));

  document.getElementById('record-form').addEventListener('submit', async e => {
    e.preventDefault();
    const errEl = document.getElementById('form-error');
    errEl.textContent = '';
    const btn = document.getElementById('btn-submit');
    btn.disabled = true;
    btn.textContent = '…';

    const data = collectForm(meta, isEdit ? record : null);
    try {
      if (isEdit) {
        await API.update(State.current.table, pkValue, data);
        Toast.success('Сохранено');
      } else {
        await API.create(State.current.table, data);
        Toast.success('Создано');
      }
      renderList(meta);
    } catch (ex) {
      errEl.textContent = ex.message;
      btn.disabled = false;
      btn.textContent = isEdit ? '💾 Сохранить' : '➕ Создать';
    }
  });
}

function renderField(col, value, isEdit = false) {
  const val  = value ?? '';
  const ro   = col.readonly;
  const req  = col.required ? '<span class="required">*</span>' : '';
  const wide = col.type === 'text' ? ' full-width' : '';

  let input;

  if (ro) {
    input = `<input type="text" value="${esc(String(val))}" readonly />`;
  } else if (col.type === 'password') {
    const ph = isEdit ? 'Оставьте пустым, чтобы не менять' : 'Новый пароль';
    input = `<input type="password" name="${col.name}" placeholder="${ph}" autocomplete="new-password" ${!isEdit && col.required !== false ? 'required' : ''} />`;
  } else if (col.type === 'fk') {
    const opts = State.fkCache[`${col.ref_table}/${col.ref_label}`] || [];
    const optHtml = opts.map(o =>
      `<option value="${esc(o.value)}" ${String(o.value) === String(val) ? 'selected' : ''}>${esc(o.label)}</option>`
    ).join('');
    input = `
      <select name="${col.name}" ${col.required ? 'required' : ''}>
        <option value="">— не выбрано —</option>
        ${optHtml}
      </select>`;
  } else if (col.type === 'enum') {
    const choices = col.choices || [];
    input = `
      <select name="${col.name}" ${col.required ? 'required' : ''}>
        <option value="">— не выбрано —</option>
        ${choices.map(c => `<option ${String(c) === String(val) ? 'selected' : ''}>${esc(c)}</option>`).join('')}
      </select>`;
  } else if (col.type === 'text') {
    input = `<textarea name="${col.name}" ${col.required ? 'required' : ''}>${esc(String(val))}</textarea>`;
  } else if (col.type === 'date') {
    const dateVal = val ? String(val).slice(0, 10) : '';
    input = `<input type="date" name="${col.name}" value="${esc(dateVal)}" ${col.required ? 'required' : ''} />`;
  } else if (col.type === 'datetime') {
    let dtVal = '';
    if (val) {
      try { dtVal = new Date(val).toISOString().slice(0, 16); } catch {}
    }
    input = `<input type="datetime-local" name="${col.name}" value="${esc(dtVal)}" ${col.required ? 'required' : ''} />`;
  } else if (col.type === 'int') {
    input = `<input type="number" name="${col.name}" value="${esc(String(val))}" step="1" ${col.required ? 'required' : ''} />`;
  } else if (col.type === 'decimal') {
    input = `<input type="number" name="${col.name}" value="${esc(String(val))}" step="0.01" ${col.required ? 'required' : ''} />`;
  } else {
    // str / default
    input = `<input type="text" name="${col.name}" value="${esc(String(val))}" ${col.required ? 'required' : ''} />`;
  }

  return `
    <div class="form-group${wide}">
      <label for="${col.name}">${esc(col.label)}${req}</label>
      ${input}
    </div>`;
}

function collectForm(meta, original) {
  const form = document.getElementById('record-form');
  const data = {};
  for (const col of meta.columns) {
    if (col.readonly) continue;
    const el = form.elements[col.name];
    if (!el) continue;
    let val = el.value;
    if (val === '' || val === null) {
      data[col.name] = null;
    } else if (col.type === 'int') {
      data[col.name] = parseInt(val, 10);
    } else if (col.type === 'decimal') {
      data[col.name] = parseFloat(val);
    } else if (col.type === 'fk') {
      data[col.name] = val === '' ? null : parseInt(val, 10);
    } else {
      data[col.name] = val;
    }
  }
  return data;
}

// ── Sidebar toggle ────────────────────────────────────────────────────────────
document.getElementById('sidebar-toggle').addEventListener('click', () => {
  document.getElementById('sidebar').classList.toggle('collapsed');
});

// ── Init ──────────────────────────────────────────────────────────────────────
(async () => {
  try {
    await initSidebar();
  } catch (e) {
    document.getElementById('sidebar-nav').innerHTML =
      `<div class="nav-loading" style="color:#f87171">Ошибка: ${esc(e.message)}</div>`;
  }
})();
