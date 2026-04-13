# 🎬 FilmDB

Контейнеризированное веб-приложение для управления базой данных фильмов. Включает пользовательский интерфейс, REST API и панель администратора.

---

## Стек

| Слой | Технология |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy |
| База данных | PostgreSQL 16 |
| Авторизация | JWT (PyJWT) + bcrypt |
| Frontend (пользовательский) | Vanilla JS SPA, тёмная тема |
| Frontend (админка) | Vanilla JS SPA |
| Контейнеризация | Docker, Docker Compose |

---

## Быстрый старт

```bash
# 1. Клонировать / распаковать проект
cd project

# 2. Скопировать конфиг окружения
cp .env.example .env

# 3. Поднять БД и приложение
docker compose up -d

# 4. Залить тестовые данные
docker compose --profile seed run --rm seed
```

Приложение доступно по адресу: **http://localhost:8000**

Тестовый аккаунт (после seed):
- Email: `user1@filmdb.example`
- Пароль: `password123`

---

## Структура проекта

```
project/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── sql/
│   └── init.sql              # schema + RBAC (применяется автоматически)
├── app/
│   ├── main.py               # FastAPI приложение, маршруты
│   ├── config.py             # настройки из переменных окружения
│   ├── database.py           # SQLAlchemy engine / session
│   ├── models.py             # ORM-модели (21 таблица)
│   ├── auth.py               # JWT, bcrypt, dependency-инъекции
│   ├── crud.py               # generic CRUD через SQLAlchemy Core
│   ├── meta.py               # метаописание таблиц для динамической админки
│   ├── routers/
│   │   ├── auth_router.py    # /api/auth — login, register, me
│   │   ├── public.py         # /api/public — публичный API
│   │   ├── api.py            # /api/tables — admin CRUD (protected)
│   │   └── meta.py           # /api/meta — метаданные для UI
│   └── static/
│       ├── index.html        # пользовательский SPA
│       ├── admin.html        # панель администратора
│       ├── css/
│       │   ├── main.css      # стили пользовательского интерфейса
│       │   └── admin.css     # стили админки
│       └── js/
│           ├── main.js       # логика пользовательского SPA
│           └── admin.js      # логика админ-панели
└── seed/
    └── seed.py               # генератор тестовых данных (Faker)
```

---

## Маршруты

| URL | Описание |
|---|---|
| `http://localhost:8000/` | Пользовательский интерфейс |
| `http://localhost:8000/admin` | Панель администратора |
| `http://localhost:8000/api/docs` | Swagger UI |

---

## API

### Авторизация

```
POST /api/auth/login      — { email, password } → { access_token, user, roles }
POST /api/auth/register   — { email, password, first_name, last_name }
GET  /api/auth/me         — информация о текущем пользователе
```

### Публичный API (доступен без авторизации)

```
GET  /api/public/films              — каталог фильмов (поиск, фильтр по жанру, сортировка)
GET  /api/public/films/{id}         — фильм + жанры + состав + рецензии + награды
GET  /api/public/genres             — список жанров
GET  /api/public/persons            — персоны (поиск, фильтр по роли)
GET  /api/public/persons/{id}       — персона + фильмография
GET  /api/public/festivals          — фестивали
POST /api/public/reviews            — добавить рецензию (требует авторизации)
GET  /api/public/profile/reviews    — мои рецензии (требует авторизации)
```

### Admin CRUD (требует роли `admin` / `content_editor` / `moderator`)

```
GET    /api/tables/{table}          — список записей (поиск, пагинация)
GET    /api/tables/{table}/{id}     — одна запись
POST   /api/tables/{table}          — создать запись
PUT    /api/tables/{table}/{id}     — обновить запись
DELETE /api/tables/{table}/{id}     — удалить запись
```

---

## Роли и права доступа

| Роль | Права |
|---|---|
| `guest` (без токена) | Просмотр каталога, персон, фестивалей |
| `user` | + Написание рецензий, профиль |
| `moderator` | + Доступ к панели администратора |
| `content_editor` | + Доступ к панели администратора |
| `admin` | Полный доступ |

---

## База данных

21 таблица, сгруппированных по доменам:

- **Справочники**: `country`, `city`, `genre`
- **Фильмы**: `film`, `film_genre`, `film_person`
- **Персоны**: `person`, `person_role`
- **Пользователи**: `app_user`, `user_device`, `user_preference`, `user_role`
- **Активность**: `view_history`, `review`, `review_rating`, `critic_review`
- **Фестивали и награды**: `festival`, `award`
- **RBAC**: `role`, `permission`, `role_permission`

---

## Тестовые данные (seed)

После запуска `seed.py` в БД будет:

| Сущность | Количество |
|---|---|
| Страны / Города | 20 / 31 |
| Жанры | 12 |
| Фильмы | 50 |
| Персоны | 80 |
| Пользователи | 100 |
| Устройства | ~250 |
| Просмотры | ~500 |
| Рецензии | 200 |
| Критические рецензии | 80 |
| Фестивали / Награды | 10 / 120 |

---

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `POSTGRES_DB` | `filmdb` | Имя базы данных |
| `POSTGRES_USER` | `filmdb` | Пользователь БД |
| `POSTGRES_PASSWORD` | `filmdb` | Пароль БД |
| `SECRET_KEY` | `changeme` | Секрет для подписи JWT |

---

## Разработка (без Docker)

```bash
pip install -r requirements.txt

# Запустить только БД
docker compose up -d db

# Запустить приложение локально
DATABASE_URL=postgresql://filmdb:filmdb@localhost:5432/filmdb \
uvicorn app.main:app --reload
```
