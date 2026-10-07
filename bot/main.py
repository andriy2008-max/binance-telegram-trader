"""Entrypoint for Binance Signal Trader Telegram bot."""

import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, ApplicationBuilder

from bot.handlers import error_handler, register_handlers, set_bot_commands

load_dotenv()

logging.basicConfig(
    format="%(asctime)s %(name)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)

# Не даємо httpx виводити Telegram token у Railway Logs.
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def on_startup(application: Application) -> None:
    await set_bot_commands(application)


def build_application() -> Application:
    token = os.getenv("BOT_TOKEN", "").strip()

    if not token:
        raise RuntimeError("BOT_TOKEN is not set in Railway Variables.")

    application = (
        ApplicationBuilder()
        .token(token)
        .post_init(on_startup)
        .build()
    )

    register_handlers(application)
    application.add_error_handler(error_handler)

    return application


def main() -> None:
    application = build_application()

    logger.info(
        "Binance Signal Trader started in SIMULATION MODE."
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
