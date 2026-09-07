"""
Render yoki Cloud Hosting uchun TELEGRAM_STRING_SESSION generatsiya qilish skripti.
Render.com da disk vaqtinchalik (ephemeral) bo'lgani uchun fayl o'rniga StringSession ishlatiladi.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

CURRENT_DIR = Path(__file__).resolve().parent
ENV_PATH = CURRENT_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

API_ID = os.environ.get("TELEGRAM_API_ID", "").strip()
API_HASH = os.environ.get("TELEGRAM_API_HASH", "").strip()
PHONE = os.environ.get("TELEGRAM_PHONE", "").strip()

if not API_ID or not API_HASH:
    print("Xatolik: .env faylida TELEGRAM_API_ID yoki TELEGRAM_API_HASH topilmadi!")
    sys.exit(1)

def main():
    print("=" * 60)
    print("Telegram StringSession generatsiya qilish boshlandi...")
    print("=" * 60)

    # StringSession bo'sh holda ishga tushiriladi
    client = TelegramClient(StringSession(), int(API_ID), API_HASH)

    try:
        if PHONE:
            print(f"Telefon: {PHONE}")
            client.start(phone=PHONE)
        else:
            client.start()

        session_string = client.session.save()
        print("\n" + "=" * 60)
        print("STRING SESSION MUVAFFAQIYATLI YARATILDI!")
        print("Render.com muhit o'zgaruvchilariga (Environment Variables) qo'shing:")
        print("=" * 60)
        print(f"\nTELEGRAM_STRING_SESSION={session_string}\n")
        print("=" * 60)

    except Exception as e:
        print(f"Xatolik: {e}")
    finally:
        if client.is_connected():
            client.disconnect()

if __name__ == "__main__":
    main()
