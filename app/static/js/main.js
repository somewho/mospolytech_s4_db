/* ================================================================
   FilmDB — Vanilla JS SPA
   ================================================================ */

'use strict';

// ── Poster gradients (placeholder без реальных постеров) ──────────────────────
const GRADIENTS = [
  ['#1a1a2e','#16213e'],['#2d1b69','#11998e'],['#4b134f','#c94b4b'],
  ['#0f3460','#533483'],['#093028','#237a57'],['#1f4037','#99f2c8'],
  ['#3a1c71','#d76d77'],['#0575e6','#021b79'],['#373b44','#4286f4'],
  ['#4b6cb7','#182848'],['#283048','#859f7c'],['#1c1c2e','#c56e2a'],
];

function posterStyle(id, title) {
  const i = ((id || 0) + (title?.charCodeAt(0) || 0)) % GRADIENTS.length;
  const [a, b] = GRADIENTS[i];
  return `background: linear-gradient(145deg, ${a}, ${b});`;
}

function ratingClass(r) {
  const n = parseFloat(r) || 0;
  if (n >= 7.5) return 'rating-high';
  if (n >= 5.0) return 'rating-mid';
  return 'rating-low';
}

function ratingColor(r) {
  const n = parseFloat(r) || 0;
  if (n >= 7.5) return '#4ade80';
  if (n >= 5.0) return '#fbbf24';
  return '#f87171';
}

function avatarColor(id) {
  const palette = [
    '#5b8def','#e8b400','#22c55e','#a855f7','#ef4444',
    '#06b6d4','#f97316','#84cc16','#ec4899',
  ];
  return palette[(id || 0) % palette.length];
}

function esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function fmt(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('ru-RU');
}

function fmtYear(d) {
  if (!d) return '';
  return String(d).slice(0, 4);
}

function roleLabel(r) {
  const map = {
    director:'Режиссёр', actor:'Актёр', producer:'Продюсер',
    writer:'Сценарист', composer:'Композитор',
    cinematographer:'Оператор', editor:'Монтажёр', critic:'Критик',
  };
  return map[r] || r;
}

