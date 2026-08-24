"""
services/bot_runtime.py — Referensi global Application Telegram bot.
====================================================================
main.py menginjeksi Application via set_bot_app() setelah dibuat,
sehingga modul lain (detector, job scheduler, handler) bisa mengirim
pesan Telegram tanpa saling mengimpor instance.
"""

import logging

logger = logging.getLogger(__name__)

bot_app = None


def set_bot_app(app):
    global bot_app
    bot_app = app
    logger.info("Bot application reference set")
