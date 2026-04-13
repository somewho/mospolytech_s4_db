"""
Генерация тестовых данных для FilmDB.
Запуск: python seed/seed.py
"""
import os
import sys
import random
from datetime import date, timedelta

from faker import Faker
from sqlalchemy import create_engine, text
import bcrypt as _bcrypt

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://filmdb:filmdb@localhost:5432/filmdb")
engine = create_engine(DATABASE_URL)
fake = Faker(["ru_RU", "en_US"])
fake_ru = Faker("ru_RU")
fake_en = Faker("en_US")
_SALT = _bcrypt.gensalt(rounds=4)  # rounds=4 для скорости seed

def hash_password(pwd: str) -> str:
    return _bcrypt.hashpw(pwd.encode(), _SALT).decode()

def run(q, params=None):
    with engine.begin() as c:
        r = c.execute(text(q), params or {})
        return r

def insert(table, rows, returning=None):
    if not rows:
        return []
    keys = list(rows[0].keys())
    cols = ", ".join(f'"{k}"' for k in keys)
    vals = ", ".join(f":{k}" for k in keys)
    ret  = f" RETURNING {returning}" if returning else ""
    ids  = []
    with engine.begin() as c:
        for row in rows:
            r = c.execute(text(f'INSERT INTO "{table}" ({cols}) VALUES ({vals}){ret}'), row)
            if returning:
                ids.append(r.scalar())
    return ids

def rand_date(start_year=1900, end_year=2023):
    start = date(start_year, 1, 1)
    end   = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

# ── 1. Countries ──────────────────────────────────────────────────────────────
print("→ countries")
country_names = [
    "Россия", "США", "Франция", "Великобритания", "Германия", "Италия",
    "Япония", "Китай", "Южная Корея", "Испания", "Польша", "Австралия",
    "Канада", "Бразилия", "Индия", "Иран", "Дания", "Швеция", "Аргентина", "Мексика",
]
run("DELETE FROM country CASCADE")
country_ids = insert("country", [{"name": n} for n in country_names], returning="country_id")
print(f"   {len(country_ids)} стран")

# ── 2. Cities ─────────────────────────────────────────────────────────────────
print("→ cities")
cities_data = [
    ("Москва", 0), ("Санкт-Петербург", 0), ("Новосибирск", 0),
    ("Нью-Йорк", 1), ("Лос-Анджелес", 1), ("Чикаго", 1),
    ("Париж", 2), ("Лион", 2),
    ("Лондон", 3), ("Манчестер", 3),
    ("Берлин", 4), ("Мюнхен", 4),
    ("Рим", 5), ("Милан", 5),
    ("Токио", 6), ("Осака", 6),
    ("Пекин", 7), ("Шанхай", 7),
    ("Сеул", 8),
    ("Мадрид", 9), ("Барселона", 9),
    ("Варшава", 10),
    ("Сидней", 11),
    ("Торонто", 12),
    ("Рио-де-Жанейро", 13),
    ("Мумбаи", 14),
    ("Тегеран", 15),
    ("Копенгаген", 16),
    ("Стокгольм", 17),
    ("Буэнос-Айрес", 18),
    ("Мехико", 19),
]
city_ids = insert("city", [
    {"country_id": country_ids[ci], "name": name}
    for name, ci in cities_data
], returning="city_id")
print(f"   {len(city_ids)} городов")

