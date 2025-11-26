import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import json
from datetime import datetime

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '0'))

ORDERS_FILE = "orders.json"
user_data = {}

def load_orders():
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_orders(orders):
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

def add_order(order_data):
    orders = load_orders()
    order_id = len(orders) + 1001
    order = {
        'id': order_id,
        'customer_name': order_data.get('name', ''),
        'phone': order_data.get('phone', ''),
        'car_model': order_data.get('car', ''),
        'parts': order_data.get('parts', ''),
        'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'status': 'new',
        'user_id': order_data.get('user_id')
    }
    orders.append(order)
    save_orders(orders)
    return order

CATALOG = {
    'расходники': {
        'name': '🔧 Расходники',
        'items': {
            'oil': 'Масло 5W-30 (1200₽)',
            'filter': 'Фильтр масляный (350₽)',
            'spark': 'Свечи зажигания (250₽/шт)'
        }
    },
    'тормоза': {
        'name': '🛑 Тормоза',
        'items': {
            'pads': 'Колодки передние (1800₽)',
            'discs': 'Диски тормозные (2200₽)'
        }
    }
}

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Каталог", callback_data='catalog')],
        [InlineKeyboar
