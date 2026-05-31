"""Теги мероприятий, общие для импорта и API."""

# Уникальный тег только у мероприятий, импортированных из Excel (is_completed=True).
IMPORTED_PAST_TAG = "прошедшие"


def with_imported_past_tag(categories: list[str]) -> list[str]:
    result = list(categories)
    if IMPORTED_PAST_TAG not in result:
        result.insert(0, IMPORTED_PAST_TAG)
    return result
