import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- SOZLAMALAR ---
BOT_TOKEN = "8821690561:AAHcRLiZonoc2wU5OQKym7c8MrbNgRHN-20"
ADMIN_ID = 5492502957
ADMIN_USERNAME = "@Javoh_1hacker"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# --- MA'LUMOTLAR BAZASI (SQLite) ---
conn = sqlite3.connect("music_bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    fullname TEXT,
    username TEXT,
    balance INTEGER DEFAULT 1000,
    total_paid INTEGER DEFAULT 0
)
""")
conn.commit()

def db_register_user(user_id, fullname, username):
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, fullname, username, balance) VALUES (?, ?, ?, 1000)", (user_id, fullname, username))
        conn.commit()
        return True
    else:
        cursor.execute("UPDATE users SET fullname = ?, username = ? WHERE user_id = ?", (fullname, username, user_id))
        conn.commit()
    return False

def db_get_user(user_id):
    cursor.execute("SELECT balance, total_paid, username, fullname FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def db_add_balance(user_id, amount):
    cursor.execute("UPDATE users SET balance = balance + ?, total_paid = total_paid + ? WHERE user_id = ?", (amount, amount, user_id))
    conn.commit()

def db_deduct_balance(user_id, amount):
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
    conn.commit()

def db_get_stats():
    cursor.execute("SELECT COUNT(user_id), SUM(total_paid) FROM users")
    return cursor.fetchone()


# --- HOLATLAR (STATES) ---
class CreateSong(StatesGroup):
    waiting_for_text = State()
    waiting_for_genre = State()

class AdminActions(StatesGroup):
    waiting_for_user_id_p = State()
    waiting_for_money = State()
    waiting_for_user_id_m = State()
    waiting_for_message = State()


# --- KLAVIATURALAR ---
def get_main_menu(user_id):
    buttons = [
        [KeyboardButton(text="🎵 Qo'shiq yaratish"), KeyboardButton(text="📊 Balans")],
        [KeyboardButton(text="💳 Pul kiritish"), KeyboardButton(text="👨‍💼 Admin")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="🛠 Admin Panel")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_genre_menu():
    buttons = [
        [KeyboardButton(text="🎤 Pop"), KeyboardButton(text="🎧 Rep")],
        [KeyboardButton(text="🔊 Bass"), KeyboardButton(text="🎼 Boshqa")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_admin_menu():
    buttons = [
        [KeyboardButton(text="💰 Pul berish"), KeyboardButton(text="✉️ Xabar yuborish")],
        [KeyboardButton(text="📈 Statistika"), KeyboardButton(text="⬅️ Bosh menyu")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


# ================= MAJBURIY GLOBAL HANDLERLAR =================

@dp.message(F.text == "💳 Pul kiritish")
async def deposit_cmd(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "💳 **Balansni to'ldirish tartibi:**\n\n"
        "Karta raqami: `6262570040359129`\n"
        "Narxi: 1 ta qo'shiq = **1 000 so'm**.\n\n"
        f"To'lovni amalga oshirgach, chekni adminga ({ADMIN_USERNAME}) yuboring.\n"
        f"Sizning Telegram ID raqamingiz: `{message.from_user.id}`. Adminga ID ni ham yuboring"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=get_main_menu(message.from_user.id))

@dp.message(F.text == "/start")
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    is_new = db_register_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    
    welcome_text = (
        f"👋 Xush kelibsiz, {message.from_user.full_name}!\n\n"
        "🤖 **Men – Sun'iy Intellekt asosida ishlaydigan eng ilg'or musiqa botiman!**\n\n"
        "✨ **Mening imkoniyatlarim:**\n"
        "📝 Har qanday mavzuda mukammal va ma'noli **qo'shiq matnlari** yarata olaman.\n"
        "👤 Istalgan **ismlarga atab** maxsus va kreativ treklar tayyorlab beraman!\n"
        "🎵 Pop, Rep, Bass va boshqa janrlarda professional kuylar bastalayman.\n\n"
    )
    
    if is_new:
        welcome_text += (
            "🎉 **Ajoyib AKSIYA!** Botimizga birinchi marta kirganingiz uchun sizga "
            "**1 ta qo'shiq yaratish mutlaqo BEPUL (1 000 so'm bonus)** qilib berildi!\n\n"
            "Hoziroq quyidagi tugmalardan foydalanib o'z taronangizga buyurtma bering 👇"
        )
    else:
        welcome_text += "Quyidagi menyu orqali bot imkoniyatlaridan to'liq foydalanishingiz mumkin 👇"

    await message.answer(welcome_text, reply_markup=get_main_menu(message.from_user.id), parse_mode="Markdown")

@dp.message(F.text == "📊 Balans")
async def balance_cmd(message: Message, state: FSMContext):
    await state.clear()
    user_data = db_get_user(message.from_user.id)
    balance = user_data[0] if user_data else 0
    await message.answer(f"💰 Sizning balansingiz: **{balance:,} so'm**\n*(1 ta super qo'shiq = 1 000 so'm)*", parse_mode="Markdown")

@dp.message(F.text == "👨‍💼 Admin")
async def admin_contact_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(f"👨‍💻 Admin bilan bog'lanish: {ADMIN_USERNAME}\n\nSavollaringiz yoki takliflaringiz bo'lsa, bemalol yozishingiz mumkin.")


# --- QO'SHIQ YARATISH JARAYONI ---
@dp.message(F.text == "🎵 Qo'shiq yaratish")
async def create_song_start(message: Message, state: FSMContext):
    await state.clear()
    user_data = db_get_user(message.from_user.id)
    balance = user_data[0] if user_data else 0
    
    if balance < 1000:
        await message.answer("⚠️ Balansingiz yetarli emas. Avval '💳 Pul kiritish' menyusi orqali balansingizni to'ldiring.")
        return

    await message.answer("📝 Qo'shiq kimga atalgan yoki nima haqida bo'lishi kerak? To'liq matnni yoki g'oyangizni yozib qoldiring:")
    await state.set_state(CreateSong.waiting_for_text)

@dp.message(CreateSong.waiting_for_text)
async def process_song_text(message: Message, state: FSMContext):
    if message.text in ["🎵 Qo'shiq yaratish", "📊 Balans", "💳 Pul kiritish", "👨‍💼 Admin", "🛠 Admin Panel"]:
        await state.clear()
        await message.answer("Jarayon bekor qilindi. Menyu qaytadan yuklandi.")
        return
        
    if not message.text:
        await message.answer("Iltimos, qo'shiq matnini matn ko'rinishida yuboring:")
        return

    await state.update_data(song_text=message.text)
    await message.answer("🎵 Qo'shiq qaysi musiqa uslubida (janrda) bo'lsin? Tanlang:", reply_markup=get_genre_menu())
    await state.set_state(CreateSong.waiting_for_genre)

@dp.message(CreateSong.waiting_for_genre)
async def process_song_genre(message: Message, state: FSMContext):
    if message.text in ["🎵 Qo'shiq yaratish", "📊 Balans", "💳 Pul kiritish", "👨‍💼 Admin", "🛠 Admin Panel"]:
        await state.clear()
        await message.answer("Jarayon bekor qilindi.")
        return
        
    genre = message.text
    data = await state.get_data()
    song_text = data.get('song_text', 'Matn topilmadi')
    
    user_data = db_get_user(message.from_user.id)
    if user_data and user_data[0] >= 1000:
        db_deduct_balance(message.from_user.id, 1000)
    else:
        await message.answer("⚠️ Xatolik: Balansingiz yetarli emas.", reply_markup=get_main_menu(message.from_user.id))
        await state.clear()
        return

    user_info = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    
    admin_msg = (
        "🎤 **YANGI BUYURTMA KELDI!**\n\n"
        f"👤 Kimdan: {message.from_user.full_name}\n"
        f"🔗 Lichkasi: {user_info}\n"
        f"🆔 ID: `{message.from_user.id}`\n"
        f"🎶 Janri: {genre}\n"
        f"📝 Matn/Mavzu: {song_text}"
    )
    
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
        await message.answer("✅ Qo'shiq matni adminga yuborildi. Sizga qo'shiq 24 soat ichida yuboriladi.", reply_markup=get_main_menu(message.from_user.id))
    except Exception as e:
        logging.error(f"Adminga buyurtma yuborishda xatolik: {e}")
        await message.answer("❌ Buyurtmani yuborishda xatolik yuz berdi. Qayta urinib ko'ring.", reply_markup=get_main_menu(message.from_user.id))
        
    await state.clear()


# ================= ADMIN PANEL BOSHQARUVI =================

@dp.message(F.text == "🛠 Admin Panel")
async def admin_panel_cmd(message: Message):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("Boshqaruv paneli:", reply_markup=get_admin_menu())

@dp.message(F.text == "⬅️ Bosh menyu")
async def back_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bosh menyudasiz.", reply_markup=get_main_menu(message.from_user.id))

@dp.message(F.text == "📈 Statistika")
async def stats_cmd(message: Message):
    if message.from_user.id != ADMIN_ID: return
    count, total = db_get_stats()
    await message.answer(
        f"📈 **Bot Statistikasi:**\n\nA'zolar: {count or 0} ta\nJami kiritilgan pul: {total or 0:,} so'm",
        parse_mode="Markdown"
    )

@dp.message(F.text == "💰 Pul berish")
async def give_money_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("Foydalanuvchi ID raqamini kiriting:")
    await state.set_state(AdminActions.waiting_for_user_id_p)

@dp.message(AdminActions.waiting_for_user_id_p)
async def give_money_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("ID faqat raqamlardan iborat bo'lishi kerak. Qayta kiriting:")
        return
    await state.update_data(target_id=message.text)
    await message.answer("Summani kiriting (Faqat raqamda):")
    await state.set_state(AdminActions.waiting_for_money)

@dp.message(AdminActions.waiting_for_money)
async def give_money_final(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
        data = await state.get_data()
        target_id = int(data['target_id'])
        db_add_balance(target_id, amount)
        await message.answer("✅ Pul balansga muvaffaqiyatli qo'shildi.")
        try:
            await bot.send_message(target_id, f"🎉 Balansingiz admin tomonidan {amount:,} so'mga to'ldirildi!")
        except:
            pass
    except ValueError:
        await message.answer("Xato kiritildi. Summa faqat raqam bo'lishi kerak.")
    finally:
        await state.clear()

@dp.message(F.text == "✉️ Xabar yuborish")
async def send_msg_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("Kimga xabar/qo'shiq yuboramiz? (Foydalanuvchi ID sini kiriting):")
    await state.set_state(AdminActions.waiting_for_user_id_m)

@dp.message(AdminActions.waiting_for_user_id_m)
async def send_msg_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("ID faqat raqamlardan iborat bo'lishi kerak. Qayta kiriting:")
        return
    await state.update_data(target_id=message.text)
    await message.answer("Xabar matnini yoki qo'shiq (audio/fayl) variantini yuboring:")
    await state.set_state(AdminActions.waiting_for_message)

@dp.message(AdminActions.waiting_for_message)
async def send_msg_final(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        await message.copy_to(chat_id=data['target_id'])
        await message.answer("✅ Xabar/Qo'shiq foydalanuvchiga muvaffaqiyatli yuborildi.")
    except Exception as e:
        await message.answer(f"❌ Xatolik: Xabarni yuborib bo'lmadi. Foydalanuvchi botni bloklagan bo'lishi mumkin.\n\n{e}")
    finally:
        await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
