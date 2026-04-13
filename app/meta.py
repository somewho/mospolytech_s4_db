"""
Table metadata — single source of truth для admin UI.
Описывает каждую таблицу: колонки, типы, FK-ссылки, что показывать в списке.
"""

# Типы колонок для фронтенда:
# int, str, text, date, datetime, decimal, bool
# fk  -> { ref_table, ref_label }  — рендерится как <select>
# enum -> { choices: [...] }       — рендерится как <select>

TABLES = {
    # ── Справочники ─────────────────────────────────────────────────────────
    "country": {
        "label": "Страны",
        "group": "Справочники",
        "pk": "country_id",
        "list_columns": ["country_id", "name"],
        "columns": [
            {"name": "country_id",  "label": "ID",      "type": "int",  "readonly": True},
            {"name": "name",        "label": "Название", "type": "str",  "required": True},
        ],
    },
    "city": {
        "label": "Города",
        "group": "Справочники",
        "pk": "city_id",
        "list_columns": ["city_id", "name", "country_id"],
        "columns": [
            {"name": "city_id",    "label": "ID",      "type": "int", "readonly": True},
            {"name": "country_id", "label": "Страна",  "type": "fk",  "ref_table": "country", "ref_label": "name", "required": True},
            {"name": "name",       "label": "Название", "type": "str", "required": True},
        ],
    },
    "genre": {
        "label": "Жанры",
        "group": "Справочники",
        "pk": "genre_id",
        "list_columns": ["genre_id", "name"],
        "columns": [
            {"name": "genre_id",     "label": "ID",         "type": "int",  "readonly": True},
            {"name": "name",         "label": "Название",   "type": "str",  "required": True},
            {"name": "description",  "label": "Описание",   "type": "text"},
        ],
    },

    # ── Фильмы ──────────────────────────────────────────────────────────────
    "film": {
        "label": "Фильмы",
        "group": "Фильмы",
        "pk": "film_id",
        "list_columns": ["film_id", "title", "created_date", "average_rating", "age_restriction"],
        "columns": [
            {"name": "film_id",        "label": "ID",              "type": "int",     "readonly": True},
            {"name": "title",          "label": "Название",        "type": "str",     "required": True},
            {"name": "description",    "label": "Описание",        "type": "text"},
            {"name": "created_date",   "label": "Дата выхода",     "type": "date"},
            {"name": "age_restriction","label": "Возрастное огр.", "type": "enum",
             "choices": ["0+", "6+", "12+", "16+", "18+"]},
            {"name": "average_rating", "label": "Средний рейтинг", "type": "decimal"},
            {"name": "added_at",       "label": "Добавлен",        "type": "datetime", "readonly": True},
        ],
    },
    "film_genre": {
        "label": "Фильм → Жанр",
        "group": "Фильмы",
        "pk": "film_genre_id",
        "list_columns": ["film_genre_id", "film_id", "genre_id"],
        "columns": [
            {"name": "film_genre_id", "label": "ID",    "type": "int", "readonly": True},
            {"name": "film_id",       "label": "Фильм", "type": "fk",  "ref_table": "film",  "ref_label": "title",  "required": True},
            {"name": "genre_id",      "label": "Жанр",  "type": "fk",  "ref_table": "genre", "ref_label": "name",   "required": True},
        ],
    },
    "film_person": {
        "label": "Фильм → Персона",
        "group": "Фильмы",
        "pk": "film_person_id",
        "list_columns": ["film_person_id", "film_id", "person_id", "role"],
        "columns": [
            {"name": "film_person_id", "label": "ID",      "type": "int", "readonly": True},
            {"name": "film_id",        "label": "Фильм",   "type": "fk",  "ref_table": "film",   "ref_label": "title",     "required": True},
            {"name": "person_id",      "label": "Персона", "type": "fk",  "ref_table": "person", "ref_label": "last_name|first_name", "required": True},
            {"name": "role",           "label": "Роль",    "type": "enum",
             "choices": ["director", "actor", "producer", "writer", "composer", "cinematographer", "editor"],
             "required": True},
        ],
    },

    # ── Персоны ─────────────────────────────────────────────────────────────
    "person": {
        "label": "Персоны",
        "group": "Персоны",
        "pk": "person_id",
        "list_columns": ["person_id", "last_name", "first_name", "birth_date", "country_id"],
        "columns": [
            {"name": "person_id",   "label": "ID",           "type": "int",  "readonly": True},
            {"name": "first_name",  "label": "Имя",          "type": "str",  "required": True},
            {"name": "last_name",   "label": "Фамилия",      "type": "str"},
            {"name": "middle_name", "label": "Отчество",     "type": "str"},
            {"name": "birth_date",  "label": "Дата рожд.",   "type": "date"},
            {"name": "birth_place", "label": "Место рожд.",  "type": "str"},
            {"name": "country_id",  "label": "Страна",       "type": "fk",   "ref_table": "country", "ref_label": "name"},
            {"name": "city_id",     "label": "Город",        "type": "fk",   "ref_table": "city",    "ref_label": "name"},
            {"name": "biography",   "label": "Биография",    "type": "text"},
            {"name": "education",   "label": "Образование",  "type": "text"},
            {"name": "photo",       "label": "Фото (URL)",   "type": "str"},
            {"name": "created_at",  "label": "Создан",       "type": "datetime", "readonly": True},
        ],
    },
    "person_role": {
        "label": "Роли персон",
        "group": "Персоны",
        "pk": "person_role_id",
        "list_columns": ["person_role_id", "person_id", "role"],
        "columns": [
            {"name": "person_role_id", "label": "ID",      "type": "int", "readonly": True},
            {"name": "person_id",      "label": "Персона", "type": "fk",  "ref_table": "person", "ref_label": "last_name|first_name", "required": True},
            {"name": "role",           "label": "Роль",    "type": "enum",
             "choices": ["director", "actor", "producer", "writer", "composer", "cinematographer", "editor", "critic"],
             "required": True},
        ],
    },

    # ── Пользователи ────────────────────────────────────────────────────────
    "app_user": {
        "label": "Пользователи",
        "group": "Пользователи",
        "pk": "user_id",
        "list_columns": ["user_id", "email", "last_name", "first_name", "rating", "registration_date"],
        "columns": [
            {"name": "user_id",           "label": "ID",            "type": "int",      "readonly": True},
            {"name": "first_name",        "label": "Имя",           "type": "str",      "required": True},
            {"name": "last_name",         "label": "Фамилия",       "type": "str"},
            {"name": "email",             "label": "Email",         "type": "str",      "required": True},
            {"name": "password_hash",     "label": "Пароль",         "type": "password"},
            {"name": "birth_date",        "label": "Дата рожд.",    "type": "date"},
            {"name": "gender",            "label": "Пол",           "type": "enum",     "choices": ["male", "female", "other"]},
            {"name": "country_id",        "label": "Страна",        "type": "fk",       "ref_table": "country", "ref_label": "name"},
            {"name": "city_id",           "label": "Город",         "type": "fk",       "ref_table": "city",    "ref_label": "name"},
            {"name": "avatar",            "label": "Аватар (URL)",  "type": "str"},
            {"name": "rating",            "label": "Рейтинг",       "type": "decimal"},
            {"name": "registration_date", "label": "Регистрация",   "type": "datetime", "readonly": True},
            {"name": "last_login",        "label": "Последний вход","type": "datetime"},
        ],
    },
    "user_device": {
        "label": "Устройства",
        "group": "Пользователи",
        "pk": "device_id",
        "list_columns": ["device_id", "user_id", "type", "model", "operating_system"],
        "columns": [
            {"name": "device_id",         "label": "ID",              "type": "int",  "readonly": True},
            {"name": "user_id",           "label": "Пользователь",    "type": "fk",   "ref_table": "app_user", "ref_label": "email", "required": True},
            {"name": "type",              "label": "Тип",             "type": "enum", "choices": ["desktop", "mobile", "tablet", "tv", "other"], "required": True},
            {"name": "model",             "label": "Модель",          "type": "str"},
            {"name": "manufacturer",      "label": "Производитель",   "type": "str"},
            {"name": "operating_system",  "label": "ОС",             "type": "str"},
            {"name": "os_version",        "label": "Версия ОС",       "type": "str"},
            {"name": "browser",           "label": "Браузер",         "type": "str"},
            {"name": "browser_version",   "label": "Версия браузера", "type": "str"},
            {"name": "screen_resolution", "label": "Разрешение",      "type": "str"},
            {"name": "registration_date", "label": "Зарегистрировано","type": "datetime", "readonly": True},
            {"name": "last_used_at",      "label": "Последнее исп.",  "type": "datetime"},
        ],
    },
    "user_preference": {
        "label": "Предпочтения",
        "group": "Пользователи",
        "pk": "preference_id",
        "list_columns": ["preference_id", "user_id", "preference_type", "genre_id", "film_id"],
        "columns": [
            {"name": "preference_id",   "label": "ID",              "type": "int",  "readonly": True},
            {"name": "user_id",         "label": "Пользователь",    "type": "fk",   "ref_table": "app_user", "ref_label": "email", "required": True},
            {"name": "preference_type", "label": "Тип",             "type": "enum", "choices": ["like", "dislike", "watchlist", "watched"], "required": True},
            {"name": "genre_id",        "label": "Жанр",            "type": "fk",   "ref_table": "genre", "ref_label": "name"},
            {"name": "film_id",         "label": "Фильм",           "type": "fk",   "ref_table": "film",  "ref_label": "title"},
            {"name": "added_at",        "label": "Добавлено",       "type": "datetime", "readonly": True},
        ],
    },
    "user_role": {
        "label": "Роли пользователей",
        "group": "Пользователи",
        "pk": None,  # composite PK
        "composite_pk": ["user_id", "role_id"],
        "list_columns": ["user_id", "role_id", "assigned_at"],
        "columns": [
            {"name": "user_id",     "label": "Пользователь", "type": "fk",   "ref_table": "app_user", "ref_label": "email", "required": True},
            {"name": "role_id",     "label": "Роль",         "type": "fk",   "ref_table": "role",     "ref_label": "name",  "required": True},
            {"name": "assigned_at", "label": "Назначено",    "type": "datetime", "readonly": True},
        ],
    },

    # ── Активность ──────────────────────────────────────────────────────────
    "view_history": {
        "label": "История просмотров",
        "group": "Активность",
        "pk": "view_id",
        "list_columns": ["view_id", "user_id", "film_id", "viewed_at", "view_percent"],
        "columns": [
            {"name": "view_id",       "label": "ID",             "type": "int",     "readonly": True},
            {"name": "user_id",       "label": "Пользователь",   "type": "fk",      "ref_table": "app_user",    "ref_label": "email", "required": True},
            {"name": "film_id",       "label": "Фильм",          "type": "fk",      "ref_table": "film",        "ref_label": "title", "required": True},
            {"name": "device_id",     "label": "Устройство",     "type": "fk",      "ref_table": "user_device", "ref_label": "model", "required": True},
            {"name": "viewed_at",     "label": "Дата просмотра", "type": "datetime", "readonly": True},
            {"name": "view_duration", "label": "Длительность (с)","type": "int"},
            {"name": "view_percent",  "label": "Прогресс (%)",   "type": "decimal"},
            {"name": "ip_address",    "label": "IP-адрес",       "type": "str"},
        ],
    },
    "review": {
        "label": "Рецензии",
        "group": "Активность",
        "pk": "review_id",
        "list_columns": ["review_id", "film_id", "user_id", "film_rating", "created_at"],
        "columns": [
            {"name": "review_id",      "label": "ID",           "type": "int",  "readonly": True},
            {"name": "film_id",        "label": "Фильм",        "type": "fk",   "ref_table": "film",     "ref_label": "title", "required": True},
            {"name": "user_id",        "label": "Пользователь", "type": "fk",   "ref_table": "app_user", "ref_label": "email", "required": True},
            {"name": "review_text",    "label": "Текст",        "type": "text", "required": True},
            {"name": "film_rating",    "label": "Оценка (1-10)","type": "int"},
            {"name": "likes_count",    "label": "Лайки",        "type": "int"},
            {"name": "dislikes_count", "label": "Дизлайки",     "type": "int"},
            {"name": "created_at",     "label": "Создано",      "type": "datetime", "readonly": True},
            {"name": "updated_at",     "label": "Обновлено",    "type": "datetime"},
        ],
    },
    "review_rating": {
        "label": "Оценки рецензий",
        "group": "Активность",
        "pk": "review_rating_id",
        "list_columns": ["review_rating_id", "review_id", "user_id", "rating_type", "rated_at"],
        "columns": [
            {"name": "review_rating_id", "label": "ID",            "type": "int",  "readonly": True},
            {"name": "review_id",        "label": "Рецензия",      "type": "fk",   "ref_table": "review",   "ref_label": "review_id", "required": True},
            {"name": "user_id",          "label": "Пользователь",  "type": "fk",   "ref_table": "app_user", "ref_label": "email",     "required": True},
            {"name": "rating_type",      "label": "Тип оценки",    "type": "enum", "choices": ["like", "dislike"], "required": True},
            {"name": "rated_at",         "label": "Дата оценки",   "type": "datetime", "readonly": True},
        ],
    },
    "critic_review": {
        "label": "Критические рецензии",
        "group": "Активность",
        "pk": "critic_review_id",
        "list_columns": ["critic_review_id", "film_id", "person_id", "rating", "published_at"],
        "columns": [
            {"name": "critic_review_id", "label": "ID",             "type": "int",  "readonly": True},
            {"name": "film_id",          "label": "Фильм",          "type": "fk",   "ref_table": "film",   "ref_label": "title",     "required": True},
            {"name": "person_id",        "label": "Критик",         "type": "fk",   "ref_table": "person", "ref_label": "last_name|first_name", "required": True},
            {"name": "publication_name", "label": "Издание",        "type": "str"},
            {"name": "title",            "label": "Заголовок",      "type": "str"},
            {"name": "review_text",      "label": "Текст",          "type": "text", "required": True},
            {"name": "summary",          "label": "Краткое резюме", "type": "text"},
            {"name": "rating",           "label": "Оценка",         "type": "decimal"},
            {"name": "published_at",     "label": "Дата публ.",     "type": "date"},
            {"name": "source_url",       "label": "URL источника",  "type": "str"},
            {"name": "views_count",      "label": "Просмотры",      "type": "int"},
        ],
    },

    # ── Фестивали ───────────────────────────────────────────────────────────
    "festival": {
        "label": "Фестивали",
        "group": "Фестивали и награды",
        "pk": "festival_id",
        "list_columns": ["festival_id", "name", "country_id", "founded_year", "prestige_rating"],
        "columns": [
            {"name": "festival_id",     "label": "ID",           "type": "int",     "readonly": True},
            {"name": "name",            "label": "Название",     "type": "str",     "required": True},
            {"name": "country_id",      "label": "Страна",       "type": "fk",      "ref_table": "country", "ref_label": "name"},
            {"name": "city_id",         "label": "Город",        "type": "fk",      "ref_table": "city",    "ref_label": "name"},
            {"name": "founded_year",    "label": "Год основания","type": "int"},
            {"name": "description",     "label": "Описание",     "type": "text"},
            {"name": "prestige_rating", "label": "Рейтинг прест.","type": "decimal"},
        ],
    },
    "award": {
        "label": "Награды",
        "group": "Фестивали и награды",
        "pk": "award_id",
        "list_columns": ["award_id", "name", "film_id", "festival_id", "year", "status"],
        "columns": [
            {"name": "award_id",    "label": "ID",         "type": "int",  "readonly": True},
            {"name": "name",        "label": "Название",   "type": "str",  "required": True},
            {"name": "festival_id", "label": "Фестиваль",  "type": "fk",   "ref_table": "festival", "ref_label": "name", "required": True},
            {"name": "year",        "label": "Год",        "type": "int",  "required": True},
            {"name": "film_id",     "label": "Фильм",      "type": "fk",   "ref_table": "film",   "ref_label": "title"},
            {"name": "person_id",   "label": "Персона",    "type": "fk",   "ref_table": "person", "ref_label": "last_name|first_name"},
            {"name": "category",    "label": "Категория",  "type": "str"},
            {"name": "person_role", "label": "Роль персоны","type": "str"},
            {"name": "status",      "label": "Статус",     "type": "enum", "choices": ["winner", "nominee"], "required": True},
            {"name": "description", "label": "Описание",   "type": "text"},
        ],
    },

    # ── RBAC ────────────────────────────────────────────────────────────────
    "role": {
        "label": "Роли",
        "group": "RBAC",
        "pk": "role_id",
        "list_columns": ["role_id", "name", "description"],
        "columns": [
            {"name": "role_id",     "label": "ID",         "type": "int",  "readonly": True},
            {"name": "name",        "label": "Название",   "type": "str",  "required": True},
            {"name": "description", "label": "Описание",   "type": "text"},
        ],
    },
    "permission": {
        "label": "Права доступа",
        "group": "RBAC",
        "pk": "permission_id",
        "list_columns": ["permission_id", "action", "resource", "description"],
        "columns": [
            {"name": "permission_id", "label": "ID",        "type": "int", "readonly": True},
            {"name": "action",        "label": "Действие",  "type": "str", "required": True},
            {"name": "resource",      "label": "Ресурс",    "type": "str", "required": True},
            {"name": "description",   "label": "Описание",  "type": "text"},
        ],
    },
    "role_permission": {
        "label": "Роль → Право",
        "group": "RBAC",
        "pk": None,
        "composite_pk": ["role_id", "permission_id"],
        "list_columns": ["role_id", "permission_id"],
        "columns": [
            {"name": "role_id",       "label": "Роль",         "type": "fk", "ref_table": "role",       "ref_label": "name",   "required": True},
            {"name": "permission_id", "label": "Право доступа","type": "fk", "ref_table": "permission", "ref_label": "action|resource", "required": True},
        ],
    },
}

# Порядок групп для отображения в sidebar
GROUP_ORDER = [
    "Справочники",
    "Фильмы",
    "Персоны",
    "Пользователи",
    "Активность",
    "Фестивали и награды",
    "RBAC",
]