// ── Toast ─────────────────────────────────────────────────────────────────────
function toast(type, title, msg = '', ms = 3500) {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<div><div class="toast-title">${esc(title)}</div>${msg ? `<div class="toast-msg">${esc(msg)}</div>` : ''}</div>`;
  document.getElementById('toast-root').appendChild(el);
  setTimeout(() => {
    el.style.animation = 'slideOut .3s ease forwards';
    setTimeout(() => el.remove(), 300);
  }, ms);
}

// ── API ───────────────────────────────────────────────────────────────────────
const API = {
  async req(method, url, body = null) {
    const token = Auth.token;
    const res = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      ...(body !== null ? { body: JSON.stringify(body) } : {}),
    });
    if (!res.ok) {
      let msg = `HTTP ${res.status}`;
      try { msg = (await res.json()).detail || msg; } catch {}
      throw new Error(msg);
    }
    return res.json();
  },

  films:     (p) => API.req('GET', `/api/public/films?page=${p.page||1}&limit=${p.limit||20}${p.genre?`&genre_id=${p.genre}`:''}${p.search?`&search=${encodeURIComponent(p.search)}`:''}${p.sort?`&sort=${p.sort}`:''}`),
  film:      (id) => API.req('GET', `/api/public/films/${id}`),
  genres:    ()   => API.req('GET', '/api/public/genres'),
  persons:   (p) => API.req('GET', `/api/public/persons${p.search?`?search=${encodeURIComponent(p.search)}`:''}${p.role?(p.search?`&role=${p.role}`:`?role=${p.role}` ):''}`),
  person:    (id) => API.req('GET', `/api/public/persons/${id}`),
  festivals: ()   => API.req('GET', '/api/public/festivals'),
  createReview: (d) => API.req('POST', '/api/public/reviews', d),
  myReviews:    ()  => API.req('GET', '/api/public/profile/reviews'),
  login:     (e, p) => API.req('POST', '/api/auth/login', { email: e, password: p }),
  register:  (d)    => API.req('POST', '/api/auth/register', d),
  me:        ()     => API.req('GET', '/api/auth/me'),
};

// ── Auth ──────────────────────────────────────────────────────────────────────
const Auth = {
  user:     null,
  token:    null,
  roles:    [],
  canAdmin: false,

  init() {
    this.token = localStorage.getItem('filmdb_token');
    const saved = localStorage.getItem('filmdb_user');
    if (saved) try { const d = JSON.parse(saved); this.user = d.user; this.roles = d.roles; this.canAdmin = d.can_admin; } catch {}
  },

  async refresh() {
    if (!this.token) return;
    try {
      const d = await API.me();
      this.user = d.user; this.roles = d.roles; this.canAdmin = d.can_admin;
      localStorage.setItem('filmdb_user', JSON.stringify(d));
    } catch {
      this.logout();
    }
  },

  save(data) {
    this.token    = data.access_token;
    this.user     = data.user;
    this.roles    = data.roles;
    this.canAdmin = data.can_admin;
    localStorage.setItem('filmdb_token', this.token);
    localStorage.setItem('filmdb_user',  JSON.stringify({ user: this.user, roles: this.roles, can_admin: this.canAdmin }));
  },

  logout() {
    this.token = null; this.user = null; this.roles = []; this.canAdmin = false;
    localStorage.removeItem('filmdb_token');
    localStorage.removeItem('filmdb_user');
  },

  async doLogin(email, password) {
    const d = await API.login(email, password);
    this.save(d);
  },

  async doRegister(data) {
    const d = await API.register(data);
    this.save(d);
  },
};

// ── Auth modal ────────────────────────────────────────────────────────────────
const AuthModal = {
  open(tab = 'login') {
    const modal = document.getElementById('auth-modal');
    modal.classList.remove('hidden');
    this.switchTab(tab);
    setTimeout(() => {
      const inp = tab === 'login'
        ? document.getElementById('login-email')
        : document.getElementById('reg-firstname');
      inp?.focus();
    }, 50);
  },
  close() {
    document.getElementById('auth-modal').classList.add('hidden');
    document.getElementById('login-error').classList.add('hidden');
    document.getElementById('reg-error').classList.add('hidden');
  },
  switchTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
    document.getElementById('auth-login').classList.toggle('hidden', tab !== 'login');
    document.getElementById('auth-register').classList.toggle('hidden', tab !== 'register');
  },
};

// ── Nav ───────────────────────────────────────────────────────────────────────
function renderNav() {
  const el = document.getElementById('nav-auth');
  if (!Auth.user) {
    el.innerHTML = `
      <button class="btn btn-ghost btn-sm" id="nav-guest-hint">Гостевой режим</button>
      <button class="btn btn-gold btn-sm" id="nav-login">Войти</button>`;
    document.getElementById('nav-login').onclick = () => AuthModal.open('login');
    document.getElementById('nav-guest-hint').onclick = () => {
      toast('info', 'Гостевой режим', 'Вы можете просматривать фильмы, персон и фестивали без авторизации');
    };
  } else {
    const { first_name, last_name, email } = Auth.user;
    const initials = [first_name, last_name].filter(Boolean).map(s => s[0]).join('').toUpperCase();
    el.innerHTML = `
      <div class="user-menu" id="user-menu">
        <div class="user-name-btn" id="user-btn">
          <div class="user-avatar" style="background:${esc(avatarColor(Auth.user.user_id))}">${esc(initials)}</div>
          ${esc(first_name)} ▾
        </div>
        <div class="dropdown hidden" id="user-dropdown">
          <div class="dropdown-header">
            <div class="dropdown-name">${esc(first_name)} ${esc(last_name || '')}</div>
            <div class="dropdown-email">${esc(email)}</div>
          </div>
          <div class="dropdown-item" id="dd-profile">👤 Мой профиль</div>
          ${Auth.canAdmin ? `<div class="dropdown-item admin-link" id="dd-admin">⚙️ Панель управления</div>` : ''}
          <div class="dropdown-sep"></div>
          <div class="dropdown-item danger" id="dd-logout">↩ Выйти</div>
        </div>
      </div>`;
    document.getElementById('user-btn').onclick = (e) => {
      e.stopPropagation();
      document.getElementById('user-dropdown').classList.toggle('hidden');
    };
    document.getElementById('dd-profile').onclick = () => {
      document.getElementById('user-dropdown').classList.add('hidden');
      Router.go('profile');
    };
    document.getElementById('dd-admin')?.addEventListener('click', () => {
      window.location.href = '/admin';
    });
    document.getElementById('dd-logout').onclick = () => {
      Auth.logout(); renderNav();
      toast('success', 'Вы вышли из аккаунта');
      Router.go('films');
    };
  }

  // active nav link
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.toggle('active', link.dataset.page === Router.page);
    link.onclick = () => Router.go(link.dataset.page);
  });
}

// ── Router ────────────────────────────────────────────────────────────────────
const Router = {
  page:   'films',
  params: {},

  go(page, params = {}) {
    this.page   = page;
    this.params = params;
    renderNav();
    Pages.render(page, params);
    window.scrollTo(0, 0);
  },
};

// ── Pagination helper ─────────────────────────────────────────────────────────
function renderPager(page, total, onGo) {
  if (total <= 1) return '';
  const range = new Set([1, total]);
  for (let p = page - 2; p <= page + 2; p++) if (p >= 1 && p <= total) range.add(p);
  const sorted = [...range].sort((a, b) => a - b);
  const btns = [];
  let prev = 0;
  for (const p of sorted) {
    if (p - prev > 1) btns.push(`<span style="color:var(--text-dim);padding:0 4px">…</span>`);
    btns.push(`<button class="page-btn${p===page?' active':''}" data-p="${p}">${p}</button>`);
    prev = p;
  }
  return `<div class="pagination">
    <button class="page-btn" data-p="${page-1}" ${page<=1?'disabled':''}>‹</button>
    ${btns.join('')}
    <button class="page-btn" data-p="${page+1}" ${page>=total?'disabled':''}>›</button>
  </div>`;
}

function bindPager(wrap, onGo) {
  wrap.querySelectorAll('.page-btn:not(:disabled)').forEach(btn => {
    btn.onclick = () => onGo(parseInt(btn.dataset.p));
  });
}

// ── Pages ─────────────────────────────────────────────────────────────────────
const Pages = {
  _genres: null,

  async _getGenres() {
    if (!this._genres) this._genres = await API.genres();
    return this._genres;
  },

  render(page, params) {
    const root = document.getElementById('page-root');
    root.innerHTML = `<div class="spinner-wrap"><div class="spinner"></div></div>`;
    const fn = this[page];
    if (fn) fn.call(this, params, root);
    else this.films({}, root);
  },

  // ── Films catalog ──────────────────────────────────────────────────────────
  async films(params, root) {
    const state = { page: 1, search: '', genre: null, sort: 'rating', ...params };
    const genres = await this._getGenres();

    const draw = async () => {
      root.innerHTML = `<div class="spinner-wrap"><div class="spinner"></div></div>`;
      let res;
      try { res = await API.films(state); } catch(e) {
        root.innerHTML = `<div class="container page"><p style="color:var(--red)">Ошибка: ${esc(e.message)}</p></div>`;
        return;
      }
      const { data, total, total_pages } = res;

      root.innerHTML = `
        <div class="container page">
          <div class="search-bar">
            <div class="search-wrap">
              <span class="search-icon">🔍</span>
              <input id="film-search" type="text" placeholder="Поиск фильмов…" value="${esc(state.search)}" />
            </div>
            <select id="film-sort" class="sort-select">
              <option value="rating" ${state.sort==='rating'?'selected':''}>По рейтингу</option>
              <option value="date"   ${state.sort==='date'?'selected':''}>По дате</option>
              <option value="title"  ${state.sort==='title'?'selected':''}>По названию</option>
            </select>
          </div>
          <div class="genre-chips">
            <div class="genre-chip${!state.genre?' active':''}" data-gid="">Все</div>
            ${genres.map(g => `<div class="genre-chip${state.genre===g.genre_id?' active':''}" data-gid="${g.genre_id}">${esc(g.name)}</div>`).join('')}
          </div>
          <div class="section-head">
            <h2>Фильмы <span style="font-size:14px;color:var(--text-muted);font-weight:400">${total}</span></h2>
          </div>
          <div class="films-grid" id="films-grid">
            ${data.length === 0
              ? `<div class="empty" style="grid-column:1/-1"><div class="empty-icon">🎬</div><p>Ничего не найдено</p></div>`
              : data.map(f => filmCard(f)).join('')
            }
          </div>
          ${renderPager(state.page, total_pages, (p) => { state.page = p; draw(); })}
        </div>`;

      // Film click
      root.querySelectorAll('.film-card').forEach(c => {
        c.onclick = () => Router.go('film', { id: parseInt(c.dataset.id) });
      });
      // Genre filter
      root.querySelectorAll('.genre-chip').forEach(c => {
        c.onclick = () => { state.genre = c.dataset.gid ? parseInt(c.dataset.gid) : null; state.page = 1; draw(); };
      });
      // Search
      let st;
      root.querySelector('#film-search').oninput = e => {
        clearTimeout(st); st = setTimeout(() => { state.search = e.target.value; state.page = 1; draw(); }, 400);
      };
      // Sort
      root.querySelector('#film-sort').onchange = e => { state.sort = e.target.value; state.page = 1; draw(); };
      // Pager
      bindPager(root, (p) => { state.page = p; draw(); });
    };

    draw();
  },

  // ── Film detail ────────────────────────────────────────────────────────────
  async film(params, root) {
    let data;
    try { data = await API.film(params.id); } catch(e) {
      root.innerHTML = `<div class="container page"><p style="color:var(--red)">Ошибка: ${esc(e.message)}</p></div>`;
      return;
    }
    const { film, genres, persons, reviews, awards } = data;
    const directors = persons.filter(p => p.role === 'director');
    const cast = persons.filter(p => p.role !== 'director');
    const year = fmtYear(film.created_date);
    const ps = posterStyle(film.film_id, film.title);
    const rating = parseFloat(film.average_rating) || 0;

    root.innerHTML = `
      <div class="film-hero">
        <div class="film-hero-bg" style="${ps}"></div>
        <div class="container">
          <div class="film-hero-content">
            <div class="film-poster-lg" style="${ps}">
              <span style="font-size:64px;opacity:.3">${esc(film.title[0])}</span>
            </div>
            <div class="film-info-block">
              <div style="margin-bottom:8px">
                <span style="color:var(--text-muted);font-size:13px;cursor:pointer" onclick="Router.go('films')">← Все фильмы</span>
              </div>
              <h1 class="film-title-lg">${esc(film.title)}</h1>
              <div class="film-meta-row">
                ${year  ? `<span class="film-meta-tag">📅 ${esc(year)}</span>` : ''}
                ${film.age_restriction ? `<span class="film-meta-tag">🔞 ${esc(film.age_restriction)}</span>` : ''}
                ${directors.length ? `<span class="film-meta-tag">🎬 ${esc(directors.map(d => `${d.first_name} ${d.last_name||''}`).join(', '))}</span>` : ''}
              </div>
              <div class="film-rating-lg ${ratingClass(rating)}" style="color:${ratingColor(rating)}">
                ⭐ ${rating > 0 ? rating.toFixed(1) : '—'} <span style="font-size:14px;font-weight:400;color:var(--text-muted)">/ 10</span>
              </div>
              <div class="film-genres-row">
                ${genres.map(g => `<span class="genre-tag">${esc(g.name)}</span>`).join('')}
              </div>
              ${film.description ? `<p class="film-desc">${esc(film.description)}</p>` : ''}
            </div>
          </div>
        </div>
      </div>

      <div class="container">
        <div class="tabs" id="film-tabs">
          <div class="tab active" data-tab="cast">Актёры (${cast.length})</div>
          <div class="tab" data-tab="reviews">Рецензии (${reviews.length})</div>
          ${awards.length ? `<div class="tab" data-tab="awards">Награды (${awards.length})</div>` : ''}
        </div>
        <div id="film-tab-content"></div>
      </div>`;

    const tabContent = root.querySelector('#film-tab-content');
    const renderTab = (tab) => {
      root.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
      if (tab === 'cast') {
        tabContent.innerHTML = cast.length
          ? `<div class="cast-grid">${cast.map(p => castCard(p)).join('')}</div>`
          : `<div class="empty"><p>Нет данных об актёрах</p></div>`;
        tabContent.querySelectorAll('.cast-card').forEach(c => {
          c.onclick = () => Router.go('person', { id: parseInt(c.dataset.id) });
        });
      } else if (tab === 'reviews') {
        tabContent.innerHTML = reviewsSection(film, reviews);
        root.querySelector('#review-submit')?.addEventListener('click', () => submitReview(film.film_id, tabContent, film, reviews, renderTab));
      } else if (tab === 'awards') {
        tabContent.innerHTML = awardsSection(awards);
      }
    };

    root.querySelectorAll('.tab').forEach(t => {
      t.onclick = () => renderTab(t.dataset.tab);
    });
    renderTab('cast');
  },

  // ── Persons ────────────────────────────────────────────────────────────────
  async persons(params, root) {
    const state = { search: '', role: '' };

    const draw = async () => {
      let data;
      try { data = await API.persons(state); } catch(e) {
        root.innerHTML = `<div class="container page"><p style="color:var(--red)">${esc(e.message)}</p></div>`;
        return;
      }
      root.innerHTML = `
        <div class="container page">
          <div class="search-bar">
            <div class="search-wrap">
              <span class="search-icon">🔍</span>
              <input id="p-search" type="text" placeholder="Поиск персон…" value="${esc(state.search)}" />
            </div>
            <select id="p-role" class="sort-select">
              <option value="">Все роли</option>
              ${['director','actor','producer','writer','composer','critic'].map(r =>
                `<option value="${r}" ${state.role===r?'selected':''}>${roleLabel(r)}</option>`
              ).join('')}
            </select>
          </div>
          <div class="section-head"><h2>Персоны <span style="font-size:14px;color:var(--text-muted);font-weight:400">${data.length}</span></h2></div>
          <div class="persons-grid">
            ${data.length === 0
              ? `<div class="empty" style="grid-column:1/-1"><div class="empty-icon">🎭</div><p>Ничего не найдено</p></div>`
              : data.map(p => personCard(p)).join('')
            }
          </div>
        </div>`;
      root.querySelectorAll('.person-card').forEach(c => {
        c.onclick = () => Router.go('person', { id: parseInt(c.dataset.id) });
      });
      let st;
      root.querySelector('#p-search').oninput = e => {
        clearTimeout(st); st = setTimeout(() => { state.search = e.target.value; draw(); }, 400);
      };
      root.querySelector('#p-role').onchange = e => { state.role = e.target.value; draw(); };
    };

    draw();
  },

  // ── Person detail ──────────────────────────────────────────────────────────
  async person(params, root) {
    let data;
    try { data = await API.person(params.id); } catch(e) {
      root.innerHTML = `<div class="container page"><p style="color:var(--red)">${esc(e.message)}</p></div>`;
      return;
    }
    const { person: p, roles, films } = data;
    const initials = [p.first_name, p.last_name].filter(Boolean).map(s => s[0]).join('').toUpperCase();
    const color = avatarColor(p.person_id);

    root.innerHTML = `
      <div class="container page">
        <div style="margin-bottom:16px">
          <span style="color:var(--text-muted);font-size:13px;cursor:pointer" onclick="Router.go('persons')">← Все персоны</span>
        </div>
        <div class="person-hero">
          <div class="person-avatar-xl" style="background:${color}22;color:${color}">${esc(initials)}</div>
          <div class="person-info">
            <h1>${esc(p.first_name)} ${esc(p.last_name || '')} ${p.middle_name ? esc(p.middle_name) : ''}</h1>
            <div class="person-meta-row">
              ${p.birth_date ? `<span class="film-meta-tag">📅 ${esc(fmt(p.birth_date))}</span>` : ''}
              ${p.country_name ? `<span class="film-meta-tag">🌍 ${esc(p.country_name)}</span>` : ''}
              ${p.birth_place  ? `<span class="film-meta-tag">📍 ${esc(p.birth_place)}</span>` : ''}
            </div>
            <div class="person-role-tags">
              ${roles.map(r => `<span class="role-tag">${esc(roleLabel(r))}</span>`).join('')}
            </div>
            ${p.biography ? `<p class="film-desc">${esc(p.biography)}</p>` : ''}
          </div>
        </div>

        <h2 style="margin-bottom:20px">Фильмография (${films.length})</h2>
        <div class="films-grid">
          ${films.map(f => filmCard(f)).join('')}
        </div>
      </div>`;

    root.querySelectorAll('.film-card').forEach(c => {
      c.onclick = () => Router.go('film', { id: parseInt(c.dataset.id) });
    });
  },

  // ── Festivals ──────────────────────────────────────────────────────────────
  async festivals(params, root) {
    let data;
    try { data = await API.festivals(); } catch(e) {
      root.innerHTML = `<div class="container page"><p style="color:var(--red)">${esc(e.message)}</p></div>`;
      return;
    }
    root.innerHTML = `
      <div class="container page">
        <div class="section-head"><h2>Фестивали</h2></div>
        <div class="festivals-grid">
          ${data.map(f => `
            <div class="festival-card">
              <div class="festival-name">🏆 ${esc(f.name)}</div>
              <div class="festival-prestige">
                ${f.prestige_rating ? `${parseFloat(f.prestige_rating).toFixed(1)}` : '—'}
                <span style="font-size:13px;color:var(--text-muted);font-weight:400">престиж</span>
              </div>
              <div class="festival-meta">
                ${f.country_name ? `<span>🌍 ${esc(f.country_name)}</span>` : ''}
                ${f.founded_year ? `<span>📅 с ${f.founded_year} г.</span>` : ''}
                <span>🏅 ${f.awards_count} наград</span>
              </div>
              ${f.description ? `<p class="festival-desc">${esc(f.description)}</p>` : ''}
            </div>`).join('')}
        </div>
      </div>`;
  },

  // ── Profile ────────────────────────────────────────────────────────────────
  async profile(params, root) {
    if (!Auth.user) {
      root.innerHTML = `
        <div class="container page">
          <div class="empty">
            <div class="empty-icon">🔑</div>
            <p>Войдите в аккаунт, чтобы увидеть профиль</p>
            <button class="btn btn-gold" style="margin-top:16px" onclick="AuthModal.open('login')">Войти</button>
          </div>
        </div>`;
      return;
    }
    const { user, roles, canAdmin } = Auth;
    const initials = [user.first_name, user.last_name].filter(Boolean).map(s => s[0]).join('').toUpperCase();
    const color = avatarColor(user.user_id);

    let myReviews = [];
    try { myReviews = await API.myReviews(); } catch {}

    root.innerHTML = `
      <div class="container page">
        <div class="profile-header">
          <div class="profile-avatar" style="background:${color}22;color:${color}">${esc(initials)}</div>
          <div>
            <div class="profile-name">${esc(user.first_name)} ${esc(user.last_name || '')}</div>
            <div class="profile-email">${esc(user.email)}</div>
            <div class="profile-role-badges">
              ${roles.map(r => `<span class="role-badge rb-${r}">${esc(r)}</span>`).join('')}
            </div>
            ${canAdmin ? `<a href="/admin" class="btn btn-sm" style="margin-top:10px;background:var(--gold-dim);color:var(--gold);border:1px solid rgba(232,180,0,.25)">⚙️ Панель управления</a>` : ''}
          </div>
        </div>

        <div class="divider"></div>
        <div class="section-head"><h2>Мои рецензии (${myReviews.length})</h2></div>
        <div class="profile-reviews">
          ${myReviews.length === 0
            ? `<div class="empty"><p>Вы ещё не написали ни одной рецензии</p></div>`
            : myReviews.map(r => `
              <div class="profile-review-card">
                <div class="prc-rating" style="color:${ratingColor(r.film_rating)}">${r.film_rating || '—'}</div>
                <div style="flex:1">
                  <div class="prc-film" data-fid="${r.film_id}">${esc(r.title)}</div>
                  <div class="prc-text">${esc(r.review_text)}</div>
                  <div class="prc-meta">${fmt(r.created_at)}</div>
                </div>
              </div>`).join('')
          }
        </div>
      </div>`;

    root.querySelectorAll('.prc-film').forEach(el => {
      el.onclick = () => Router.go('film', { id: parseInt(el.dataset.fid) });
    });
  },
};

// ── Component helpers ─────────────────────────────────────────────────────────

function filmCard(f) {
  const rating = parseFloat(f.average_rating) || 0;
  const year   = fmtYear(f.created_date);
  const ps     = posterStyle(f.film_id, f.title);
  return `
    <div class="film-card" data-id="${f.film_id}">
      <div class="film-poster" style="${ps}">
        <div class="film-poster-initial">${esc(f.title[0])}</div>
        ${f.age_restriction ? `<div class="film-age-badge">${esc(f.age_restriction)}</div>` : ''}
        ${rating > 0 ? `<div class="film-rating-badge ${ratingClass(rating)}">${rating.toFixed(1)}</div>` : ''}
      </div>
      <div class="film-card-body">
        <div class="film-card-title">${esc(f.title)}</div>
        <div class="film-card-meta">${year || ''}${f.director ? ` · ${esc(f.director.trim())}` : ''}</div>
        ${f.genres ? `<div class="film-card-genres">${esc(f.genres)}</div>` : ''}
      </div>
    </div>`;
}

function castCard(p) {
  const color    = avatarColor(p.person_id);
  const initials = [p.first_name, p.last_name].filter(Boolean).map(s => s[0]).join('').toUpperCase();
  return `
    <div class="cast-card" data-id="${p.person_id}">
      <div class="cast-avatar" style="background:${color}22;color:${color}">${esc(initials)}</div>
      <div class="cast-name">${esc(p.first_name)} ${esc(p.last_name || '')}</div>
      <div class="cast-role">${esc(roleLabel(p.role))}</div>
    </div>`;
}

function personCard(p) {
  const color    = avatarColor(p.person_id);
  const initials = [p.first_name, p.last_name].filter(Boolean).map(s => s[0]).join('').toUpperCase();
  return `
    <div class="person-card" data-id="${p.person_id}">
      <div class="person-avatar-lg" style="background:${color}22;color:${color}">${esc(initials)}</div>
      <div class="person-name">${esc(p.first_name)} ${esc(p.last_name || '')}</div>
      <div class="person-roles">${esc(p.roles || '')}</div>
      <div class="person-films">${p.film_count || 0} фильмов</div>
    </div>`;
}

function reviewsSection(film, reviews) {
  const formHtml = Auth.user
    ? `<div class="review-form-wrap">
        <h3>Написать рецензию</h3>
        <textarea id="review-text" placeholder="Поделитесь впечатлениями о фильме…"></textarea>
        <div class="form-row">
          <select class="rating-select" id="review-rating">
            <option value="">— оценка —</option>
            ${[10,9,8,7,6,5,4,3,2,1].map(n => `<option value="${n}">${n} / 10</option>`).join('')}
          </select>
          <button class="btn btn-gold btn-sm" id="review-submit">Отправить</button>
          <span id="review-err" style="color:var(--red);font-size:13px"></span>
        </div>
      </div>`
    : `<div class="review-login-hint">
        <span style="cursor:pointer;color:var(--blue)" onclick="AuthModal.open('login')">Войдите</span>,
        чтобы оставить рецензию
      </div>`;

  const list = reviews.length
    ? reviews.map(r => {
        const init = [r.first_name, r.last_name].filter(Boolean).map(s => s[0]).join('').toUpperCase();
        const col  = avatarColor(r.user_id);
        return `
          <div class="review-card">
            <div class="review-header">
              <div class="cast-avatar" style="width:36px;height:36px;font-size:14px;background:${col}22;color:${col}">${esc(init)}</div>
              <div>
                <div class="review-author">${esc(r.first_name)} ${esc(r.last_name || '')}</div>
                <div class="review-date">${fmt(r.created_at)}</div>
              </div>
              ${r.film_rating ? `<div class="review-rating ${ratingClass(r.film_rating)}" style="color:${ratingColor(r.film_rating)}">${r.film_rating}/10</div>` : ''}
            </div>
            <div class="review-text">${esc(r.review_text)}</div>
          </div>`;
      }).join('')
    : `<div class="empty"><p>Рецензий пока нет. Будьте первым!</p></div>`;

  return `${formHtml}<div class="reviews-list">${list}</div>`;
}

async function submitReview(filmId, container, film, reviews, renderTab) {
  const text   = container.querySelector('#review-text')?.value?.trim();
  const rating = container.querySelector('#review-rating')?.value;
  const errEl  = container.querySelector('#review-err');
  const btn    = container.querySelector('#review-submit');

  if (!text) { if (errEl) errEl.textContent = 'Введите текст рецензии'; return; }
  btn.disabled = true; btn.textContent = '…';

  try {
    const created = await API.createReview({
      film_id:     filmId,
      review_text: text,
      film_rating: rating ? parseInt(rating) : null,
    });
    // Добавляем новую рецензию в список
    const newRev = {
      ...created,
      first_name: Auth.user.first_name,
      last_name:  Auth.user.last_name,
      user_id:    Auth.user.user_id,
    };
    reviews.unshift(newRev);
    renderTab('reviews');
    toast('success', 'Рецензия опубликована');
  } catch(e) {
    btn.disabled = false; btn.textContent = 'Отправить';
    if (errEl) errEl.textContent = e.message;
  }
}

function awardsSection(awards) {
  return `<div class="awards-list">
    ${awards.map(a => `
      <div class="award-item">
        <div class="award-icon">${a.status === 'winner' ? '🥇' : '🏅'}</div>
        <div class="award-info">
          <div class="award-name">${esc(a.name)}</div>
          <div class="award-meta">${esc(a.festival_name)} · ${a.year}${a.category ? ` · ${esc(a.category)}` : ''}</div>
        </div>
        <div class="award-status ${a.status === 'winner' ? 'status-winner' : 'status-nominee'}">
          ${a.status === 'winner' ? 'Победитель' : 'Номинант'}
        </div>
      </div>`).join('')}
  </div>`;
}

// ── Auth modal wiring ─────────────────────────────────────────────────────────
document.getElementById('auth-modal-close').onclick = () => AuthModal.close();
document.getElementById('auth-modal').addEventListener('click', e => {
  if (e.target === e.currentTarget) AuthModal.close();
});
document.querySelectorAll('.auth-tab').forEach(t => {
  t.onclick = () => AuthModal.switchTab(t.dataset.tab);
});
document.getElementById('switch-to-register').onclick = () => AuthModal.switchTab('register');
document.getElementById('switch-to-login').onclick    = () => AuthModal.switchTab('login');

async function doLogin() {
  const email = document.getElementById('login-email').value.trim();
  const pass  = document.getElementById('login-password').value;
  const errEl = document.getElementById('login-error');
  errEl.classList.add('hidden'); errEl.textContent = '';
  const btn = document.getElementById('login-submit');
  btn.disabled = true; btn.textContent = 'Вход…';
  try {
    await Auth.doLogin(email, pass);
    AuthModal.close();
    renderNav();
    toast('success', `Добро пожаловать, ${Auth.user.first_name}!`);
    Router.go(Router.page, Router.params);
  } catch(e) {
    errEl.textContent = e.message; errEl.classList.remove('hidden');
  } finally { btn.disabled = false; btn.textContent = 'Войти'; }
}

async function doRegister() {
  const fn    = document.getElementById('reg-firstname').value.trim();
  const ln    = document.getElementById('reg-lastname').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const pass  = document.getElementById('reg-password').value;
  const errEl = document.getElementById('reg-error');
  errEl.classList.add('hidden'); errEl.textContent = '';
  if (!fn) { errEl.textContent = 'Введите имя'; errEl.classList.remove('hidden'); return; }
  if (pass.length < 6) { errEl.textContent = 'Пароль минимум 6 символов'; errEl.classList.remove('hidden'); return; }
  const btn = document.getElementById('reg-submit');
  btn.disabled = true; btn.textContent = 'Создание…';
  try {
    await Auth.doRegister({ first_name: fn, last_name: ln, email, password: pass });
    AuthModal.close();
    renderNav();
    toast('success', 'Аккаунт создан!', `Добро пожаловать, ${fn}!`);
    Router.go(Router.page, Router.params);
  } catch(e) {
    errEl.textContent = e.message; errEl.classList.remove('hidden');
  } finally { btn.disabled = false; btn.textContent = 'Создать аккаунт'; }
}

document.getElementById('login-submit').onclick = doLogin;
document.getElementById('reg-submit').onclick   = doRegister;
document.getElementById('login-password').addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });

// Close dropdowns on outside click
document.addEventListener('click', e => {
  if (!e.target.closest('#user-menu'))
    document.getElementById('user-dropdown')?.classList.add('hidden');
});

// ── Init ──────────────────────────────────────────────────────────────────────
(async () => {
  Auth.init();
  await Auth.refresh();
  renderNav();

  // Check if redirected from admin with need_login
  if (location.search.includes('need_login=1') && !Auth.user) {
    AuthModal.open('login');
  }

  // Default page
  Router.go('films');
})();
