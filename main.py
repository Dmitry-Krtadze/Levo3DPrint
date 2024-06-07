from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# Ваш токен бота-пересылателя и другие параметры
TOKEN_RECEIVER = '7001703443:AAElOxcHkz5typgolEqk64_l6QP-mItx5T8'
TOKEN_FORWARDER = '7332798600:AAGnnjy_jVsk71rSMIon3ynM8ZuYmGf6YkE'
CHAT_ID_FORWARDER = '1061513902'

def start(update: Update, context):
    update.message.reply_text(
        "Привіт робокотик ! 👋\n"
        "Вирішив замовити друк ? 😉\n\n"
        "Ознайомся з інструкцією:\n"
        "1. Тицяємо \"Продовжити\"  👉\n"
        "2.1. Вставляємо посилання з сайту <a href='https://www.thingiverse.com/'>thingiverse.com</a>  🌐\n"
        "2.2 Або завантаж файл у форматі STL / OBJ\n"
        "3. Очікуй на свою модель😍", 
        parse_mode='HTML'
    )

def handle_link_or_file(update: Update, context):
    user = update.message.from_user
    if update.message.document:
        file = update.message.document
        if file.mime_type in ["model/stl", "model/obj"]:
            forward_message = f"Отримано файл від @{user.username or user.full_name}:\n{file.file_name}"
            forwarder_bot.send_document(chat_id=CHAT_ID_FORWARDER, document=file.file_id)
            update.message.reply_text("Файл отримано та надіслано на обробку.")
        else:
            update.message.reply_text("Невірний формат файлу. Будь ласка, надішліть STL або OBJ файл.")
    elif update.message.text and update.message.text.startswith("https://www.thingiverse.com/"):
        link = update.message.text
        forward_message = f"Отримано посилання від @{user.username or user.full_name}:\n{link}"
        forwarder_bot.send_message(chat_id=CHAT_ID_FORWARDER, text=forward_message)
        update.message.reply_text("Посилання отримано та надіслано на обробку.")
    else:
        update.message.reply_text("Невірне посилання або формат файлу. Будь ласка, спробуйте ще раз.")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN_RECEIVER).build()

    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.ALL, handle_link_or_file)

    application.add_handler(start_handler)
    application.add_handler(message_handler)

    application.run_polling()
