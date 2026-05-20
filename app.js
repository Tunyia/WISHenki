// Сессия: JWT и профиль с бэкенда (/api/auth).
const SESSION_KEY = 'wishenki_session';

/** Группы для регистрации (как в фильтре рейтинга). */
const AVAILABLE_GROUPS = ['ШЦТ-111', 'ШЦТ-112', 'ГЛЭК-111'];

// Пустая строка — запросы на тот же хост (Docker + nginx проксирует /api).
// Порт 5500 — локальный python -m http.server, API отдельно на :8000.
const API_BASE = window.location.port === '5500' ? 'http://127.0.0.1:8000' : '';

/** Картинки мероприятия: с API (поле images), раздаются с бэкенда /photos/ или полный URL. */
function resolveActivityPhotoUrl(raw) {
    const s = String(raw || '').trim();
    if (!s) return '';
    if (/^https?:\/\//i.test(s)) return s;
    const path = s.startsWith('/') ? s : `/photos/${s.replace(/^\/?photos\/?/i, '')}`;
    return `${API_BASE}${path}`;
}

let modalActivityId = null;
/** 'upcoming' | 'past' — откуда открыта модалка */
let modalActivityKind = 'upcoming';

function getSession() {
    try {
        const raw = localStorage.getItem(SESSION_KEY);
        if (!raw) return null;
        const data = JSON.parse(raw);
        if (!data || !data.accessToken) return null;
        return data;
    } catch {
        return null;
    }
}

function setSession(session) {
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

function clearSession() {
    localStorage.removeItem(SESSION_KEY);
}

/** ID студента в БД; без входа — null. */
function getCurrentUserId() {
    const s = getSession();
    if (!s || s.studentId == null || s.studentId === '') return null;
    const n = Number(s.studentId);
    return Number.isFinite(n) ? n : null;
}

function fullNameFromSession(s) {
    if (!s) return '';
    return [s.lastName, s.firstName, s.middleName].filter(Boolean).join(' ').trim();
}

/** Разбор ФИО из строки от API (фамилия имя отчество). */
function splitFullName(fullName) {
    const parts = (fullName || '').trim().split(/\s+/).filter(Boolean);
    return {
        lastName: parts[0] || '',
        firstName: parts[1] || '',
        middleName: parts.slice(2).join(' ') || '',
    };
}

function sessionFromTokenPayload(data) {
    const fio = splitFullName(data.full_name);
    return {
        accessToken: data.access_token,
        email: data.email,
        studentId: data.student_id,
        lastName: fio.lastName,
        firstName: fio.firstName,
        middleName: fio.middleName,
        group: data.study_group,
        cherries: data.available_points,
    };
}

function sessionFromMePayload(data, prev) {
    const fio = splitFullName(data.full_name);
    return {
        accessToken: prev.accessToken,
        email: data.email,
        studentId: data.student_id,
        lastName: fio.lastName,
        firstName: fio.firstName,
        middleName: fio.middleName,
        group: data.study_group,
        cherries: data.available_points,
    };
}

function setAuthError(message) {
    const el = document.getElementById('auth-form-error');
    if (!el) return;
    if (!message) {
        el.hidden = true;
        el.textContent = '';
        return;
    }
    el.hidden = false;
    el.textContent = message;
}

function showAuthView(mode) {
    const loginForm = document.getElementById('form-login');
    const regForm = document.getElementById('form-register');
    const title = document.getElementById('auth-modal-title');
    if (!loginForm || !regForm || !title) return;
    setAuthError('');
    if (mode === 'register') {
        loginForm.hidden = true;
        regForm.hidden = false;
        title.textContent = 'Регистрация';
    } else {
        loginForm.hidden = false;
        regForm.hidden = true;
        title.textContent = 'Вход в аккаунт';
    }
}

function populateRegisterGroupSelect() {
    const sel = document.getElementById('reg-group');
    if (!sel) return;
    sel.innerHTML =
        '<option value="" disabled selected>Выберите группу</option>' +
        AVAILABLE_GROUPS.map((g) => `<option value="${g}">${g}</option>`).join('');
}

function openAuthModal(mode) {
    const modal = document.getElementById('auth-modal');
    if (!modal) return;
    showAuthView(mode === 'register' ? 'register' : 'login');
    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
}

function closeAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (!modal) return;
    const content = modal.querySelector('.modal-content');
    if (content) content.classList.add('closing');
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    setTimeout(() => {
        if (content) content.classList.remove('closing');
    }, 300);
}

function updateProfilePanelVisibility() {
    const guest = document.getElementById('profile-guest');
    const user = document.getElementById('profile-user');
    const loggedIn = !!getSession();
    if (guest) guest.hidden = loggedIn;
    if (user) user.hidden = !loggedIn;
}

async function refreshProfileFromServerOrSession() {
    updateProfilePanelVisibility();
    const session = getSession();
    if (!session) {
        return;
    }

    const fallback = {
        fullName: fullNameFromSession(session) || 'Студент',
        group: session.group || '—',
        role: 'Студент',
        cherries: session.cherries != null ? session.cherries : 0,
    };
    renderProfile(fallback);

    try {
        const me = await apiFetch('/api/auth/me', { auth: true });
        const next = sessionFromMePayload(me, session);
        setSession(next);
        renderProfile({
            fullName: me.full_name,
            group: me.study_group,
            role: 'Студент',
            cherries: me.available_points,
        });
    } catch (e) {
        console.warn('Не удалось обновить профиль по /api/auth/me (токен истёк или бэкенд недоступен).', e);
        const sid = getCurrentUserId();
        if (sid == null) return;
        try {
            const me = await apiFetch(`/api/students/${sid}`);
            renderProfile({
                fullName: me.full_name,
                group: me.study_group,
                role: 'Студент',
                cherries: me.available_points,
            });
            session.cherries = me.available_points;
            setSession(session);
        } catch (e2) {
            console.warn('Не удалось подтянуть профиль студента.', e2);
        }
    }
}

async function apiFetch(path, options = {}) {
    const method = options.method || 'GET';
    const body = options.body !== undefined ? options.body : null;
    const auth = !!options.auth;

    const headers = { Accept: 'application/json' };
    if (body != null) headers['Content-Type'] = 'application/json';
    if (auth) {
        const s = getSession();
        if (s?.accessToken) headers['Authorization'] = `Bearer ${s.accessToken}`;
    }

    const res = await fetch(`${API_BASE}${path}`, {
        method,
        headers,
        body: body != null ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
        const text = await res.text().catch(() => '');
        let msg = `HTTP ${res.status}`;
        if (text) {
            try {
                const j = JSON.parse(text);
                if (typeof j.detail === 'string') msg = j.detail;
                else if (Array.isArray(j.detail))
                    msg = j.detail.map((x) => (x.msg ? x.msg : JSON.stringify(x))).join('; ');
                else msg = text.slice(0, 200);
            } catch {
                msg = text.slice(0, 200);
            }
        }
        throw new Error(msg);
    }

    if (res.status === 204) return null;
    return res.json();
}

// Данные приходят с API; этот массив нужен как общий источник для рендера/фильтра
const mockLeaderboardData = [];

let upcomingActivitiesData = [];
let pastActivitiesData = [];

// Функция для обновления верхней личной карточки
function renderProfile(data) {
    document.getElementById('user-name').textContent = data.fullName;
    document.getElementById('user-group').textContent = data.group;
    document.getElementById('user-role').textContent = data.role;
    document.getElementById('user-balance').textContent = data.cherries;
}

// Функция рендера таблицы лидерборда
function renderLeaderboard(data) {
    const tbody = document.getElementById('leaderboard-body');
    tbody.innerHTML = ''; // Очищаем таблицу перед отрисовкой

    // Если ничего не найдено
    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 20px;">Ничего не найдено</td></tr>';
        return;
    }

    // Перебираем массив студентов и создаем HTML-строки
    data.forEach((student, index) => {
        // Выдаем красивые классы для топ-3
        let rankClass = '';
        if (index === 0) rankClass = 'rank-1';
        if (index === 1) rankClass = 'rank-2';
        if (index === 2) rankClass = 'rank-3';

        // --- ЛОГИКА ВЫДЕЛЕНИЯ СЕБЯ ---
        const meId = getCurrentUserId();
        const isCurrentUser = meId != null && student.id === meId;
        // Если это "я", добавляем класс 'current-user-row' (стили для него мы писали ранее в CSS)
        const rowClass = isCurrentUser ? 'current-user-row' : '';

        const tr = document.createElement('tr');
        tr.className = rowClass; // Применяем класс к строке

        tr.innerHTML = `
            <td class="${rankClass}">#${index + 1}</td>
            <td>
                <div class="student-cell">
                    <div class="student-avatar-mini">${student.fullName.charAt(0)}</div>
                    ${student.fullName}
                </div>
            </td>
            <td>${student.group}</td>
            
            <td style="font-weight: 600; color: var(--cherry-red);">
                <div style="display: flex; align-items: center; gap: 6px;">
                    ${student.cherries}
                    <img src="icons/wishenka.svg" alt="вишенки" style="width: 20px; height: 20px; flex-shrink: 0; display: block;">
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Функция фильтрации (работает "на лету" при вводе)
function filterLeaderboard() {
    const searchText = document.getElementById('search-input').value.toLowerCase();
    const filterGroup = document.getElementById('group-filter').value;

    const filteredData = mockLeaderboardData.filter(student => {
        // Ищем совпадения в ФИО ИЛИ в названии группы
        const matchText = student.fullName.toLowerCase().includes(searchText) || 
                          student.group.toLowerCase().includes(searchText);
        
        // Проверяем фильтр по группе (если пусто - показываем все)
        const matchGroup = filterGroup === "" || student.group === filterGroup;
        
        return matchText && matchGroup;
    });

    // Сортируем по убыванию вишенок (на случай, если данные придут вразнобой)
    filteredData.sort((a, b) => b.cherries - a.cherries);

    renderLeaderboard(filteredData);
}

// Вспомогательная функция для подбора цвета тега
function getTagClass(tagName) {
    const name = tagName.toLowerCase();
    if (name.includes('it') || name.includes('программирование')) return 'tag-it';
    if (name.includes('наука') || name.includes('лекция')) return 'tag-science';
    if (name.includes('социальное') || name.includes('волонтер')) return 'tag-social';
    return 'tag-default';
}

function collectActivityTags(allActivities) {
    const existing = new Set();
    const tags = [];
    allActivities.forEach((a) => {
        (a.categories || []).forEach(t => {
            const key = String(t).trim();
            if (!key) return;
            if (existing.has(key)) return;
            existing.add(key);
            tags.push(key);
        });
    });
    tags.sort((a, b) => a.localeCompare(b, 'ru'));
    return tags;
}

function fillTagSelect(selectId, tags) {
    const select = document.getElementById(selectId);
    if (!select) return;
    select.innerHTML =
        `<option value="">Все теги</option>` +
        tags.map((t) => `<option value="${t}">${t}</option>`).join('');
}

function renderActivityTagOptions() {
    const all = [...upcomingActivitiesData, ...pastActivitiesData];
    const tags = collectActivityTags(all);
    fillTagSelect('tag-filter', tags);
    fillTagSelect('past-tag-filter', tags);
}

function filterActivityList(data, searchId, tagId) {
    const searchText = (document.getElementById(searchId)?.value || '').toLowerCase();
    const filterTag = document.getElementById(tagId)?.value || '';
    return data.filter((a) => {
        const title = (a.title || '').toLowerCase();
        const organizer = (a.organizer || '').toLowerCase();
        const desc = (a.description || '').toLowerCase();
        const matchText =
            !searchText ||
            title.includes(searchText) ||
            organizer.includes(searchText) ||
            desc.includes(searchText);
        const cats = a.categories || [];
        const matchTag = !filterTag || cats.includes(filterTag);
        return matchText && matchTag;
    });
}

function filterActivities() {
    renderActivities(filterActivityList(upcomingActivitiesData, 'activity-search', 'tag-filter'));
}

function filterPastActivities() {
    renderPastActivities(filterActivityList(pastActivitiesData, 'past-activity-search', 'past-tag-filter'));
}

let currentImages = [];
let currentImgIndex = 0;
function updateGallery() {
    const wrapper = document.getElementById('images-wrapper');
    const prevBtn = document.getElementById('prev-img');
    const nextBtn = document.getElementById('next-img');

    if (!wrapper || currentImages.length === 0) return;

    const offset = currentImgIndex * 100;
    wrapper.style.transform = `translateX(-${offset}%)`;

    const multi = currentImages.length > 1;
    prevBtn.classList.toggle('visible', multi && currentImgIndex > 0);
    nextBtn.classList.toggle('visible', multi && currentImgIndex < currentImages.length - 1);
}

// Функции перелистывания
document.getElementById('prev-img').onclick = () => {
    if (currentImgIndex > 0) {
        currentImgIndex--;
        updateGallery();
    }
};
document.getElementById('next-img').onclick = () => {
    if (currentImgIndex < currentImages.length - 1) {
        currentImgIndex++;
        updateGallery();
    }
};

function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text == null ? '' : String(text);
    return d.innerHTML;
}

function initialsFromFullName(fullName) {
    const p = (fullName || '').trim().split(/\s+/).filter(Boolean);
    if (p.length === 0) return '?';
    if (p.length === 1) return p[0].slice(0, 2).toUpperCase();
    return (p[0][0] + p[1][0]).toUpperCase();
}

function renderParticipantsLoading() {
    const el = document.getElementById('participants-list');
    const badge = document.getElementById('modal-participants-count');
    if (badge) badge.textContent = '…';
    if (el) el.innerHTML = '<p class="participants-loading">Загрузка списка…</p>';
}

function renderParticipantsList(participants, kind) {
    const el = document.getElementById('participants-list');
    const badge = document.getElementById('modal-participants-count');
    const heading = document.getElementById('participants-heading');
    if (heading) {
        heading.textContent = kind === 'past' ? 'Посетили' : 'Уже записались';
    }
    if (!el) return;
    const list = Array.isArray(participants) ? participants : [];
    const n = list.length;
    if (badge) badge.textContent = String(n);
    const meId = getCurrentUserId();

    if (n === 0) {
        el.innerHTML =
            kind === 'past'
                ? '<p class="participants-empty">Пока нет отмеченных посещений.</p>'
                : '<p class="participants-empty">Пока никто не записался. Зайдите в аккаунт и запишитесь первым.</p>';
        return;
    }

    const rows = list
        .map((p, i) => {
            const isMe = meId != null && p.student_id === meId;
            const initials = escapeHtml(initialsFromFullName(p.full_name));
            const youCell = isMe
                ? '<span class="pm-you-badge">Вы</span>'
                : '';
            return `<tr class="${isMe ? 'pm-row-me' : ''}">
                <td class="pm-td-rank">${i + 1}</td>
                <td>
                    <div class="student-cell pm-student-cell">
                        <div class="student-avatar-mini">${initials}</div>
                        <span class="pm-student-name">${escapeHtml(p.full_name)}</span>
                    </div>
                </td>
                <td class="pm-td-group">${escapeHtml(p.study_group)}</td>
                <td class="pm-td-you">${youCell}</td>
            </tr>`;
        })
        .join('');

    el.innerHTML = `
        <table class="participants-modal-table">
            <colgroup>
                <col class="pm-col-rank" />
                <col class="pm-col-student" />
                <col class="pm-col-group" />
                <col class="pm-col-mark" />
            </colgroup>
            <thead>
                <tr>
                    <th class="pm-th-rank" scope="col">#</th>
                    <th scope="col">Студент</th>
                    <th class="pm-th-group" scope="col">Группа</th>
                    <th class="pm-th-mark" scope="col"></th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>`;
}

function syncEventRegisterButton() {
    const btn = document.getElementById('btn-event-register');
    const hint = document.getElementById('btn-register-hint');
    const footer = document.getElementById('modal-footer');
    const isPast = modalActivityKind === 'past';
    if (footer) footer.hidden = isPast;
    if (!btn) return;
    if (isPast) return;
    const logged = !!getSession()?.accessToken;
    btn.disabled = !logged;
    if (hint) hint.hidden = logged;
}

function closeModal() {
    modalActivityId = null;
    modalActivityKind = 'upcoming';
    const modal = document.getElementById('event-modal');
    const content = modal.querySelector('.modal-content');

    content.classList.add('closing');
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');

    setTimeout(() => {
        content.classList.remove('closing');
        document.body.style.overflow = '';
    }, 300);
}

function findActivityById(activityId) {
    return (
        upcomingActivitiesData.find((a) => a.id === activityId) ||
        pastActivitiesData.find((a) => a.id === activityId)
    );
}

async function openEventModal(activityId, kind) {
    const activity =
        kind === 'past'
            ? pastActivitiesData.find((a) => a.id === activityId)
            : upcomingActivitiesData.find((a) => a.id === activityId);
    if (!activity) return;

    modalActivityId = activityId;
    modalActivityKind = kind === 'past' ? 'past' : 'upcoming';

    const rawImages = Array.isArray(activity.images) ? activity.images.filter(Boolean) : [];
    currentImages = rawImages.map(resolveActivityPhotoUrl).filter(Boolean);
    currentImgIndex = 0;

    const track = document.getElementById('modal-gallery-track');
    const emptyEl = document.getElementById('modal-gallery-empty');
    const wrapper = document.getElementById('images-wrapper');

    if (currentImages.length === 0) {
        track.hidden = true;
        emptyEl.hidden = false;
    } else {
        emptyEl.hidden = true;
        track.hidden = false;
        wrapper.innerHTML = currentImages.map((url) => `<img src="${url}" alt="">`).join('');
        wrapper.style.transition = 'none';
        wrapper.style.transform = 'translateX(0)';
        setTimeout(() => {
            wrapper.style.transition = 'transform 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
        }, 50);
    }

    document.getElementById('modal-title').innerText = activity.title;
    document.getElementById('modal-desc-full').innerText = activity.description;
    document.getElementById('modal-reward').innerText = activity.base_reward;
    document.getElementById('modal-organizer').innerText = activity.organizer;
    document.getElementById('modal-date').innerText = activity.event_date;

    const tagsContainer = document.getElementById('modal-tags');
    tagsContainer.innerHTML = (activity.categories || [])
        .map((tag) => `<span class="activity-tag ${getTagClass(tag)}">${tag}</span>`)
        .join('');

    if (currentImages.length > 0) updateGallery();
    else {
        document.getElementById('prev-img').classList.remove('visible');
        document.getElementById('next-img').classList.remove('visible');
    }

    renderParticipantsLoading();

    document.getElementById('event-modal').classList.add('active');
    document.getElementById('event-modal').setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';

    try {
        const path =
            modalActivityKind === 'past'
                ? `/api/activities/${activityId}/attendees`
                : `/api/activities/${activityId}/participants`;
        const participants = await apiFetch(path);
        renderParticipantsList(participants, modalActivityKind);
    } catch (e) {
        console.warn('Список участников не загрузился', e);
        renderParticipantsList([], modalActivityKind);
    }

    syncEventRegisterButton();
}

// Закрытие модалки мероприятия
const eventCloseBtn = document.querySelector('#event-modal .close-modal');
if (eventCloseBtn) eventCloseBtn.onclick = closeModal;
document.getElementById('event-modal').onclick = (e) => {
    if (e.target.id === 'event-modal') closeModal();
};

// Не забывай обновить renderActivities, чтобы при клике вызывалась эта функция:
// card.onclick = () => openEventModal(activity.id);

function renderActivities(activities) {
    const grid = document.getElementById('activities-grid');
    grid.innerHTML = '';

    activities.forEach(activity => {
        const card = document.createElement('div');
        card.className = 'activity-card';
        
        const tagsHtml = activity.categories
            .map(tag => `<span class="activity-tag ${getTagClass(tag)}">${tag}</span>`)
            .join('');

        card.innerHTML = `
            <div>
                <div class="activity-tags">${tagsHtml}</div>
                <div class="activity-title">${activity.title}</div>
                <div class="activity-organizer">
                    Организатор: ${activity.organizer}
                </div>
                <div class="activity-description">${activity.description}</div>
            </div>
            <div class="activity-footer">
                <div class="activity-reward">
                    ${activity.base_reward} <img src="icons/wishenka.svg" style="width: 16px;">
                </div>
                <div class="activity-date">${activity.event_date}</div>
            </div>
        `;
        grid.appendChild(card);
        card.onclick = () => openEventModal(activity.id, 'upcoming');
    });
}

function renderPastActivities(activities) {
    const grid = document.getElementById('past-activities-grid');
    if (!grid) return;
    grid.innerHTML = '';
    activities.forEach((activity) => {
        const card = document.createElement('div');
        card.className = 'activity-card activity-card--past';
        const tagsHtml = (activity.categories || [])
            .map((tag) => `<span class="activity-tag ${getTagClass(tag)}">${tag}</span>`)
            .join('');
        card.innerHTML = `
            <div>
                <div class="activity-tags">${tagsHtml}</div>
                <div class="activity-title">${escapeHtml(activity.title)}</div>
                <div class="activity-organizer">Организатор: ${escapeHtml(activity.organizer)}</div>
                <div class="activity-description">${escapeHtml(activity.description)}</div>
            </div>
            <div class="activity-footer">
                <div class="activity-reward">
                    ${activity.base_reward} <img src="icons/wishenka.svg" style="width: 16px;" alt="">
                </div>
                <div class="activity-date">${escapeHtml(activity.event_date)}</div>
            </div>
        `;
        card.onclick = () => openEventModal(activity.id, 'past');
        grid.appendChild(card);
    });
}

// ОСНОВНОЙ БЛОК: Запускаем всё, когда страница загрузилась
document.addEventListener('DOMContentLoaded', () => {
    updateProfilePanelVisibility();
    populateRegisterGroupSelect();

    (async () => {
        // 1) Лидерборд: всегда пытаемся взять реальный список студентов.
        // Если список недоступен (бэк не запущен) — только тогда падаем на моки.
        try {
            const students = await apiFetch('/api/students?skip=0&limit=500');
            const leaderboard = students
                .map(s => ({
                    id: s.id,
                    fullName: s.full_name,
                    group: s.study_group,
                    cherries: s.available_points,
                }))
                .sort((a, b) => b.cherries - a.cherries);

            mockLeaderboardData.length = 0;
            mockLeaderboardData.push(...leaderboard);
        } catch (e) {
            console.warn('Не удалось загрузить список студентов с API, используем моки.', e);
        }

        mockLeaderboardData.sort((a, b) => b.cherries - a.cherries);
        renderLeaderboard(mockLeaderboardData);

        // 1b) Мероприятия (предстоящие и прошедшие)
        try {
            const [upcoming, past] = await Promise.all([
                apiFetch('/api/activities?time=upcoming&limit=500'),
                apiFetch('/api/activities?time=past&limit=500'),
            ]);
            upcomingActivitiesData = upcoming;
            pastActivitiesData = past;
            renderActivityTagOptions();
            filterActivities();
            filterPastActivities();
        } catch (e) {
            console.warn('Не удалось загрузить мероприятия с API.', e);
            upcomingActivitiesData = [];
            pastActivitiesData = [];
            renderActivityTagOptions();
            renderActivities([]);
            renderPastActivities([]);
        }

        // 2) Профиль: только для вошедшего пользователя (данные сессии + опционально API по studentId).
        await refreshProfileFromServerOrSession();
    })();

    document.getElementById('btn-open-auth')?.addEventListener('click', () => openAuthModal('login'));
    document.getElementById('btn-logout')?.addEventListener('click', () => {
        clearSession();
        closeModal();
        updateProfilePanelVisibility();
        filterLeaderboard();
    });

    document.getElementById('btn-event-register')?.addEventListener('click', async () => {
        if (!modalActivityId || !getSession()?.accessToken) return;
        try {
            await apiFetch(`/api/activities/${modalActivityId}/enroll`, {
                method: 'POST',
                auth: true,
            });
            const path =
                modalActivityKind === 'past'
                    ? `/api/activities/${modalActivityId}/attendees`
                    : `/api/activities/${modalActivityId}/participants`;
            const participants = await apiFetch(path);
            renderParticipantsList(participants, modalActivityKind);
        } catch (err) {
            alert(err.message || 'Не удалось записаться.');
        }
    });

    document.getElementById('close-auth-modal')?.addEventListener('click', closeAuthModal);
    document.getElementById('auth-modal')?.addEventListener('click', (e) => {
        if (e.target.id === 'auth-modal') closeAuthModal();
    });
    document.getElementById('link-to-register')?.addEventListener('click', () => showAuthView('register'));
    document.getElementById('link-to-login')?.addEventListener('click', () => showAuthView('login'));

    document.getElementById('form-login')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = (document.getElementById('login-email').value || '').trim().toLowerCase();
        const password = document.getElementById('login-password').value || '';
        if (!email || !password) {
            setAuthError('Введите почту и пароль.');
            return;
        }
        try {
            const data = await apiFetch('/api/auth/login', {
                method: 'POST',
                body: { email, password },
            });
            setSession(sessionFromTokenPayload(data));
            closeAuthModal();
            await refreshProfileFromServerOrSession();
            filterLeaderboard();
            syncEventRegisterButton();
            if (modalActivityId) {
                try {
                    const path =
                        modalActivityKind === 'past'
                            ? `/api/activities/${modalActivityId}/attendees`
                            : `/api/activities/${modalActivityId}/participants`;
                    const participants = await apiFetch(path);
                    renderParticipantsList(participants, modalActivityKind);
                } catch (_) {
                    /* ignore */
                }
            }
        } catch (err) {
            setAuthError(err.message || 'Не удалось войти.');
        }
    });

    document.getElementById('form-register')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = (document.getElementById('reg-email').value || '').trim().toLowerCase();
        const password = document.getElementById('reg-password').value || '';
        const password2 = document.getElementById('reg-password2').value || '';
        const study_group = document.getElementById('reg-group').value;
        const last_name = (document.getElementById('reg-last-name').value || '').trim();
        const first_name = (document.getElementById('reg-first-name').value || '').trim();
        const middle_name = (document.getElementById('reg-middle-name').value || '').trim();

        if (!email || !password || !study_group || !last_name || !first_name) {
            setAuthError('Заполните обязательные поля.');
            return;
        }
        if (password !== password2) {
            setAuthError('Пароли не совпадают.');
            return;
        }
        try {
            const body = {
                email,
                password,
                study_group,
                last_name,
                first_name,
            };
            if (middle_name) body.middle_name = middle_name;
            const data = await apiFetch('/api/auth/register', {
                method: 'POST',
                body,
            });
            setSession(sessionFromTokenPayload(data));
            closeAuthModal();
            try {
                const students = await apiFetch('/api/students?skip=0&limit=500');
                const leaderboard = students
                    .map((s) => ({
                        id: s.id,
                        fullName: s.full_name,
                        group: s.study_group,
                        cherries: s.available_points,
                    }))
                    .sort((a, b) => b.cherries - a.cherries);
                mockLeaderboardData.length = 0;
                mockLeaderboardData.push(...leaderboard);
                renderLeaderboard(mockLeaderboardData);
            } catch (_) {
                filterLeaderboard();
            }
            await refreshProfileFromServerOrSession();
            filterLeaderboard();
            syncEventRegisterButton();
            if (modalActivityId) {
                try {
                    const path =
                        modalActivityKind === 'past'
                            ? `/api/activities/${modalActivityId}/attendees`
                            : `/api/activities/${modalActivityId}/participants`;
                    const participants = await apiFetch(path);
                    renderParticipantsList(participants, modalActivityKind);
                } catch (_) {
                    /* ignore */
                }
            }
        } catch (err) {
            setAuthError(err.message || 'Не удалось зарегистрироваться.');
        }
    });

    // Фильтры таблицы
    document.getElementById('search-input').addEventListener('input', filterLeaderboard);
    document.getElementById('group-filter').addEventListener('change', filterLeaderboard);

    // Фильтры мероприятий (как у рейтинга)
    document.getElementById('activity-search')?.addEventListener('input', filterActivities);
    document.getElementById('tag-filter')?.addEventListener('change', filterActivities);
    document.getElementById('past-activity-search')?.addEventListener('input', filterPastActivities);
    document.getElementById('past-tag-filter')?.addEventListener('change', filterPastActivities);

    const pastToggleBtn = document.getElementById('btn-toggle-past-events');
    const pastPanel = document.getElementById('past-events-panel');
    const pastToggleBar = document.getElementById('past-events-toggle-bar');
    pastToggleBtn?.addEventListener('click', () => {
        const isOpen = pastPanel?.hasAttribute('hidden');
        if (isOpen) {
            pastPanel.removeAttribute('hidden');
            pastToggleBtn.setAttribute('aria-expanded', 'true');
            pastToggleBar?.classList.add('is-open');
        } else {
            pastPanel?.setAttribute('hidden', '');
            pastToggleBtn.setAttribute('aria-expanded', 'false');
            pastToggleBar?.classList.remove('is-open');
        }
    });
});
