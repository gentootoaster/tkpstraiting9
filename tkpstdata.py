import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext, CallbackQueryHandler
from datetime import datetime, time as dt_time
import pytz
import asyncio
import json
import os
import logging

TOKEN = '7413686501:AAElURaHJvQTodFF253xqEN6sbiCQfSEVC8'
CHAT_IDS_FILE = 'chat_ids.json'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def get_links(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Ошибка при загрузке страницы :( - {e}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    links = [urljoin(url, link['href']) for link in soup.find_all('a', href=True)]
    return links

def search_name_on_page(url, name):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Ошибка при загрузке страницы :( - {e}")
        return False
    
    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.get_text()
    if name in text:
        for row in soup.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) > 2: 
                name_cell = cells[2].get_text()
                if name in name_cell:
                    result = (f"Информация:\n"
                              f"Рейтинг: {cells[0].get_text()}\n"
                              f"Какая-то лажа: {cells[1].get_text()}\n"
                              f"Имя: {cells[2].get_text()}\n"
                              f"Доки: {cells[3].get_text()}\n"
                              f"Средний балл: {cells[4].get_text()}")
                    return result
    return f"Имя '{name}' не найдено на странице."

async def send_telegram_message(chat_id, token, message):
    bot = Bot(token=token)
    try:
        await bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения :( {e}")

async def job(context: CallbackContext):
    base_url = 'https://tkpst.ru/applicants/rating9/'
    name_to_search = 'Лобачев Арсений Сергеевич'
    result = search_name_on_page(base_url, name_to_search)
    
    chat_ids = load_chat_ids()
    if chat_ids:
        for chat_id in chat_ids:
            await send_telegram_message(chat_id, TOKEN, result)
    else:
        logger.info("Нет юзеров для отправки")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    save_chat_id(chat_id)
    await update.message.reply_text("Бим-бам-бом...")
    await job(context)

def load_chat_ids():
    try:
        if os.path.exists(CHAT_IDS_FILE):
            with open(CHAT_IDS_FILE, 'r') as f:
                chat_ids = json.load(f)
                if not isinstance(chat_ids, list):
                    chat_ids = []
        else:
            chat_ids = []
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Ошибка при загрузке файла chat_ids.json: {e}")
        chat_ids = []
    return chat_ids

def save_chat_id(chat_id):
    chat_ids = load_chat_ids()
    if chat_id not in chat_ids:
        chat_ids.append(chat_id)
        with open(CHAT_IDS_FILE, 'w') as f:
            json.dump(chat_ids, f)

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))

    timezone = pytz.timezone('Asia/Yekaterinburg')  
    target_time = timezone.localize(datetime.strptime("20:05", "%H:%M")).time()

    application.job_queue.run_daily(job, time=dt_time(hour=target_time.hour, minute=target_time.minute, tzinfo=timezone))
    
    logger.info("Пим-бам-бум...")
    application.run_polling()

if __name__ == '__main__':
    main()