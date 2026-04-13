from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, Numeric,
    ForeignKey, func
)
from app.database import Base


class Country(Base):
    __tablename__ = "country"
    country_id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)


class City(Base):
    __tablename__ = "city"
    city_id = Column(Integer, primary_key=True)
    country_id = Column(Integer, ForeignKey("country.country_id"), nullable=False)
    name = Column(String(100), nullable=False)


class AppUser(Base):
    __tablename__ = "app_user"
    user_id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100))
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    birth_date = Column(Date)
    gender = Column(String(20))
    country_id = Column(Integer, ForeignKey("country.country_id"))
    city_id = Column(Integer, ForeignKey("city.city_id"))
    avatar = Column(String(500))
    rating = Column(Numeric(5, 2), default=0)
    registration_date = Column(DateTime, server_default=func.current_timestamp())
    last_login = Column(DateTime)


class Person(Base):
    __tablename__ = "person"
    person_id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100))
    middle_name = Column(String(100))
    birth_date = Column(Date)
    birth_place = Column(String(255))
    country_id = Column(Integer, ForeignKey("country.country_id"))
    city_id = Column(Integer, ForeignKey("city.city_id"))
    biography = Column(Text)
    education = Column(Text)
    photo = Column(String(500))
    created_at = Column(DateTime, server_default=func.current_timestamp())


class PersonRole(Base):
    __tablename__ = "person_role"
    person_role_id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("person.person_id"), nullable=False)
    role = Column(String(100), nullable=False)


class Genre(Base):
    __tablename__ = "genre"
    genre_id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)


class Film(Base):
    __tablename__ = "film"
    film_id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    created_date = Column(Date)
    age_restriction = Column(String(10))
    average_rating = Column(Numeric(3, 2), default=0)
    added_at = Column(DateTime, server_default=func.current_timestamp())


class FilmGenre(Base):
    __tablename__ = "film_genre"
    film_genre_id = Column(Integer, primary_key=True)
    film_id = Column(Integer, ForeignKey("film.film_id"), nullable=False)
    genre_id = Column(Integer, ForeignKey("genre.genre_id"), nullable=False)


class FilmPerson(Base):
    __tablename__ = "film_person"
    film_person_id = Column(Integer, primary_key=True)
    film_id = Column(Integer, ForeignKey("film.film_id"), nullable=False)
    person_id = Column(Integer, ForeignKey("person.person_id"), nullable=False)
    role = Column(String(100), nullable=False)


class UserDevice(Base):
    __tablename__ = "user_device"
    device_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("app_user.user_id"), nullable=False)
    type = Column(String(50), nullable=False)
    model = Column(String(255))
    manufacturer = Column(String(100))
    operating_system = Column(String(100))
    os_version = Column(String(50))
    browser = Column(String(100))
    browser_version = Column(String(50))
    screen_resolution = Column(String(50))
    registration_date = Column(DateTime, server_default=func.current_timestamp())
    last_used_at = Column(DateTime)


class ViewHistory(Base):
    __tablename__ = "view_history"
    view_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("app_user.user_id"), nullable=False)
    film_id = Column(Integer, ForeignKey("film.film_id"), nullable=False)
    device_id = Column(Integer, ForeignKey("user_device.device_id"), nullable=False)
    viewed_at = Column(DateTime, server_default=func.current_timestamp())
    view_duration = Column(Integer)
    view_percent = Column(Numeric(5, 2))
    ip_address = Column(String(50))


class Review(Base):
    __tablename__ = "review"
    review_id = Column(Integer, primary_key=True)
    film_id = Column(Integer, ForeignKey("film.film_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("app_user.user_id"), nullable=False)
    review_text = Column(Text, nullable=False)
    film_rating = Column(Integer)
    likes_count = Column(Integer, default=0)
    dislikes_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime)


class ReviewRating(Base):
    __tablename__ = "review_rating"
    review_rating_id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey("review.review_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("app_user.user_id"), nullable=False)
    rating_type = Column(String(50), nullable=False)
    rated_at = Column(DateTime, server_default=func.current_timestamp())


class CriticReview(Base):
    __tablename__ = "critic_review"
    critic_review_id = Column(Integer, primary_key=True)
    film_id = Column(Integer, ForeignKey("film.film_id"), nullable=False)
    person_id = Column(Integer, ForeignKey("person.person_id"), nullable=False)
    publication_name = Column(String(255))
    title = Column(String(500))
    review_text = Column(Text, nullable=False)
    summary = Column(Text)
    rating = Column(Numeric(3, 1))
    published_at = Column(Date)
    source_url = Column(String(1000))
    views_count = Column(Integer, default=0)


class Festival(Base):
    __tablename__ = "festival"
    festival_id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    country_id = Column(Integer, ForeignKey("country.country_id"))
    city_id = Column(Integer, ForeignKey("city.city_id"))
    founded_year = Column(Integer)
    description = Column(Text)
    prestige_rating = Column(Numeric(3, 2))


class Award(Base):
    __tablename__ = "award"
    award_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    festival_id = Column(Integer, ForeignKey("festival.festival_id"), nullable=False)
    year = Column(Integer, nullable=False)
    film_id = Column(Integer, ForeignKey("film.film_id"))
    person_id = Column(Integer, ForeignKey("person.person_id"))
    category = Column(String(255))
    person_role = Column(String(100))
    status = Column(String(50), nullable=False)
    description = Column(Text)


class UserPreference(Base):
    __tablename__ = "user_preference"
    preference_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("app_user.user_id"), nullable=False)
    genre_id = Column(Integer, ForeignKey("genre.genre_id"))
    film_id = Column(Integer, ForeignKey("film.film_id"))
    preference_type = Column(String(50), nullable=False)
    added_at = Column(DateTime, server_default=func.current_timestamp())


# RBAC
class Role(Base):
    __tablename__ = "role"
    role_id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)


class Permission(Base):
    __tablename__ = "permission"
    permission_id = Column(Integer, primary_key=True)
    action = Column(String(50), nullable=False)
    resource = Column(String(100), nullable=False)
    description = Column(Text)


class RolePermission(Base):
    __tablename__ = "role_permission"
    role_id = Column(Integer, ForeignKey("role.role_id"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permission.permission_id"), primary_key=True)


class UserRole(Base):
    __tablename__ = "user_role"
    user_id = Column(Integer, ForeignKey("app_user.user_id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("role.role_id"), primary_key=True)
    assigned_at = Column(DateTime, server_default=func.current_timestamp())
