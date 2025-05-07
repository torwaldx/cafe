from datetime import datetime
from decimal import Decimal
from typing import Optional

import ormar
from sqlalchemy import func

from .db import ormar_base_config


class Category(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255, nullable=True)


class EstablishmentCategory(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="establishments_categories")

    id: int = ormar.Integer(primary_key=True)
    sort_order: int = ormar.Integer(nullable=True)


class Establishment(ormar.Model):
    ormar_config = ormar_base_config.copy()

    id: int = ormar.Integer(primary_key=True)
    yandex_id: int = ormar.BigInteger()
    y_name: str = ormar.String(max_length=128)
    y_address: str = ormar.String(max_length=128)
    latitude: Decimal = ormar.Decimal(max_digits=9, decimal_places=6)
    longitude: Decimal = ormar.Decimal(max_digits=9, decimal_places=6)
    rating: Decimal = ormar.Decimal(max_digits=3, decimal_places=2)
    reviews_count: int = ormar.Integer()
    created: datetime = ormar.DateTime(server_default=func.now())
    updated: datetime = ormar.DateTime(server_default=func.now(), server_onupdate=func.now())
    y_text: str = ormar.Text(nullable=True)
    gen_text: str = ormar.Text(nullable=True)
    categories = ormar.ManyToMany(Category, through=EstablishmentCategory)


class Source(ormar.Model):
    ormar_config = ormar_base_config.copy()
    id: int = ormar.Integer(primary_key=True)
    source_type: str = ormar.String(max_length=64)
    is_active: bool = ormar.Boolean(default=True, server_default="1")
    is_deleted: bool = ormar.Boolean(default=False, server_default="0")
    processed_at: datetime = ormar.DateTime(nullable=True)


class Tg_Channel(ormar.Model):
    ormar_config = ormar_base_config.copy()

    id: int = ormar.Integer(primary_key=True)
    tg_chat_id: int = ormar.BigInteger(nullable=True)
    tg_name: str = ormar.String(max_length=100, nullable=True)
    tg_link: str = ormar.String(max_length=100, nullable=True)
    last_message_id: int = ormar.Integer(default=1, server_default="1")
    source: Source = ormar.ForeignKey(
        Source,
        ondelete="RESTRICT",
        on_update="CASCADE",
    )


class Instagram_Account(ormar.Model):
    ormar_config = ormar_base_config.copy()

    id: int = ormar.Integer(primary_key=True)
    inst_user_id: int = ormar.BigInteger(nullable=True)
    inst_username: str = ormar.String(max_length=100)
    last_message_time: int = ormar.Integer(default=0, server_default="0")
    source: Source = ormar.ForeignKey(
        Source,
        ondelete="RESTRICT",
        on_update="CASCADE",
    )


class Message(ormar.Model):
    ormar_config = ormar_base_config.copy()

    id: int = ormar.Integer(primary_key=True)
    source: Source = ormar.ForeignKey(
        Source,
        ondelete="RESTRICT",
        on_update="CASCADE",
    )
    external_id: str = ormar.String(max_length=128)
    text: str = ormar.Text()
    estimated_name: str = ormar.String(max_length=128, nullable=True)
    estimated_address: str = ormar.String(max_length=128, nullable=True)
    estimated_category: str = ormar.String(max_length=128, nullable=True)
    establishment: Optional[Establishment] = ormar.ForeignKey(
        Establishment,
        nullable=True,
        ondelete="SET NULL",
        onupdate="CASCADE",
    )
    attempt_count: int = ormar.Integer(default=0, server_default="0")
    created_at: datetime = ormar.DateTime(server_default=func.now())
    processed_at: datetime = ormar.DateTime(nullable=True)


class Y_Image(ormar.Model):
    ormar_config = ormar_base_config.copy()

    id: int = ormar.Integer(primary_key=True)
    link: str = ormar.String(max_length=256)
    establishment: Establishment = ormar.ForeignKey(
        Establishment,
        ondelete="CASCADE",
        onupdate="CASCADE",
    )


class User(ormar.Model):
    ormar_config = ormar_base_config.copy()

    id: int = ormar.Integer(primary_key=True)
    tg_user_id: int = ormar.BigInteger(unique=True)
    tg_user_name: str = ormar.String(max_length=255, nullable=True)
    last_update_check: datetime = ormar.DateTime(nullable=True)
    created: datetime = ormar.DateTime(server_default=func.now())


class Favorite(ormar.Model):
    ormar_config = ormar_base_config.copy()

    id: int = ormar.Integer(primary_key=True)
    user: User = ormar.ForeignKey(
        User,
        ondelete="CASCADE",
        onupdate="CASCADE",
    )
    establishment: Establishment = ormar.ForeignKey(
        Establishment,
        ondelete="CASCADE",
        onupdate="CASCADE",
    )
    added_at: datetime = ormar.DateTime(server_default=func.now())
    # deleted_at: datetime = ormar.DateTime(nullable=True)

