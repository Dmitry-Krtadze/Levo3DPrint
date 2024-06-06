import os
import re
import logging
from tempfile import NamedTemporaryFile
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, \
    ContextTypes, ConversationHandler
from telegram.error import BadRequest, TimedOut, NetworkError

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токены и ID чата
TOKEN_RECEIVER = '7001703443:AAElOxcHkz5typgolEqk64_l6QP-mItx5T8'
TOKEN_FORWARDER = '7332798600:AAGnnjy_jVsk71rSMIon3ynM8ZuYmGf6YkE'
CHAT_ID_FORWARDER = '1061513902'

# Создание экземпляра бота-пересылателя
forwarder_bot = Bot(TOKEN_FORWARDER)

# Определение состояний
ASK_LINK_OR_FILE = 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("Продовжити", callback_data='continue')],
        [InlineKeyboardButton("Закрити", callback_data='close')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = (
        'Привіт робокотик ! 👋\n'
        'Вирішив замовити друк ? 😉\n\n'
        'Ознайомся з інструкцією:\n'
        '1. Тицяємо "Продовжити"  👉\n'
        '2.1. Вставляємо посилання з сайту <a href="https://www.thingiverse.com/">thingiverse.com</a>  🌐\n'
        '2.2 Або завантаж файл у форматі STL / OBJ\n'
        '3. Очікуй на свою модель😍'
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')
    return ASK_LINK_OR_FILE


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == 'continue':
        await query.edit_message_text(
            text="Введіть посилання на модель з сайту Thingiverse або надішліть файл у форматі STL або OBJ.")
        return ASK_LINK_OR_FILE
    elif query.data == 'close':
        await query.edit_message_text(text="Заявка скасована.")
        return ConversationHandler.END


async def handle_link_or_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message
    user_info = f'Користувач: @{message.from_user.username}' if message.from_user.username else f'Користувач: {message.from_user.full_name}'

    if message.document:
        file = message.document
        logger.info(f'Received file: {file.file_name}, MIME type: {file.mime_type}')
        if file.mime_type in ['application/vnd.ms-pki.stl', 'application/octet-stream', 'application/sla', 'model/stl',
                              'application/x-obj']:
            try:
                # Получение файла
                new_file = await file.get_file()
                file_path = new_file.file_path

                # Скачивание файла и сохранение во временное хранилище
                with NamedTemporaryFile(delete=False) as tmp_file:
                    await new_file.download_to_drive(custom_path=tmp_file.name)
                    tmp_file_path = tmp_file.name

                # Отправка файла
                with open(tmp_file_path, 'rb') as f:
                    input_file = InputFile(f, filename=file.file_name)
                    await forwarder_bot.send_document(chat_id=CHAT_ID_FORWARDER, document=input_file, caption=user_info)

                # Удаление временного файла
                os.remove(tmp_file_path)

                await message.reply_text('Файл прийнято і відправлено на обробку.')
                await start(update, context)
                return ASK_LINK_OR_FILE
            except (BadRequest, TimedOut, NetworkError) as e:
                logger.error(f"Error sending document: {e}")
                await message.reply_text('Сталася помилка при відправці файлу. Спробуйте знову.')
                return ASK_LINK_OR_FILE
        else:
            await message.reply_text('Будь ласка, надішліть файл у форматі STL або OBJ.')
            return ASK_LINK_OR_FILE

    elif message.text:
        link = message.text
        logger.info(f'Received link: {link}')
        if re.match(r'^https://www\.thingiverse\.com/.+', link):
            try:
                await forwarder_bot.send_message(chat_id=CHAT_ID_FORWARDER, text=f'{user_info}\nПосилання: {link}')
                await message.reply_text('Посилання прийнято і відправлено на обробку.')
                await start(update, context)
                return ASK_LINK_OR_FILE
            except (BadRequest, TimedOut, NetworkError) as e:
                logger.error(f"Error sending link: {e}")
                await message.reply_text('Сталася помилка при відправці посилання. Спробуйте знову.')
                return ASK_LINK_OR_FILE
        else:
            await message.reply_text('Будь ласка, надішліть посилання з сайту Thingiverse.')
            return ASK_LINK_OR_FILE


def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update.effective_message:
        text = "Сталася помилка. Спробуйте знову пізніше."
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def main() -> None:
    application = ApplicationBuilder().token(TOKEN_RECEIVER).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_LINK_OR_FILE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link_or_file),
                MessageHandler(filters.Document.ALL, handle_link_or_file),
            ],
        },
        fallbacks=[CallbackQueryHandler(button)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button, pattern='^(continue|close)$'))
    application.add_error_handler(error_handler)

    application.run_polling()


if __name__ == '__main__':
    main()
