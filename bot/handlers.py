"""Telegram handlers for Binance Signal Trader — SIMULATION MODE."""

import logging

from telegram import ReplyKeyboardMarkup, Update
from telegram.error import Conflict, NetworkError, TimedOut
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


logger = logging.getLogger(__name__)

# Keys used by bot.main for optional shared backends.
DB_KEY = "db"
REDIS_KEY = "redis"

# Temporary simulated positions.
# Nothing here is sent to Binance.
POSITIONS = {}

BOT_COMMANDS = (
    ("start", "Open trading menu"),
    ("long", "Open simulated LONG"),
    ("short", "Open simulated SHORT"),
    ("close", "Close simulated position"),
    ("status", "Show simulated positions"),
    ("help", "Show commands"),
)

MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📊 STATUS", "❌ CLOSE ALL"],
        ["ℹ️ HELP"],
    ],
    resize_keyboard=True,
)

HELP_TEXT = """🤖 Binance Signal Trader

⚠️ SIMULATION MODE — no real orders.

Commands:

/long BTCUSDT 10
Open simulated LONG for 10 USDT.

/short BTCUSDT 10
Open simulated SHORT for 10 USDT.

/close BTCUSDT
Close simulated position.

/status
Show open simulated positions.

Examples:
/long BTCUSDT 10
/short ETHUSDT 20
/close BTCUSDT
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message

    if message is None:
        return

    await message.reply_text(
        "🤖 Binance Signal Trader is running.\n\n"
        "🧪 SIMULATION MODE\n"
        "No orders are being sent to Binance.\n\n"
        "Type /help to see trading commands.",
        reply_markup=MAIN_MENU_KEYBOARD,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message

    if message is not None:
        await message.reply_text(HELP_TEXT)


async def long_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await open_position(update, context, "LONG")


async def short_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await open_position(update, context, "SHORT")


async def open_position(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    side: str,
) -> None:
    message = update.effective_message

    if message is None:
        return

    if len(context.args) != 2:
        await message.reply_text(
            f"Usage:\n/{side.lower()} BTCUSDT 10"
        )
        return

    symbol = context.args[0].upper()

    try:
        amount = float(context.args[1])
    except ValueError:
        await message.reply_text("❌ Amount must be a number.")
        return

    if amount <= 0:
        await message.reply_text("❌ Amount must be greater than 0.")
        return

    POSITIONS[symbol] = {
        "side": side,
        "amount": amount,
    }

    emoji = "🟢" if side == "LONG" else "🔴"

    await message.reply_text(
        f"{emoji} SIMULATED {side}\n\n"
        f"Symbol: {symbol}\n"
        f"Amount: {amount:.2f} USDT\n\n"
        "⚠️ No Binance order was placed."
    )


async def close_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message

    if message is None:
        return

    if len(context.args) != 1:
        await message.reply_text(
            "Usage:\n/close BTCUSDT"
        )
        return

    symbol = context.args[0].upper()

    position = POSITIONS.pop(symbol, None)

    if position is None:
        await message.reply_text(
            f"ℹ️ No simulated position for {symbol}."
        )
        return

    await message.reply_text(
        f"✅ SIMULATED POSITION CLOSED\n\n"
        f"{symbol}\n"
        f"{position['side']}\n"
        f"{position['amount']:.2f} USDT"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message

    if message is None:
        return

    if not POSITIONS:
        await message.reply_text(
            "📊 No simulated positions are open."
        )
        return

    lines = ["📊 SIMULATED POSITIONS\n"]

    for symbol, position in POSITIONS.items():
        emoji = "🟢" if position["side"] == "LONG" else "🔴"

        lines.append(
            f"{emoji} {symbol}\n"
            f"{position['side']} | {position['amount']:.2f} USDT\n"
        )

    await message.reply_text(
        "\n".join(lines)
    )


async def close_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message

    if message is None:
        return

    count = len(POSITIONS)

    POSITIONS.clear()

    await message.reply_text(
        f"❌ Closed {count} simulated position(s)."
    )


async def menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message

    if message is None or not message.text:
        return

    text = message.text.strip()

    if text == "📊 STATUS":
        await status_command(update, context)

    elif text == "❌ CLOSE ALL":
        await close_all(update, context)

    elif text == "ℹ️ HELP":
        await help_command(update, context)


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message

    if message is not None:
        await message.reply_text(
            "❓ Unknown command.\nType /help."
        )


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    error = context.error

    if isinstance(
        error,
        (Conflict, NetworkError, TimedOut),
    ):
        logger.warning(
            "Transient Telegram error: %s",
            error,
        )
        return

    logger.exception(
        "Error while processing update: %s",
        update,
        exc_info=error,
    )

    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, an error occurred while processing your message."
        )


async def set_bot_commands(application: Application) -> None:
    await application.bot.set_my_commands(
        BOT_COMMANDS
    )


def register_handlers(application: Application) -> None:
    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("long", long_command)
    )

    application.add_handler(
        CommandHandler("short", short_command)
    )

    application.add_handler(
        CommandHandler("close", close_command)
    )

    application.add_handler(
        CommandHandler("status", status_command)
    )

    application.add_handler(
        MessageHandler(
            filters.Regex(
                r"^(📊 STATUS|❌ CLOSE ALL|ℹ️ HELP)$"
            ),
            menu_button,
        )
    )

    application.add_handler(
        MessageHandler(
            filters.COMMAND,
            unknown_command,
        )
    )
