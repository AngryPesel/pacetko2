import random
import json
import os
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "pacetko_data.json"

# Завантаження даних
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Збереження даних
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🐷 Ласкаво просимо у світ П.А.Ц.Є.Т.К.О. 2!\n"
        "Тут ти зможеш вирощувати свою пацєтку, "
        "годувати її чікі-бріками, запивати горілкою з ковбасою і батоном.\n"
        "Але почнемо з головного — догляду за своєю пацєткою!"
    )
    await update.message.reply_text(text)

# /feed
async def feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)

    if chat_id not in data:
        data[chat_id] = {}

    if user_id not in data[chat_id]:
        data[chat_id][user_id] = {
            "name": f"Пацєтко_{user_id[-4:]}",  # дефолтне ім'я
            "weight": 10,
            "last_feed": 0
        }

    pig = data[chat_id][user_id]
    now = time.time()

    if now - pig["last_feed"] < 12 * 3600:
        remaining = int((12 * 3600 - (now - pig["last_feed"])) / 3600)
        await update.message.reply_text(
            f"⏳ Твоя пацєтка вже ситенька. Почекай ще {remaining} год."
        )
        return

    change = random.randint(-40, 40)
    pig["weight"] = max(1, pig["weight"] + change)
    pig["last_feed"] = now

    if change > 0:
        await update.message.reply_text(
            f"🍞 Ти покормив {pig['name']}! Вона погладшала на {change} кг.\n"
            f"Тепер вага: {pig['weight']} кг."
        )
    elif change < 0:
        await update.message.reply_text(
            f"🥓 {pig['name']} щось не дуже засвоїла їжу і схудла на {-change} кг.\n"
            f"Тепер вага: {pig['weight']} кг."
        )
    else:
        await update.message.reply_text(
            f"🤷‍♂️ {pig['name']} поїла, але вага не змінилася.\n"
            f"Вага: {pig['weight']} кг."
        )

    save_data(data)

# /name
async def name_pig(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)

    if len(context.args) == 0:
        await update.message.reply_text("❌ Напиши ім'я після команди. Приклад: /name Хрюня")
        return

    new_name = " ".join(context.args)

    if chat_id not in data:
        data[chat_id] = {}
    if user_id not in data[chat_id]:
        data[chat_id][user_id] = {"name": new_name, "weight": 10, "last_feed": 0}

    data[chat_id][user_id]["name"] = new_name
    save_data(data)

    await update.message.reply_text(f"✅ Твоя пацєтка тепер зветься: {new_name}")

# /top
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)

    if chat_id not in data or not data[chat_id]:
        await update.message.reply_text("❌ У цьому чаті ще немає пацєток.")
        return

    sorted_pigs = sorted(data[chat_id].values(), key=lambda x: x["weight"], reverse=True)
    top_list = sorted_pigs[:10]

    text = "🏆 Топ 10 пацєток чату:\n"
    for i, pig in enumerate(top_list, 1):
        text += f"{i}. {pig['name']} — {pig['weight']} кг\n"

    await update.message.reply_text(text)

# Запуск бота
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("feed", feed))
app.add_handler(CommandHandler("name", name_pig))
app.add_handler(CommandHandler("top", top))

print("Бот запущений!")
app.run_polling()