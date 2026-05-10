// ID текущего залогиненного пользователя (Алексей Смирнов)
// В будущем этот ID будет приходить от FastAPI при авторизации
// Для демо: можно поменять на любой существующий student id из БД
const currentUserId = 1; 

const API_BASE = 'http://127.0.0.1:8000';

async function fetchJson(path) {
    const res = await fetch(`${API_BASE}${path}`, {
        headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) {
        const text = await res.text().catch(() => '');
        throw new Error(`HTTP ${res.status} ${res.statusText}${text ? `: ${text}` : ''}`);
    }
    return res.json();
}

// Данные приходят с API; этот массив нужен как общий источник для рендера/фильтра
const mockLeaderboardData = [];

// Имитация базы данных студентов
const mockStudents = [
    { id: 1, name: "Иванов Пётр", group: "ШЦТ-111", initials: "ИП" },
    { id: 2, name: "Анна Смирнова", group: "ШЦТ-111", initials: "АС" },
    { id: 3, name: "Михаил Зубенко", group: "ШЦТ-112", initials: "МЗ" },
    { id: 4, name: "Дарья Козлова", group: "ШЦТ-112", initials: "ДК" },
    { id: 5, name: "Артём Морозов", group: "ШЦТ-111", initials: "АМ" },
    { id: 6, name: "Елена Вишня", group: "ШЦТ-112", initials: "ЕВ" },
    { id: 7, name: "Игорь Север", group: "ШЦТ-111", initials: "ИС" },
    { id: 8, name: "Ольга Бузова", group: "ШЦТ-111", initials: "ОБ" },
    { id: 9, name: "Дмитрий Ларин", group: "ШЦТ-111", initials: "ДЛ" },
    { id: 10, name: "Никита Петров", group: "ШЦТ-112", initials: "НП" },
    { id: 11, name: "София Лебедева", group: "ШЦТ-112", initials: "СЛ" },
    { id: 12, name: "Павел Дуров", group: "ШЦТ-111", initials: "ПД" }
];

let activitiesData = [];

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
        // Проверяем, совпадает ли ID студента в строке с ID залогиненного пользователя
        const isCurrentUser = (student.id === currentUserId);
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

function renderActivityTagOptions(allActivities) {
    const select = document.getElementById('tag-filter');
    if (!select) return;

    const existing = new Set();
    const tags = [];
    allActivities.forEach(a => {
        (a.categories || []).forEach(t => {
            const key = String(t).trim();
            if (!key) return;
            if (existing.has(key)) return;
            existing.add(key);
            tags.push(key);
        });
    });
    tags.sort((a, b) => a.localeCompare(b, 'ru'));

    select.innerHTML = `<option value="">Все теги</option>` + tags.map(t => `<option value="${t}">${t}</option>`).join('');
}

function filterActivities() {
    const searchText = (document.getElementById('activity-search')?.value || '').toLowerCase();
    const filterTag = document.getElementById('tag-filter')?.value || '';

    const filtered = activitiesData.filter(a => {
        const title = (a.title || '').toLowerCase();
        const organizer = (a.organizer || '').toLowerCase();
        const desc = (a.description || '').toLowerCase();
        const matchText = !searchText || title.includes(searchText) || organizer.includes(searchText) || desc.includes(searchText);

        const cats = a.categories || [];
        const matchTag = !filterTag || cats.includes(filterTag);
        return matchText && matchTag;
    });

    renderActivities(filtered);
}

let currentImages = [];
let currentImgIndex = 0;
function updateGallery() {
    const wrapper = document.getElementById('images-wrapper');
    const prevBtn = document.getElementById('prev-img');
    const nextBtn = document.getElementById('next-img');

    if (!wrapper) return; // Защита от ошибок

    // ИСПРАВЛЕНО: используем .style.transform
    const offset = currentImgIndex * 100;
    wrapper.style.transform = `translateX(-${offset}%)`;

    // Видимость стрелок
    prevBtn.classList.toggle('visible', currentImgIndex > 0);
    nextBtn.classList.toggle('visible', currentImgIndex < currentImages.length - 1);
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

function generateParticipantsTable(students) {
    return students.map((student, index) => `
        <tr>
            <td>${index + 1}</td>
            <td>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div class="student-avatar-mini">${student.initials}</div>
                    <span style="font-weight: 500;">${student.name}</span>
                </div>
            </td>
            <td style="text-align: right; color: var(--text-muted);">${student.group}</td>
        </tr>
    `).join('');
}

function closeModal() {
    const modal = document.getElementById('event-modal');
    const content = modal.querySelector('.modal-content');
    
    // Запускаем анимацию вылета контента
    content.classList.add('closing');
    
    // Скрываем оверлей (сработает transition: opacity из CSS)
    modal.classList.remove('active');

    // Ждем завершения анимации и чистим классы
    setTimeout(() => {
        content.classList.remove('closing');
        document.body.style.overflow = ''; // Возвращаем скролл сайта
    }, 300); // 300мс должно совпадать с временем в CSS
}

function openEventModal(activityId) {
    const activity = activitiesData.find(a => a.id === activityId);
    if (!activity) return;

    currentImages = activity.images && activity.images.length > 0
        ? activity.images
        : ["photos/kot.png", "photos/kot2.png", "photos/nekot.png"];
    currentImgIndex = 0;

    // Генерируем все картинки сразу в ленту
    const wrapper = document.getElementById('images-wrapper');
    wrapper.innerHTML = currentImages.map(img => `<img src="${img}" alt="event">`).join('');
    
    // Сбрасываем положение ленты без анимации перед открытием
    wrapper.style.transition = 'none';
    wrapper.style.transform = 'translateX(0)';
    
    // Включаем анимацию обратно через мгновение
    setTimeout(() => {
        wrapper.style.transition = 'transform 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
    }, 50);

    // Заполняем данные
    document.getElementById('modal-title').innerText = activity.title;
    document.getElementById('modal-desc-full').innerText = activity.description;
    document.getElementById('modal-reward').innerText = activity.base_reward;
    document.getElementById('modal-organizer').innerText = activity.organizer;
    document.getElementById('modal-date').innerText = activity.event_date;
    
    // Рендерим теги
    const tagsContainer = document.getElementById('modal-tags');
    tagsContainer.innerHTML = activity.categories
        .map(tag => `<span class="activity-tag ${getTagClass(tag)}">${tag}</span>`)
        .join('');

    updateGallery();

    // Генерируем таблицу лидеров для мероприятия
    const participantsContainer = document.getElementById('participants-list');
    participantsContainer.innerHTML = `
        <div class="participants-scroll-area">
            <table class="participants-table">
                <thead>
                    <tr>
                        <th style="width: 30px;">№</th>
                        <th>Студент</th>
                        <th style="text-align: right; padding-right: 8px;">Группа</th>
                    </tr>
                </thead>
                <tbody>
                    ${generateParticipantsTable(mockStudents)}
                </tbody>
            </table>
        </div>
    `;

    // Показываем модалку
    document.getElementById('event-modal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

// Закрытие модалки
document.querySelector('.close-modal').onclick = closeModal;
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
        card.onclick = () => openEventModal(activity.id);
    });
}

// ОСНОВНОЙ БЛОК: Запускаем всё, когда страница загрузилась
document.addEventListener('DOMContentLoaded', () => {

    (async () => {
        // 1) Лидерборд: всегда пытаемся взять реальный список студентов.
        // Если список недоступен (бэк не запущен) — только тогда падаем на моки.
        try {
            const students = await fetchJson('/api/students?skip=0&limit=500');
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

        // 1b) Мероприятия
        try {
            activitiesData = await fetchJson('/api/activities?skip=0&limit=500');
            renderActivityTagOptions(activitiesData);
            filterActivities();
        } catch (e) {
            console.warn('Не удалось загрузить мероприятия с API.', e);
            activitiesData = [];
            renderActivityTagOptions(activitiesData);
            renderActivities([]);
        }

        // 2) Профиль: пробуем взять "себя". Если такого id пока нет — показываем "пустой" профиль.
        try {
            const me = await fetchJson(`/api/students/${currentUserId}`);
            renderProfile({
                fullName: me.full_name,
                group: me.study_group,
                role: 'Студент',
                cherries: me.available_points,
            });
        } catch (e) {
            console.warn('Профиль не найден в API (вероятно, в БД ещё нет такого студента).', e);
            renderProfile({
                fullName: "Профиль не найден",
                group: "—",
                role: "—",
                cherries: 0
            });
        }
    })();

    // Фильтры таблицы
    document.getElementById('search-input').addEventListener('input', filterLeaderboard);
    document.getElementById('group-filter').addEventListener('change', filterLeaderboard);

    // Фильтры мероприятий (как у рейтинга)
    document.getElementById('activity-search')?.addEventListener('input', filterActivities);
    document.getElementById('tag-filter')?.addEventListener('change', filterActivities);
});