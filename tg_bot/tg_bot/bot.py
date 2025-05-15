from shared.logging_config import setup_logger
from os import getenv

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LinkPreviewOptions,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    Defaults,
    MessageHandler,
    filters,
)
from .usecase import (
    add_to_favorites,
    check_user,
    get_cafe,
    get_favorites,
    get_full_msg,
    get_new_cafes,
    get_short_msg,
    is_in_favorites,
    remove_from_favorites,
)

from shared.models.db import database

TG_BOT_TOKEN = getenv("TG_BOT_TOKEN")

logger = setup_logger()
# ---------------------------------------------------------------------------


def get_main_menu():
    return ReplyKeyboardMarkup([["Избранное", "Обновить"]], resize_keyboard=True)


def get_keyboard(expanded: bool):
    if expanded:
        keyboard = [[InlineKeyboardButton(">>> Раскрыть", callback_data="collapse")]]
    else:
        keyboard = [[InlineKeyboardButton("<<<", callback_data="expand")]]
    return InlineKeyboardMarkup(keyboard)


def get_compact_buttons(cafe):
    keyboard = [[InlineKeyboardButton("Подробнее >>>", callback_data=f"expand:{cafe.id}")]]
    return InlineKeyboardMarkup(keyboard)


def get_extended_buttons(cafe_id, in_favorites):
    toggle_text = "Добавить в избранное"
    if in_favorites:
        toggle_text = "Удалить из избранного"

    keyboard = [
        [
            InlineKeyboardButton("<<<", callback_data=f"collapse:{str(cafe_id)}"),
            InlineKeyboardButton(toggle_text, callback_data=f"toggle_fav:{str(cafe_id)}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def show_item(update: Update, context: ContextTypes.DEFAULT_TYPE, cafe):
    await update.message.reply_text(
        await get_short_msg(cafe),
        reply_markup=get_compact_buttons(cafe),
    )


# ---------------------------------------------------------------------------


async def expand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cafe_id = int(query.data.split(":")[1])

    in_favorites = await is_in_favorites(query.from_user.id, cafe_id)
    await query.edit_message_text(
        await get_full_msg(cafe_id, in_favorites),
        reply_markup=get_extended_buttons(cafe_id, in_favorites),
    )


async def collapse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cafe_id = int(query.data.split(":")[1])
    cafe = await get_cafe(cafe_id)

    await query.edit_message_text(await get_short_msg(cafe), reply_markup=get_compact_buttons(cafe))


async def toggle_fav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cafe_id = int(query.data.split(":")[1])
    tg_user_id = query.from_user.id

    in_favorites = await is_in_favorites(tg_user_id, cafe_id)

    if in_favorites and await remove_from_favorites(tg_user_id, cafe_id):
        in_favorites = False
        await query.edit_message_text(
            await get_full_msg(cafe_id, in_favorites),
            reply_markup=get_extended_buttons(cafe_id, in_favorites),
        )

    elif (not in_favorites) and await add_to_favorites(tg_user_id, cafe_id):
        in_favorites = True
        await query.edit_message_text(
            await get_full_msg(cafe_id, in_favorites),
            reply_markup=get_extended_buttons(cafe_id, in_favorites),
        )


# ---------------------------------------------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    await check_user(user_id, username)
    await update.message.reply_text(
        "Добро пожаловать!\n Выберите действие:", reply_markup=get_main_menu()
    )


async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cafes = await get_favorites(update.message.from_user.id)
    if not cafes:
        await update.message.reply_text("В избранном пока ничего нет!")
    else:
        for cafe in cafes:
            await show_item(update, context, cafe)


async def show_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cafes = await get_new_cafes(update.message.from_user.id)

    if not cafes:
        await update.message.reply_text("Ничего нового!")
    else:
        for cafe in cafes:
            await show_item(update, context, cafe)


# ---------------------------------------------------------------------------
async def on_startup(application: Application) -> None:
    await database.connect()


async def on_shutdown(application: Application) -> None:
    await database.disconnect()


# --------------------------------------------------------------------------

if __name__ == "__main__":
    defaults = Defaults(
        parse_mode=ParseMode.HTML, link_preview_options=LinkPreviewOptions(is_disabled=True)
    )

    app = (
        Application.builder()
        .token(TG_BOT_TOKEN)
        .defaults(defaults)
        .post_init(on_startup)
        .post_shutdown(on_shutdown)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text("Избранное"), show_favorites))
    app.add_handler(MessageHandler(filters.Text("Обновить"), show_new))

    app.add_handler(CallbackQueryHandler(expand, pattern=r"^expand:\d+$"))
    app.add_handler(CallbackQueryHandler(collapse, pattern=r"^collapse:\d+$"))
    app.add_handler(CallbackQueryHandler(toggle_fav, pattern=r"^toggle_fav:\d+$"))

    app.run_polling()