# ── 3. Genres ─────────────────────────────────────────────────────────────────
print("→ genres")
genres = [
    ("Драма",        "Фильмы с акцентом на эмоциональный и психологический конфликт"),
    ("Комедия",      "Лёгкие фильмы, призванные развлечь и рассмешить"),
    ("Боевик",       "Фильмы с динамичными сценами борьбы и погонь"),
    ("Триллер",      "Напряжённые фильмы с элементами тайны и саспенса"),
    ("Ужасы",        "Фильмы, призванные напугать зрителя"),
    ("Фантастика",   "Истории с научно-фантастическими допущениями"),
    ("Фэнтези",      "Истории с магией, мифическими существами и вымышленными мирами"),
    ("Документальный","Документальные записи реальных событий и личностей"),
    ("Мелодрама",    "Фильмы о романтических отношениях и чувствах"),
    ("Анимация",     "Рисованные или компьютерные мультипликационные фильмы"),
    ("Криминал",     "Истории о преступлениях и их расследовании"),
    ("Биография",    "Истории жизни реальных людей"),
]
genre_ids = insert("genre", [{"name": n, "description": d} for n,d in genres], returning="genre_id")
print(f"   {len(genre_ids)} жанров")

# ── 4. Persons ────────────────────────────────────────────────────────────────
print("→ persons")
roles_pool = ["director", "actor", "producer", "writer", "composer", "cinematographer", "critic"]
persons = []
for _ in range(80):
    ci = random.randint(0, len(country_ids)-1)
    persons.append({
        "first_name":  fake_ru.first_name(),
        "last_name":   fake_ru.last_name(),
        "middle_name": fake_ru.middle_name() if random.random() > 0.5 else None,
        "birth_date":  rand_date(1930, 1990),
        "birth_place": fake_ru.city(),
        "country_id":  country_ids[ci],
        "city_id":     random.choice(city_ids),
        "biography":   fake_ru.text(max_nb_chars=400),
        "education":   fake_ru.text(max_nb_chars=150) if random.random() > 0.4 else None,
        "photo":       None,
    })
person_ids = insert("person", persons, returning="person_id")
print(f"   {len(person_ids)} персон")

# person_roles (каждая персона получает 1-2 роли)
person_role_rows = []
used = set()
for pid in person_ids:
    n_roles = random.randint(1, 2)
    chosen  = random.sample(roles_pool, n_roles)
    for role in chosen:
        key = (pid, role)
        if key not in used:
            person_role_rows.append({"person_id": pid, "role": role})
            used.add(key)
insert("person_role", person_role_rows)
print(f"   {len(person_role_rows)} ролей персон")

# ── 5. Films ──────────────────────────────────────────────────────────────────
print("→ films")
film_titles = [
    "Тихий шторм", "Последний рубеж", "Полночный дозор", "Осколки памяти",
    "Зеркало судьбы", "Красная нить", "Белый шум", "Горизонт событий",
    "Тень прошлого", "Свободное падение", "Северный ветер", "Город теней",
    "Золотой век", "Вечный двигатель", "Сломанные крылья", "Дальние берега",
    "Обратная сторона луны", "Последний поезд", "Хрустальная ночь", "Небесный огонь",
    "Чёрный лебедь", "Призрак оперы", "Код да Винчи", "Мастер и Маргарита",
    "Война и мир", "Анна Каренина", "Доктор Живаго", "Броненосец Потёмкин",
    "Сталкер", "Солярис", "Зеркало", "Иваново детство",
    "Летят журавли", "Баллада о солдате", "Судьба человека", "А зори здесь тихие",
    "Белое солнце пустыни", "Офицеры", "Семнадцать мгновений весны", "Место встречи изменить нельзя",
    "Ирония судьбы", "Служебный роман", "Москва слезам не верит", "Берегись автомобиля",
    "Бриллиантовая рука", "Кавказская пленница", "Операция «Ы»", "Джентльмены удачи", "Афоня", "Мимино",
]
age_restrictions = ["0+", "6+", "12+", "16+", "18+"]
films = []
for title in film_titles:
    films.append({
        "title":          title,
        "description":    fake_ru.text(max_nb_chars=500),
        "created_date":   rand_date(1950, 2024),
        "age_restriction":random.choice(age_restrictions),
        "average_rating": round(random.uniform(4.0, 9.5), 2),
    })
film_ids = insert("film", films, returning="film_id")
print(f"   {len(film_ids)} фильмов")

