# Web_Shop_Django

## Описание
Проект интернет-магазина на Django в рамках обучения Основам Django

## Установка
- [клонируйте репозиторий](https://github.com/Grigorii-Goncharov/Web_shop_django.git
)
```

## Использование
1. Перейдите на страницу в GitHub.
2. Создайте новую учетную запись или войдите в существующий.
3. Перенести проект в локальный репозиторий.
4. Откройте модуль manage.py и перейдите по сслыке http://127.0.0.1:8000/
5. Откройте модуль manage.py и перейдите по сслыке http://127.0.0.1:8000/blog/ - запуск приложения Блога с путешествиями
6. Добавалена регистрация и атторизация приложения catalog
7. Реализованы права доступа по категорям пользьзователей, реализованы проава модератора, кнопки "редактивроать",
 "Удалить продукт", есть теперь только у Администратора, МОдератора и вледельца продукта!
8. Добавлено: брокер кэширования Redis
```
from django.core.cache import cache

# Попробуем записать и прочитать из кэша
cache.set('test_key', 'работает!', 30)  # сохраняем на 30 секунд
result = cache.get('test_key')
print(result)  # Должно вывести: работает!
```

создание фикстур:
"python -Xutf8 manage.py dumpdata catalog.Products catalog.Category --output general_fixture.json --indent 4"  - общие
"python -Xutf8 manage.py dumpdata catalog.Products --output products_fixture.json --indent 4" - конкретное
"python manage.py loaddata products_fixture_load.json --database=default --ignorenonexistent"  - загрузка с указанием БД 
из файла settings и указание игнорирования несуществующих полей

Запуск кастомной команды на добалвение тестовых продуктов по категорям:   
"python manage.py add_test_products"   

## Зависимости
Зависимости проекта управляются через Poetry. Они перечислены в файле `pyproject.toml`


## Документация:
Для получения дополнительной информации обратитесь к [документации](docs/README.md).

## Лицензия:

Этот проект лицензирован по [лицензии MIT](LICENSE).