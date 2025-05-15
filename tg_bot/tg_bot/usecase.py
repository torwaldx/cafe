import decimal
from shared.models.models import User, Establishment, Favorite

NEW_CAFES_LIMIT = 10
MIN_REVIEWS = 150
MIN_RATING = 4.8


async def check_user(tg_user_id: int, tg_user_name=None):
    # Проверяем и добавляем пользователя в БД
    return await User.objects.get_or_create(
        tg_user_id=tg_user_id, _defaults={"tg_user_name": tg_user_name}
    )


async def get_cafe(cafe_id):
    return await Establishment.objects.get(id=cafe_id)


async def get_new_cafes(tg_user_id: int):
    user, is_created = await User.objects.get_or_create(tg_user_id=tg_user_id)

    last_update_check = user.last_update_check
    new_cafes = []

    if is_created or last_update_check is None:
        new_cafes = (
            await Establishment.objects.filter(
                (Establishment.rating >= MIN_RATING) & (Establishment.reviews_count >= MIN_REVIEWS)
            )
            .order_by(["-rating", "-reviews_count", "-created"])
            .limit(NEW_CAFES_LIMIT)
            .all()
        )
    else:
        new_cafes = (
            await Establishment.objects.filter(
                (Establishment.rating >= MIN_RATING)
                & (Establishment.reviews_count >= MIN_REVIEWS)
                & (Establishment.created > last_update_check)
            )
            .order_by(["-rating", "-reviews_count", "-created"])
            .limit(NEW_CAFES_LIMIT)
            .all()
        )

    if new_cafes:
        user.last_update_check = max(new_cafes, key=lambda cafe: cafe.created).created

        await user.update()

    return new_cafes


async def get_favorites(tg_user_id):
    user, _ = await User.objects.get_or_create(tg_user_id=tg_user_id)

    favorites = (
        await Favorite.objects.filter(Favorite.user.id == user.id)
        .select_related("establishment")
        .all()
    )

    cafes = [fav.establishment for fav in favorites]

    return cafes


async def add_to_favorites(tg_user_id, cafe_id):
    try:
        user, _ = await User.objects.get_or_create(tg_user_id=tg_user_id)
        await Favorite.objects.update_or_create(user=user, establishment=cafe_id)
    except Exception:
        return False
    return True


async def remove_from_favorites(tg_user_id, cafe_id):
    try:
        user, _ = await User.objects.get_or_create(tg_user_id=tg_user_id)
        await Favorite.objects.delete(user=user, establishment=cafe_id)
    except Exception:
        return False
    return True


async def is_in_favorites(tg_user_id, cafe_id):
    user, _ = await User.objects.get_or_create(tg_user_id=tg_user_id)

    return await Favorite.objects.filter(
        (Favorite.user.id == user.id) & (Favorite.establishment.id == cafe_id)
    ).exists()


async def get_short_msg(cafe: Establishment):
    categories = await cafe.categories.order_by("establishmentcategory__sort_order").all()
    category_name = categories[0].name if categories else ""
    return f"{category_name.capitalize()} <b>«{cafe.y_name}»</b>"


def get_reviews_count(cafe: Establishment) -> str:
    count = cafe.reviews_count
    if count >= 300:
        return f"  —  {str(count // 100)}00+ отзывов"
    if count >= 10:
        return f"  —  {str(count // 10)}0+ отзывов"
    return ""


async def get_full_msg(cafe_id, in_favorites=False):
    cafe = await get_cafe(cafe_id)

    # Устанавливает точность до 1 знака после запятой
    rating = cafe.rating.quantize(decimal.Decimal("1.0"), decimal.ROUND_HALF_UP)

    text = (
        await get_short_msg(cafe)
        + f"\n\n{cafe.gen_text}"
        + f"\n\n<b>Адрес:</b> {cafe.y_address}"
        + f"\n\n<b>Рейтинг: {rating}{get_reviews_count(cafe)}</b>"
        + f'\n\n<a href="https://yandex.ru/maps/org/{cafe.yandex_id}/">[<u><b>Перейти на сайт</b></u>]</a>'
        + ("  —  [⭐ <b>В избранном</b>]" if in_favorites else "")
    )
    return text


# ⭐ 🔄