# film_genre (2-3 жанра на фильм)
fg_rows = []
fg_used = set()
for fid in film_ids:
    for gid in random.sample(genre_ids, random.randint(2, 3)):
        if (fid, gid) not in fg_used:
            fg_rows.append({"film_id": fid, "genre_id": gid})
            fg_used.add((fid, gid))
insert("film_genre", fg_rows)
print(f"   {len(fg_rows)} film_genre")

# film_person
film_roles = ["director", "actor", "producer", "writer", "composer"]
fp_rows = []
fp_used = set()
for fid in film_ids:
    # 1 режиссёр
    director = random.choice(person_ids)
    if (fid, director, "director") not in fp_used:
        fp_rows.append({"film_id": fid, "person_id": director, "role": "director"})
        fp_used.add((fid, director, "director"))
    # 3-5 актёров
    for pid in random.sample(person_ids, random.randint(3, 5)):
        if (fid, pid, "actor") not in fp_used:
            fp_rows.append({"film_id": fid, "person_id": pid, "role": "actor"})
            fp_used.add((fid, pid, "actor"))
insert("film_person", fp_rows)
print(f"   {len(fp_rows)} film_person")

# ── 6. Users ──────────────────────────────────────────────────────────────────
print("→ users")
users = []
for i in range(100):
    ci = random.randint(0, len(country_ids)-1)
    users.append({
        "first_name":       fake_ru.first_name(),
        "last_name":        fake_ru.last_name(),
        "email":            f"user{i+1}@filmdb.example",
        "password_hash":    hash_password("password123"),
        "birth_date":       rand_date(1960, 2005),
        "gender":           random.choice(["male", "female"]),
        "country_id":       country_ids[ci],
        "city_id":          random.choice(city_ids),
        "rating":           round(random.uniform(0, 10), 2),
    })
user_ids = insert("app_user", users, returning="user_id")
print(f"   {len(user_ids)} пользователей")

# user_roles
role_rows = []
with engine.connect() as c:
    db_roles = {r[0]: r[1] for r in c.execute(text("SELECT role_id, name FROM role")).fetchall()}
user_role_rows = []
ur_used = set()
for uid in user_ids:
    # все пользователи получают роль 'user'
    user_role_id = next(k for k,v in db_roles.items() if v == 'user')
    if (uid, user_role_id) not in ur_used:
        user_role_rows.append({"user_id": uid, "role_id": user_role_id})
        ur_used.add((uid, user_role_id))
# 5 модераторов
mod_role_id = next(k for k,v in db_roles.items() if v == 'moderator')
for uid in random.sample(user_ids, 5):
    if (uid, mod_role_id) not in ur_used:
        user_role_rows.append({"user_id": uid, "role_id": mod_role_id})
        ur_used.add((uid, mod_role_id))
# 2 content_editor
ce_role_id = next(k for k,v in db_roles.items() if v == 'content_editor')
for uid in random.sample(user_ids, 2):
    if (uid, ce_role_id) not in ur_used:
        user_role_rows.append({"user_id": uid, "role_id": ce_role_id})
        ur_used.add((uid, ce_role_id))
# 1 admin
admin_role_id = next(k for k,v in db_roles.items() if v == 'admin')
if (user_ids[0], admin_role_id) not in ur_used:
    user_role_rows.append({"user_id": user_ids[0], "role_id": admin_role_id})
insert("user_role", user_role_rows)
print(f"   {len(user_role_rows)} user_role")

# ── 7. Devices ────────────────────────────────────────────────────────────────
print("→ devices")
device_types = ["desktop", "mobile", "tablet", "tv"]
browsers = ["Chrome", "Firefox", "Safari", "Edge"]
os_list  = [("Windows", "11"), ("macOS", "14"), ("Android", "14"), ("iOS", "17"), ("Linux", "Ubuntu 24.04")]
devices = []
for uid in user_ids:
    for _ in range(random.randint(1, 3)):
        osi = random.choice(os_list)
        devices.append({
            "user_id":          uid,
            "type":             random.choice(device_types),
            "model":            fake_en.user_agent()[:50],
            "manufacturer":     random.choice(["Apple", "Samsung", "Google", "Xiaomi", "HP", "Dell"]),
            "operating_system": osi[0],
            "os_version":       osi[1],
            "browser":          random.choice(browsers),
            "browser_version":  str(random.randint(100, 130)),
            "screen_resolution":random.choice(["1920x1080", "2560x1440", "1280x720", "390x844", "820x1180"]),
        })
