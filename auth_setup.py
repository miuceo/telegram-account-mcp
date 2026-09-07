"""
Telegram Account uchun bir martalik avtorizatsiya skripti.
Ushbu skript shaxsiy Telegram akkauntingizga ulanadi va Claude Desktop
uchun zarur bo'lgan '.session' faylini xavfsiz yaratadi.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env faylini loyiha papkasidan yuklash
CURRENT_DIR = Path(__file__).resolve().parent
ENV_PATH = CURRENT_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

def get_credentials():
    api_id = os.environ.get("TELEGRAM_API_ID", "").strip()
    api_hash = os.environ.get("TELEGRAM_API_HASH", "").strip()
    session_name = os.environ.get("TELEGRAM_SESSION_NAME", "telegram_user").strip()

    if not api_id or not api_hash or api_id == "12345678" or "your_api_hash" in api_hash:
        print("=" * 60)
        print("Telegram API ma'lumotlari topilmadi yoki to'liq emas.")
        print("Ularni https://my.telegram.org -> 'API development tools' dan olishingiz mumkin.")
        print("=" * 60)
        
        try:
            input_id = input("Telegram API_ID kiriting: ").strip()
            input_hash = input("Telegram API_HASH kiriting: ").strip()
        except KeyboardInterrupt:
            print("\nJarayon bekor qilindi.")
            sys.exit(1)

        if not input_id or not input_hash:
            print("API_ID yoki API_HASH bo'sh bo'lishi mumkin emas!")
            sys.exit(1)

        # .env ga saqlashni taklif qilish
        save_env = input(".env fayliga saqlansinmi? (y/n): ").strip().lower()
        if save_env in ["y", "yes", "ha", ""]:
            with open(ENV_PATH, "w", encoding="utf-8") as f:
                f.write(f"TELEGRAM_API_ID={input_id}\n")
                f.write(f"TELEGRAM_API_HASH={input_hash}\n")
                f.write(f"TELEGRAM_SESSION_NAME={session_name}\n")
            print(f"Ma'lumotlar {ENV_PATH} fayliga saqlandi.\n")

        api_id = input_id
        api_hash = input_hash

    try:
        api_id = int(api_id)
    except ValueError:
        print("Xatolik: API_ID faqat raqamlardan iborat bo'lishi kerak!")
        sys.exit(1)

    return api_id, api_hash, session_name

def main():
    try:
        from telethon.sync import TelegramClient
    except ImportError:
        print("Xatolik: Telethon kutubxonasi o'rnatilmagan.")
        print("Iltimos, avval buyruqni bajaring: pip install telethon python-dotenv")
        sys.exit(1)

    api_id, api_hash, session_name = get_credentials()
    session_file_path = CURRENT_DIR / session_name

    print("\n" + "=" * 60)
    print("Telegram avtorizatsiya jarayoni boshlanmoqda...")
    print(f"Sessiya saqlanadigan joy: {session_file_path}.session")
    print("=" * 60)

    client = TelegramClient(str(session_file_path), api_id, api_hash)

    phone = os.environ.get("TELEGRAM_PHONE", "").strip()
    try:
        # client.start() telefon raqam ko'rsatilgan bo'lsa darhol kod so'raydi
        if phone:
            print(f"Telefon raqam aniqlandi: {phone}")
            client.start(phone=phone)
        else:
            client.start()
        me = client.get_me()

        print("\n" + "=" * 60)
        print("TABRIKLAYMIZ! Avtorizatsiya muvaffaqiyatli yakunlandi.")
        print("=" * 60)
        print(f"Ism: {me.first_name} {me.last_name or ''}".strip())
        print(f"Username: @{me.username}" if me.username else "Username: mavjud emas")
        print(f"User ID: {me.id}")
        print(f"Telefon: {me.phone}")
        print(f"Sessiya fayli: {session_file_path}.session (yaratildi)")
        print("=" * 60)
        print("\nEndi Claude Desktop-ga ulashingiz mumkin!")
    except Exception as e:
        print(f"\nXatolik yuz berdi: {e}")
    finally:
        if client.is_connected():
            client.disconnect()

if __name__ == "__main__":
    main()
