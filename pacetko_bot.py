import random
import json
import os
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "pacetko_data.json"

# --- СТАЛКЕРСЬКІ ФРАЗИ ---
FEED_PHRASES_GAIN = [
    "Чікі-брики — і в дамки! {name} тепер на {change} кг товстіше.",
    "Горілка з ковбасою зайшла добре. {name} +{change} кг.",
    "Ну шо, мужик, {name} сьогодні добре під'їв (+{change} кг).",
    "Пацєтко від щастя аж похрюкує (+{change} кг)."
]
FEED_PHRASES_LOSS = [
    "Ой, аномалія сальце висмоктала... {name} -{loss} кг.",
    "{name} поглянув на кабана... і схуд на {loss} кг.",
    "Щось не те з чікі-брикі... {name} -{loss} кг."
]
FEED_PHRASES_ZERO = [
    "{name} поїв, але вага стоїть. Дивина!",
    "Ні туди, ні сюди... {name} не змінив вагу."
]

PET_PHRASES = [
    "Ооо, {name} аж прищулився від задоволення!",
    "{name} тихенько похрюкує — йому подобається!",
    "Тепер {name} любить тебе ще більше.",
    "Ах ти ж пустун, чухаєш {name} за вушком!"
]

REPLY_PHRASES = [
    "Чікі-брики — і в дамки!",
    "Мужик, в тебе є батон?",
    "Аномалія тут, будь обережний...",
    "Хрю-хрю, сталкер!",
    "Горілка з ковбасою — моє паливо!",
    "Пацєтко готовий до пригод."
]

# --- Завантаження / збереження даних ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# --- Допоміжна функція ---
def get_or_create_pig(chat_id, user_id):
    if chat_id not in data:
        data[chat_id] = {}
    if user_id not in data[chat_id]:
        data[chat_id][user_id] = {
            "name": f"Пацєтко_{user_id[-4:]}",
            "weight": 10,
            "last_feed": 0
        }
    return data[chat_id][user_id]

# --- Команди ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🐷 Ласкаво просимо у світ П.А.Ц.Є.Т.К.О. 2!\n"
        "Вирощуй свою пацєтку, годуй її чікі-брикі та бережи від аномалій."
    )
    await update.message.reply_text(text)

async def feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)

    pig = get_or_create_pig(chat_id, user_id)
    now = time.time()

    if now - pig["last_feed"] < 12 * 3600:
        remaining = int((12 * 3600 - (now - pig["last_feed"])) / 3600)
        await update.message.reply_text(f"⏳ {pig['name']} ще переварює. Чекай {remaining} год.")
        return

    change = random.randint(-40, 40)
    pig["weight"] = max(1, pig["weight"] + change)
    pig["last_feed"] = now

    if change > 0:
        msg = random.choice(FEED_PHRASES_GAIN).format(name=pig['name'], change=change)
    elif change < 0:
        msg = random.choice(FEED_PHRASES_LOSS).format(name=pig['name'], loss=-change)
    else:
        msg = random.choice(FEED_PHRASES_ZERO).format(name=pig['name'])

    await update.message.reply_text(msg + f"\nВага: {pig['weight']} кг.")
    save_data(data)

async def name_pig(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)

    if not context.args:
        await update.message.reply_text("❌ Напиши ім'я після команди. Приклад: /name Хрюня")
        return

    new_name = " ".join(context.args)
    pig = get_or_create_pig(chat_id, user_id)
    pig["name"] = new_name
    save_data(data)

    await update.message.reply_text(f"✅ Твоя пацєтка тепер зветься: {new_name}")

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

async def pet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)

    pig = get_or_create_pig(chat_id, user_id)
    msg = random.choice(PET_PHRASES).format(name=pig['name'])

    # 5% шанс на бонусну вагу
    if random.random() <= 0.05:
        gain = random.randint(1, 3)
        pig["weight"] += gain
        msg += f"\n🎉 {pig['name']} набрав {gain} кг сальця!"
        save_data(data)

    await update.message.reply_text(msg)

# --- Відповідь на згадки ---
async def reply_mentions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "пацєтко" in text or "pacetko" in text:
        await update.message.reply_text(random.choice(REPLY_PHRASES))
    
# --- Запуск бота ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("feed", feed))
app.add_handler(CommandHandler("name", name_pig))
app.add_handler(CommandHandler("top", top))
app.add_handler(CommandHandler("pet", pet))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_mentions))

print("Бот запущений!")

app.run_polling()

