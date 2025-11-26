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
        [InlineKeyboardButton("🔍 Поиск", callback_data='search')],
        [InlineKeyboardButton("📋 Заказы", callback_data='orders')],
        [InlineKeyboardButton("📞 Контакты", callback_data='contact')]
    ])

def catalog_kb():
    kb = [[InlineKeyboardButton(cat['name'], callback_data=f'cat_{cid}')] for cid, cat in CATALOG.items()]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data='main')])
    return InlineKeyboardMarkup(kb)

def category_kb(cat_id):
    cat = CATALOG[cat_id]
    kb = [[InlineKeyboardButton(name, callback_data=f'item_{cat_id}_{iid}')] for iid, name in cat['items'].items()]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data='catalog')])
    return InlineKeyboardMarkup(kb)

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    text = f"👋 Здравствуйте, {user.first_name}!\n\n<b>Автозапчасти Тула</b>\n\n✅ Доставка 1-3 часа\n✅ Гарантия\n\nВыберите действие:"
    update.message.reply_text(text, parse_mode='HTML', reply_markup=main_kb())

def button(update: Update, context: CallbackContext):
    q = update.callback_query
    q.answer()
    data = q.data
    uid = q.from_user.id
    
    if data == 'main':
        q.edit_message_text("Выберите действие:", reply_markup=main_kb())
    elif data == 'catalog':
        q.edit_message_text("📦 <b>Каталог</b>\n\nВыберите категорию:", parse_mode='HTML', reply_markup=catalog_kb())
    elif data.startswith('cat_'):
        cid = data.replace('cat_', '')
        q.edit_message_text(f"{CATALOG[cid]['name']}\n\nВыберите товар:", reply_markup=category_kb(cid))
    elif data.startswith('item_'):
        parts = data.split('_')
        item = CATALOG[parts[1]]['items'][parts[2]]
        user_data[uid] = {'item': item, 'waiting': True}
        q.edit_message_text(f"📦 <b>{item}</b>\n\nДля заказа отправьте:\n1. Имя\n2. Телефон\n3. Марка авто\n4. Год", parse_mode='HTML')
    elif data == 'search':
        q.edit_message_text("🔍 Отправьте артикул или VIN", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='main')]]))
        user_data[uid] = {'search': True}
    elif data == 'orders':
        ords = [o for o in load_orders() if o.get('user_id') == uid]
        text = "У вас нет заказов" if not ords else "📋 <b>Ваши заказы:</b>\n\n" + "\n".join([f"🆕 #{o['id']} - {o['parts']}\n{o['timestamp']}\n" for o in ords[-3:]])
        q.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='main')]]))
    elif data == 'contact':
        q.edit_message_text("📞 <b>Контакты</b>\n\n📱 +7 (4872) 123-456\n⏰ Пн-Пт: 9-19", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='main')]]))

def msg(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    text = update.message.text
    
    if uid not in user_data:
        user_data[uid] = {}
    
    if user_data[uid].get('waiting'):
        lines = text.strip().split('\n')
        if len(lines) >= 3:
            order = add_order({
                'name': lines[0],
                'phone': lines[1],
                'car': f"{lines[2]} {lines[3] if len(lines)>3 else ''}",
                'parts': user_data[uid].get('item', ''),
                'user_id': uid
            })
            update.message.reply_text(f"✅ Заказ #{order['id']} оформлен!", parse_mode='HTML', reply_markup=main_kb())
            try:
                context.bot.send_message(ADMIN_ID, f"🆕 ЗАКАЗ #{order['id']}\n\n{order['customer_name']}\n{order['phone']}\n{order['car_model']}\n{order['parts']}")
            except:
                pass
            user_data[uid]['waiting'] = False
        else:
            update.message.reply_text("❌ Укажите все данные")
    elif user_data[uid].get('search'):
        update.message.reply_text(f"🔍 Ищу: {text}\n\nМенеджер ответит в течение 10 минут", reply_markup=main_kb())
        try:
            context.bot.send_message(ADMIN_ID, f"🔍 Поиск: {text}\nОт: {update.effective_user.first_name}")
        except:
            pass
        user_data[uid]['search'] = False
    else:
        update.message.reply_text("Используйте кнопки меню 👇", reply_markup=main_kb())

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден в переменных окружения!")
        return
    
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, msg))
    
    print("✅ Бот запущен!")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
