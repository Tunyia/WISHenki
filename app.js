// ID текущего залогиненного пользователя (Алексей Смирнов)
// В будущем этот ID будет приходить от FastAPI при авторизации
const currentUserId = 19; 

// Шаблонные данные для лидерборда (в будущем придут в формате JSON от FastAPI)
const mockLeaderboardData = [
    { id: 1, fullName: "Алексей Смирнов", group: "ШЦТ-111", cherries: 114 },
    { id: 2, fullName: "Екатерина Иванова", group: "ШЦТ-112", cherries: 130 },
    { id: 3, fullName: "Иван Петров", group: "ШЦТ-111", cherries: 115 },
    { id: 4, fullName: "Анна Сидорова", group: "ШЦТ-112", cherries: 90 },
    { id: 5, fullName: "Дмитрий Волков", group: "ШЦТ-111", cherries: 85 },
    { id: 6, fullName: "Волк Дмитриев", group: "ШЦТ-111", cherries: 85 },
    { id: 7, fullName: "Студентович 1", group: "ШЦТ-111", cherries: 0 },
    { id: 8, fullName: "Студентович 2", group: "ШЦТ-111", cherries: 0 },
    { id: 9, fullName: "Студентович 3", group: "ШЦТ-111", cherries: 0 },
    { id: 10, fullName: "Студентович 4", group: "ШЦТ-111", cherries: 0 },
    { id: 11, fullName: "Студентович 5", group: "ШЦТ-111", cherries: 0 },
    { id: 12, fullName: "Студентович 6", group: "ШЦТ-111", cherries: 0 },
    { id: 13, fullName: "Студентович 7", group: "ШЦТ-111", cherries: 0 },
    { id: 14, fullName: "Студентович 8", group: "ШЦТ-111", cherries: 0 },
    { id: 15, fullName: "Студентович 9", group: "ШЦТ-112", cherries: 0 },
    { id: 16, fullName: "Студентович 10", group: "ШЦТ-112", cherries: 0 },
    { id: 17, fullName: "Студентович 10", group: "ШЦТ-112", cherries: 0 },
    { id: 18, fullName: "Ченцов Артемий", group: "ШЦТ-111", cherries: 999 },
    { id: 19, fullName: "Жмышенко Валерий", group: "ГЛЭК-111", cherries: 145}
];

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

const mockActivitiesData = [
    {
        id: 1,
        title: "Хакатон «Code & Chill»",
        organizer: "IT-Клуб",
        description: "Разработка инновационных решений для университета за 24 часа. Приходи с командой или найди её на месте!",
        // Добавили несколько категорий
        categories: ["Программирование", "Хакатон", "IT"], 
        base_reward: 50,
        event_date: "15 Октября, 10:00"
    },
    {
        id: 2,
        title: "Лекция по GeoAI",
        organizer: "Деканат",
        description: "Обсуждаем современные тренды в геоаналитике, цифровые двойники городов и спутниковые снимки.",
        categories: ["Наука", "Геодезия"],
        base_reward: 15,
        event_date: "18 Октября, 14:30"
    },
    {
        id: 3,
        title: "Волонтерство на Дне Открытых Дверей",
        organizer: "Университет",
        description: "Помощь в организации навигации для абитуриентов и их родителей. Нужны ответственные ребята.",
        categories: ["Социальное", "Волонтерство", "ВУЗ"],
        base_reward: 30,
        event_date: "20 Октября, 09:00"
    },
    {
        id: 4,
        title: "Хакатон «Code & Chill»",
        organizer: "IT-Клуб",
        description: "Разработка инновационных решений для университета за 24 часа.",
        categories: ["IT", "Хакатон"], 
        base_reward: 50,
        event_date: "15 Октября, 10:00"
    },
    {
        id: 5,
        title: "Лекция по Python",
        organizer: "Деканат",
        description: "Обсуждаем python!",
        categories: ["Наука", "IT"],
        base_reward: 15,
        event_date: "18 Октября, 14:30"
    }
];

// Вспомогательная функция для подбора цвета тега
function getTagClass(tagName) {
    const name = tagName.toLowerCase();
    if (name.includes('it') || name.includes('программирование')) return 'tag-it';
    if (name.includes('наука') || name.includes('лекция')) return 'tag-science';
    if (name.includes('социальное') || name.includes('волонтер')) return 'tag-social';
    return 'tag-default';
}

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
    });
}

// ОСНОВНОЙ БЛОК: Запускаем всё, когда страница загрузилась
document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Имитация запроса к FastAPI для получения данных профиля
    // В будущем: const mockProfileData = await fetch('/api/users/me').then(r => r.json());
    const mockProfileData = {
        fullName: "Жмышенко Валерий",
        group: "ГЛЭК-111", // Исправил опечатку ЩЦТ -> ШЦТ для консистентности
        role: "Студент",
        cherries: 145
    };

    // 2. Обновляем верхнюю личную карточку
    renderProfile(mockProfileData);

    // 3. Отрисовываем лидерборд в первый раз (функция сама отсортирует моковые данные)
    // Перед первым рендером полезно отсортировать данные
    mockLeaderboardData.sort((a, b) => b.cherries - a.cherries);
    renderLeaderboard(mockLeaderboardData);

    // 4. Вешаем слушатели на строку поиска и селект, чтобы фильтровать без перезагрузки страницы
    document.getElementById('search-input').addEventListener('input', filterLeaderboard);
    document.getElementById('group-filter').addEventListener('change', filterLeaderboard);

    // 5. Карточки мероприятий
    renderActivities(mockActivitiesData);
});