device_ids = insert("user_device", devices, returning="device_id")
print(f"   {len(device_ids)} устройств")

# ── 8. View history ───────────────────────────────────────────────────────────
print("→ view_history")
view_rows = []
for uid in user_ids:
    user_devs = [d for d, u_id in zip(device_ids, [dv["user_id"] for dv in devices]) if u_id == uid]
    if not user_devs:
        continue
    for _ in range(random.randint(2, 8)):
        pct = round(random.uniform(5, 100), 2)
        dur = int(pct / 100 * random.randint(3600, 9000))
        view_rows.append({
            "user_id":       uid,
            "film_id":       random.choice(film_ids),
            "device_id":     random.choice(user_devs),
            "view_duration": dur,
            "view_percent":  pct,
            "ip_address":    fake_en.ipv4(),
        })
insert("view_history", view_rows)
print(f"   {len(view_rows)} просмотров")

# ── 9. Reviews ────────────────────────────────────────────────────────────────
print("→ reviews")
review_rows = []
rev_used = set()
for _ in range(200):
    uid = random.choice(user_ids)
    fid = random.choice(film_ids)
    if (uid, fid) in rev_used:
        continue
    rev_used.add((uid, fid))
    review_rows.append({
        "film_id":       fid,
        "user_id":       uid,
        "review_text":   fake_ru.text(max_nb_chars=600),
        "film_rating":   random.randint(1, 10),
        "likes_count":   random.randint(0, 200),
        "dislikes_count":random.randint(0, 50),
    })
review_ids = insert("review", review_rows, returning="review_id")
print(f"   {len(review_ids)} рецензий")

# review_ratings
rr_rows = []
rr_used = set()
for rid in random.sample(review_ids, min(len(review_ids), 100)):
    for uid in random.sample(user_ids, random.randint(1, 5)):
        if (rid, uid) not in rr_used:
            rr_rows.append({
                "review_id":   rid,
                "user_id":     uid,
                "rating_type": random.choice(["like", "dislike"]),
            })
            rr_used.add((rid, uid))
insert("review_rating", rr_rows)
print(f"   {len(rr_rows)} оценок рецензий")

# ── 10. Critic reviews ────────────────────────────────────────────────────────
print("→ critic_reviews")
publications = ["Кинопоиск", "КГ-Портал", "Рёв из ямы", "Синемаскоп", "Total Film RU", "Empire RU", "Афиша"]
cr_rows = []
cr_used = set()
critic_person_ids = random.sample(person_ids, min(20, len(person_ids)))
for _ in range(80):
    fid = random.choice(film_ids)
    pid = random.choice(critic_person_ids)
    if (fid, pid) in cr_used:
        continue
    cr_used.add((fid, pid))
    cr_rows.append({
        "film_id":          fid,
        "person_id":        pid,
        "publication_name": random.choice(publications),
        "title":            fake_ru.sentence(nb_words=6)[:100],
        "review_text":      fake_ru.text(max_nb_chars=800),
        "summary":          fake_ru.text(max_nb_chars=200),
        "rating":           round(random.uniform(1.0, 10.0), 1),
        "published_at":     rand_date(2000, 2024),
        "source_url":       f"https://filmdb.example/critic/{fid}/{pid}",
        "views_count":      random.randint(100, 50000),
    })
insert("critic_review", cr_rows)
print(f"   {len(cr_rows)} критических рецензий")

