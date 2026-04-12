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
    const activity = mockActivitiesData.find(a => a.id === activityId);
    if (!activity) return;

    currentImages = activity.images || ["photos/kot.png", "photos/kot2.png", "photos/nekot.png"];
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