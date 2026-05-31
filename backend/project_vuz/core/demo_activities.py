"""Шаблоны демо-мероприятий для записи на защите (тег «ДЕМО», предстоящие)."""

from __future__ import annotations

DEMO_TAG = "ДЕМО"


def demo_categories(*extra: str) -> list[str]:
    tags = [DEMO_TAG]
    for item in extra:
        if item and item not in tags:
            tags.append(item)
    return tags


# Предстоящие мероприятия без картинок — для seed и seed_demo_activities.py
DEMO_UPCOMING_ACTIVITIES: list[dict] = [
    {
        "title": "Хакатон «Code & Chill»",
        "organizer": "IT-Клуб",
        "description": (
            "Разработка инновационных решений для университета за 24 часа. "
            "Приходи с командой или найди её на месте!"
        ),
        "categories": demo_categories("Программирование", "Хакатон", "IT"),
        "base_reward": 50,
        "event_date": "25 Мая, 10:00",
        "images": [],
        "is_completed": False,
    },
    {
        "title": "Волонтерство на Дне Открытых Дверей",
        "organizer": "Университет",
        "description": "Помощь в организации навигации для абитуриентов и их родителей.",
        "categories": demo_categories("Социальное", "Волонтерство", "ВУЗ"),
        "base_reward": 30,
        "event_date": "28 Мая, 09:00",
        "images": [],
        "is_completed": False,
    },
    {
        "title": "Лекция: карьера в IT",
        "organizer": "Деканат",
        "description": "Приглашённые спикеры из индустрии.",
        "categories": demo_categories("IT", "Наука"),
        "base_reward": 20,
        "event_date": "30 Мая, 16:00",
        "images": [],
        "is_completed": False,
    },
    {
        "title": "Лекция по GeoAI",
        "organizer": "Деканат",
        "description": (
            "Обсуждаем современные тренды в геоаналитике, цифровые двойники городов "
            "и спутниковые снимки."
        ),
        "categories": demo_categories("Наука", "Геодезия"),
        "base_reward": 15,
        "event_date": "2 Июня, 14:30",
        "images": [],
        "is_completed": False,
    },
    {
        "title": "Лекция по Python",
        "organizer": "Деканат",
        "description": "Практика и основы Python для инженерных задач.",
        "categories": demo_categories("Наука", "IT"),
        "base_reward": 15,
        "event_date": "5 Июня, 14:30",
        "images": [],
        "is_completed": False,
    },
    {
        "title": "Фестиваль «ВИШенка»",
        "organizer": "Студсовет",
        "description": "Главное мероприятие института — знакомство, активности и награды.",
        "categories": demo_categories("Социальное", "ВУЗ"),
        "base_reward": 50,
        "event_date": "10 Июня, 18:00",
        "images": [],
        "is_completed": False,
    },
]