# ── 11. Festivals ─────────────────────────────────────────────────────────────
print("→ festivals")
festival_data = [
    ("Каннский кинофестиваль",            2,  0, 1946, 9.80),
    ("Венецианский кинофестиваль",        5,  12, 1932, 9.70),
    ("Берлинский кинофестиваль (Берлинале)",4, 10, 1951, 9.50),
    ("Sundance Film Festival",             1,  4, 1978, 8.90),
    ("Московский международный кинофестиваль", 0, 0, 1935, 8.20),
    ("Токийский кинофестиваль",           6,  14, 1985, 7.80),
    ("Сеульский кинофестиваль",           8,  18, 1996, 7.50),
    ("Karlovyvary Film Festival",         10, 20, 1946, 7.30),
    ("Sydney Film Festival",              11, 22, 1954, 7.00),
    ("Toronto International Film Festival",12, 24, 1976, 8.60),
]
festival_rows = []
for name, ci, city_i, year, prestige in festival_data:
    festival_rows.append({
        "name":            name,
        "country_id":      country_ids[ci],
        "city_id":         city_ids[city_i] if city_i < len(city_ids) else None,
        "founded_year":    year,
        "description":     fake_ru.text(max_nb_chars=300),
        "prestige_rating": prestige,
    })
festival_ids = insert("festival", festival_rows, returning="festival_id")
print(f"   {len(festival_ids)} фестивалей")

# ── 12. Awards ────────────────────────────────────────────────────────────────
print("→ awards")
categories = [
    "Лучший фильм", "Лучший режиссёр", "Лучшая мужская роль",
    "Лучшая женская роль", "Лучший сценарий", "Лучшая музыка",
    "Гран-при", "Специальный приз жюри", "Лучший дебют",
]
award_rows = []
for _ in range(120):
    fid = random.choice(film_ids)
    pid = random.choice(person_ids) if random.random() > 0.3 else None
    award_rows.append({
        "name":        random.choice(categories),
        "festival_id": random.choice(festival_ids),
        "year":        random.randint(1990, 2024),
        "film_id":     fid,
        "person_id":   pid,
        "category":    random.choice(categories),
        "person_role": random.choice(["director", "actor", "writer"]) if pid else None,
        "status":      random.choice(["winner", "nominee"]),
        "description": fake_ru.text(max_nb_chars=200) if random.random() > 0.5 else None,
    })
award_ids = insert("award", award_rows, returning="award_id")
print(f"   {len(award_ids)} наград")

# ── 13. User preferences ──────────────────────────────────────────────────────
print("→ user_preferences")
pref_types = ["like", "dislike", "watchlist", "watched"]
up_rows = []
up_used = set()
for uid in user_ids:
    # жанровые предпочтения
    for gid in random.sample(genre_ids, random.randint(2, 4)):
        ptype = random.choice(["like", "dislike"])
        key = (uid, "genre", gid, ptype)
        if key not in up_used:
            up_rows.append({"user_id": uid, "genre_id": gid, "film_id": None, "preference_type": ptype})
            up_used.add(key)
    # фильмовые предпочтения
    for fid in random.sample(film_ids, random.randint(3, 6)):
        ptype = random.choice(pref_types)
        key = (uid, "film", fid, ptype)
        if key not in up_used:
            up_rows.append({"user_id": uid, "genre_id": None, "film_id": fid, "preference_type": ptype})
            up_used.add(key)
insert("user_preference", up_rows)
print(f"   {len(up_rows)} предпочтений")

print("\n✅ Seed completed!")
print(f"   Стран: {len(country_ids)}, Городов: {len(city_ids)}, Жанров: {len(genre_ids)}")
print(f"   Фильмов: {len(film_ids)}, Персон: {len(person_ids)}")
print(f"   Пользователей: {len(user_ids)}, Устройств: {len(device_ids)}")
print(f"   Просмотров: {len(view_rows)}, Рецензий: {len(review_ids)}")
print(f"   Фестивалей: {len(festival_ids)}, Наград: {len(award_ids)}")
print(f"\n   Admin user: user1@filmdb.example / password123")
