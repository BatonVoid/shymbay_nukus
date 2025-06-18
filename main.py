import asyncio
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ChatMember
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, BigInteger, select
import logging
from aiogram.client.bot import DefaultBotProperties



default_bot_properties = DefaultBotProperties(parse_mode="HTML")



# ==== 🔐 Конфигурация ====
BOT_TOKEN = "8159844260:AAHOqePOs3MESOJbpgOu_HeX0RzQI3axNzo"

ADMIN_ID = 1033785549  # Admin IDs
DATABASE_URL = "sqlite+aiosqlite:///./taxi_bot.db"

# ==== 🧱 База данных ====
Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
START_TEXT = """

Sálem, jolawshı. Siziń jolıńız - biz ushın áhmietli!

Nókis - Shym taksisi - balalar hám jaqınlarıńız bilen sayaxatlarda 
isenimli birge islesiwshińiz. Biz qolaylıq, qáwipsizlik hám qolaylı kún tártibin támiyinleymiz.

Pútkil shańaraq ushın keń avtomobiller
Ádepli hám tájiriybeli aydawshılar
Jasırın tólemlersiz belgilengen baha
Dem alıw hám awqatlanıw ushın toqtaw imkaniyatı
Taza salon, qáwipsizlik remeni, klimat-kontrol.
🚗 Tuwısqanlarǵa barıw jolı shın mánisinde qolaylı bolsın. Búgin taksi buyırtpa etiń!
"""

TEXT_SHYMBAY_NOKIS = """
✅ SHYMBAY - NOKIS jónelisin tańlaǵanıńız ushın raxmet!
Siziń jolıńızdıń bir bólegi bolıp, sayaxatıńızdı ańsat hám kewilli qılıwımızdan quwanıshlımız.

Siz ushın qolaylı waqıtta jolǵa shıǵıwǵa tayar bolǵan tájiriybeli aydawshılar sebepli bizde hár qashan hár kim ushın orın tabıladı. 
Iseniwiniz múmkin: jol artıqsha táshwishsiz hám óz waqtında ótedi.

➤ <b>Telefon</b>: +998907288311
➤ <b>Telefon</b>: +998907348311
✅ <b>Qosımsha xızmetler</b>: Amanat bolsa ALÍP KETEMIZ.

Jolıńız bolsın!
"""

TEXT_NOKIS_SHYMBAY = """
✅ NOKIS - SHYMBAY tańladıńız ba? Ájayıp tańlaw!
Ózimizdiń úsh shofer jigitimiz bar, hámmesi ózimizdiń, sınalǵan, baylanısta. 
Mashinalar taza, tártip penen háreketlenedi, balalı shańaraqqa yamasa doslar toparına sáykes kele aladı.

Belgili bir waqıtta shıǵıw kerek bolsa, qońıraw etiń. 
Hámmesin kelisip alıp, sizlerdi waqtında kútip alamız.

➤ <b>Telefon</b>: +998907288311
➤ <b>Telefon</b>: +998907348311
✅ <b>Qosımsha xızmetler</b>: Amanat bolsa ALÍP KETEMIZ.

Jolıńız bolsın!
"""
class UserStats(Base):
    __tablename__ = "user_stats"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, index=True)
    interactions = Column(Integer, default=1)

# ==== 🎛 Клавиатуры ====
def get_user_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏙 Shymbay → Nokis")],
            [KeyboardButton(text="🌆 Nókis → Shymbay")]
        ],
        resize_keyboard=True
    )

def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏙 Shymbay → Nokis")],
            [KeyboardButton(text="🌆 Nókis → Shymbay")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="Xabarlandırıw")]
        ],
        resize_keyboard=True
    )

# ==== 🤖 Логика ====
router = Router()


async def add_or_update_user(user_id: int):
    async with SessionLocal() as session:
        result = await session.execute(select(UserStats).where(UserStats.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            user.interactions += 1
        else:
            user = UserStats(user_id=user_id)
            session.add(user)

        await session.commit()

async def broadcast_to_all_users(bot: Bot, text: str):
    async with SessionLocal() as session:
        result = await session.execute(select(UserStats.user_id))
        user_ids = [row[0] for row in result.fetchall()]

    success = 0
    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=user_id, text=text)
            success += 1
        except Exception:
            pass
    return success

# ==== 🎯 Хендлеры ====

@router.message(CommandStart())
async def cmd_start(message: Message):
    bot = message.bot
    user_id = message.from_user.id

    await add_or_update_user(user_id)

    keyboard = get_admin_keyboard() if user_id == ADMIN_ID else get_user_keyboard()

    await message.answer(
        "Sálemetsiz be! Qay jóneliske taksi kerek?" + START_TEXT,
        reply_markup=keyboard
    )

@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    async with SessionLocal() as session:
        result = await session.execute(select(UserStats))
        users = result.scalars().all()

    total_users = len(users)
    total_interactions = sum(u.interactions for u in users)

    await message.answer(
        f"📈 Жалпы қолданушылар: <b>{total_users}</b>\n"
        f"📊 Жалпы әрекеттер: <b>{total_interactions}</b>",

    )

@router.message(F.text == "Xabarlandırıw")
async def notify_info(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("✍️ Jiberginiz kelgen xabardı jazıń, onı hámme kóredi..")

@router.message(F.text)
async def message_handler(message: Message):
    user_id = message.from_user.id
    text = message.text


    

    if text == ("🏙 Shymbay → Nokis"):
        await add_or_update_user(user_id)
        await message.answer(f" " + TEXT_SHYMBAY_NOKIS)


    if text == ("🌆 Nókis → Shymbay"):
        await add_or_update_user(user_id)
        await message.answer(f" " + TEXT_NOKIS_SHYMBAY)


    if user_id == ADMIN_ID and text not in ["📊 Statistika", "Xabarlandırıw", "🏙 Shymbay → Nókis", "🌆 Nókis → Shymbay"]:
        count = await broadcast_to_all_users(message.bot, f"📢 Admin xabarı:\n\n{text}")
        await message.answer(f"✅ Xabar {count} adamǵa jiberildi.")
        return


async def main():

    # Создание таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    default_bot_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
    bot = Bot(token=BOT_TOKEN, default=default_bot_properties)
    dp = Dispatcher()
    dp.include_router(router)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logging.error(f"Ошибка при создании таблиц: {e}")

    logging.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
