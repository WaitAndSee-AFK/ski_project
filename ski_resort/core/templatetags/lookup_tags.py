# Импортируем библиотеку для работы с шаблонами Django
from django import template

# Создаём объект библиотеки шаблонов
register = template.Library()

# Регистрируем фильтр lookup для поиска значения в словаре по ключу
@register.filter
def lookup(dictionary, key):
    # Возвращаем значение словаря по ключу или None, если ключ не найден
    return dictionary.get(key)