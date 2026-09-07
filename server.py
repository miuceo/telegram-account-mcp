"""
Open Source Telegram MCP Connector for Claude & Anthropic Ecosystem.
Connects personal Telegram account to Claude via Model Context Protocol (MCP).
Supports both local stdio (Claude Desktop) and remote SSE (Render / Docker / VPS).
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# FastMCP / MCPServer import (MCP 1.x and 2.x compatibility)
try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import (
    User,
    Chat,
    Channel,
    MessageMediaDocument,
    MessageMediaPhoto,
    MessageMediaGeo,
    MessageMediaContact,
    MessageMediaPoll,
)

# Loyiha papkasi va .env yuklash
CURRENT_DIR = Path(__file__).resolve().parent
ENV_PATH = CURRENT_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

API_ID_STR = os.environ.get("TELEGRAM_API_ID", "").strip()
API_HASH = os.environ.get("TELEGRAM_API_HASH", "").strip()
SESSION_NAME = os.environ.get("TELEGRAM_SESSION_NAME", "telegram_user").strip()

try:
    API_ID = int(API_ID_STR) if API_ID_STR else 0
except ValueError:
    API_ID = 0

# MCP Server initsializatsiyasi
mcp = MCPServer("telegram-connector")

_client: Optional[TelegramClient] = None
_client_lock = asyncio.Lock()


def format_bytes(size: Optional[int]) -> str:
    """Baytlarni KB, MB yoki GB formatiga o'tkazadi."""
    if not size:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def get_media_description(msg) -> str:
    """Xabarga biriktirilgan media yoki fayl haqida to'liq ma'lumot qaytaradi."""
    if not msg.media:
        return ""

    if isinstance(msg.media, MessageMediaPhoto):
        return " [📷 Rasm]"

    if isinstance(msg.media, MessageMediaDocument):
        file_name = msg.file.name if msg.file and msg.file.name else "Nomsiz fayl"
        file_size = format_bytes(msg.file.size) if msg.file else "noma'lum hajm"
        mime = msg.file.mime_type if msg.file and msg.file.mime_type else "hujjat"
        return f" [📎 Fayl: {file_name} ({file_size}, {mime})]"

    if isinstance(msg.media, MessageMediaGeo):
        return " [📍 Geolokatsiya]"

    if isinstance(msg.media, MessageMediaContact):
        return f" [👤 Kontakt: {msg.media.first_name} ({msg.media.phone_number})]"

    if isinstance(msg.media, MessageMediaPoll):
        return f" [📊 So'rovnoma: {msg.media.poll.question}]"

    return " [Fayl/Media]"


def parse_chat_id(chat_id: str):
    """Chat ID, username yoki maxsus 'me' (Saved Messages) identifikatorini aniqlaydi."""
    chat_id = str(chat_id).strip()
    if chat_id.lower() in ["me", "self", "saved", "saved messages", "saqlanganlar"]:
        return "me"
    if (chat_id.startswith("-") and chat_id[1:].isdigit()) or chat_id.isdigit():
        return int(chat_id)
    return chat_id


async def get_client() -> TelegramClient:
    """Telegram mijozini xavfsiz ulaydi (StringSession yoki lokal .session fayli orqali)."""
    global _client
    async with _client_lock:
        if not API_ID or not API_HASH:
            raise RuntimeError(
                "TELEGRAM_API_ID yoki TELEGRAM_API_HASH sozlanmagan! "
                "Iltimos, .env faylini to'ldiring yoki muhit o'zgaruvchilarini sozlang."
            )

        string_session = os.environ.get("TELEGRAM_STRING_SESSION", "").strip()

        if _client is None:
            if string_session:
                _client = TelegramClient(StringSession(string_session), API_ID, API_HASH)
            else:
                session_file = CURRENT_DIR / f"{SESSION_NAME}.session"
                if not session_file.exists():
                    raise RuntimeError(
                        f"Telegram sessiya fayli ({session_file.name}) topilmadi!\n"
                        f"Iltimos, avval konsolda 'python auth_setup.py' ni ishga tushirib avtorizatsiyadan o'ting."
                    )
                session_path = CURRENT_DIR / SESSION_NAME
                _client = TelegramClient(str(session_path), API_ID, API_HASH)

        if not _client.is_connected():
            await _client.connect()

        if not await _client.is_user_authorized():
            raise RuntimeError(
                "Telegram sessiyasi avtorizatsiyadan o'tmagan yoki bekor qilingan.\n"
                "Iltimos, 'python auth_setup.py' orqali qayta kiring."
            )

        return _client


@mcp.tool()
async def get_me() -> str:
    """
    Ulangan shaxsiy Telegram akkaunt ma'lumotlarini (ism, username, user_id, telefon) qaytaradi.
    Claude, bu vositani akkaunt haqida ma'lumot olish yoki aloqani tekshirish uchun chaqir.
    """
    try:
        tg = await get_client()
        me = await tg.get_me()
        return (
            f"👤 Ulangan Telegram akkaunt:\n"
            f"- Ism: {me.first_name} {me.last_name or ''}\n"
            f"- Username: @{me.username if me.username else 'mavjud emas'}\n"
            f"- User ID: `{me.id}`\n"
            f"- Telefon: +{me.phone if me.phone else 'yashirilgan'}\n"
            f"- Premium: {'Ha' if getattr(me, 'premium', False) else 'Yo‘q'}"
        )
    except Exception as e:
        return f"Xatolik yuz berdi: {str(e)}"


@mcp.tool()
async def get_telegram_stats() -> str:
    """
    Telegram akkauntingizning to'liq umumiy statistikasini qaytaradi:
    jami suhbatlar, ulangan kanallar, guruhlar, shaxsiy suhbatlar, botlar va o'qilmagan xabarlar soni.
    Claude, foydalanuvchi akkaunt holati yoki nechta kanalga a'zoligini so'raganda ushbu vositadan foydalan.
    """
    try:
        tg = await get_client()
        dialogs = await tg.get_dialogs()

        channels_count = 0
        groups_count = 0
        private_count = 0
        bots_count = 0
        total_unread_dialogs = 0
        total_unread_messages = 0

        for d in dialogs:
            entity = d.entity
            if d.unread_count > 0:
                total_unread_dialogs += 1
                total_unread_messages += d.unread_count

            if isinstance(entity, Channel):
                if entity.broadcast:
                    channels_count += 1
                else:
                    groups_count += 1
            elif isinstance(entity, Chat):
                groups_count += 1
            elif isinstance(entity, User):
                if entity.bot:
                    bots_count += 1
                else:
                    private_count += 1

        return (
            f"📊 Telegram akkaunt statistikasi:\n"
            f"- Jami suhbatlar (chatlar): {len(dialogs)}\n"
            f"- A'zo bo'lingan kanallar: {channels_count}\n"
            f"- Guruhlar (va superguruhlar): {groups_count}\n"
            f"- Shaxsiy suhbatlar: {private_count}\n"
            f"- Botlar: {bots_count}\n"
            f"- O'qilmagan xabarlar mavjud chatlar: {total_unread_dialogs}\n"
            f"- Jami o'qilmagan xabarlar soni: {total_unread_messages}"
        )
    except Exception as e:
        return f"Statistikani olishda xatolik: {str(e)}"


@mcp.tool()
async def get_saved_messages(limit: int = 15) -> str:
    """
    Shaxsiy 'Saved Messages' (Saqlangan xabarlar / Избранное) bo'limidagi so'nggi xabarlarni o'qiydi.
    MUHIM (Claude uchun): Agar foydalanuvchi limit ko'rsatmagan bo'lsa, foydalanuvchidan nechta xabarni o'qish kerakligini so'rang (standart: 15).
    """
    try:
        tg = await get_client()
        messages = await tg.get_messages("me", limit=limit)

        if not messages:
            return "Saved Messages (Saqlangan xabarlar) bo'sh."

        lines = [f"📁 Saved Messages'dagi so'nggi {len(messages)} ta xabar:\n"]
        for msg in reversed(messages):
            date_str = msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else ""
            media_str = get_media_description(msg)
            text = msg.text or "(matnsiz xabar)"
            lines.append(f"• [{date_str}] (ID: `{msg.id}`): {text}{media_str}")

        return "\n".join(lines)
    except Exception as e:
        return f"Saved Messages'ni o'qishda xatolik: {str(e)}"


@mcp.tool()
async def send_to_saved_messages(message: str) -> str:
    """
    Shaxsiy 'Saved Messages' (Saqlangan xabarlar) bo'limiga yangi qayd, matn yoki xabar saqlaydi.
    message: Saqlanishi kerak bo'lgan matn.
    """
    try:
        if not message.strip():
            return "Xatolik: Saqlanadigan matn bo'sh bo'lishi mumkin emas."

        tg = await get_client()
        sent = await tg.send_message("me", message)
        return f"✅ Xabar Saved Messages'ga muvaffaqiyatli saqlandi! (Xabar ID: {sent.id})"
    except Exception as e:
        return f"Saved Messages'ga saqlashda xatolik: {str(e)}"


@mcp.tool()
async def get_dialogs(limit: int = 15, filter_type: str = "all") -> str:
    """
    Telegramdagi so'nggi chatlar ro'yxatini qaytaradi.
    filter_type: 'all' (hammasi), 'channels' (faqat kanallar), 'groups' (faqat guruhlar), 'private' (shaxsiy yozishmalar), 'bots' (botlar).
    limit: Nechta chatni ko'rsatish kerak (standart: 15).
    MUHIM (Claude uchun): Agar foydalanuvchi limitni aytmagan bo'lsa, undan nechtagacha chatni ko'rishni xohlashini so'rang.
    """
    try:
        tg = await get_client()
        dialogs = await tg.get_dialogs(limit=None if filter_type != "all" else limit)

        results = []
        filter_type = filter_type.lower()

        for d in dialogs:
            entity = d.entity
            chat_type = "Noma'lum"

            if isinstance(entity, Channel):
                chat_type = "Kanal" if entity.broadcast else "Guruh"
            elif isinstance(entity, Chat):
                chat_type = "Guruh"
            elif isinstance(entity, User):
                chat_type = "Bot" if entity.bot else "Shaxsiy"

            # Filtrlash
            if filter_type == "channels" and chat_type != "Kanal":
                continue
            if filter_type == "groups" and chat_type != "Guruh":
                continue
            if filter_type == "private" and chat_type != "Shaxsiy":
                continue
            if filter_type == "bots" and chat_type != "Bot":
                continue

            unread = f" [O'qilmagan: {d.unread_count}]" if d.unread_count > 0 else ""
            results.append(f"• ID: `{d.id}` | Nomi: **{d.name}** | Turi: {chat_type}{unread}")

            if len(results) >= limit:
                break

        if not results:
            return f"'{filter_type}' filtri bo'yicha chatlar topilmadi."

        return f"📋 Topilgan {len(results)} ta chat ({filter_type}):\n\n" + "\n".join(results)
    except Exception as e:
        return f"Chatlar ro'yxatini olishda xatolik: {str(e)}"


@mcp.tool()
async def get_messages(chat_id: str, limit: int = 20) -> str:
    """
    Muayyan chat, kanal, guruh yoki foydalanuvchining so'nggi xabarlar tarixini o'qiydi.
    chat_id: Chat ID raqami (masalan, -100123456789), username (masalan, @kanal) yoki 'me' (Saved Messages).
    limit: Nechta oxirgi xabarni o'qish (standart: 20).
    MUHIM (Claude uchun): Agar foydalanuvchi limitni aytmagan bo'lsa, undan nechta xabarni o'qishni xohlashini so'rang.
    """
    try:
        tg = await get_client()
        target = parse_chat_id(chat_id)
        entity = await tg.get_entity(target)
        entity_name = getattr(entity, 'title', None) or getattr(entity, 'first_name', str(chat_id))

        messages = await tg.get_messages(entity, limit=limit)

        if not messages:
            return f"'{entity_name}' chatida xabarlar mavjud emas."

        lines = [f"💬 '{entity_name}' chatidagi so'nggi {len(messages)} ta xabar:\n"]
        for msg in reversed(messages):
            sender_name = "Noma'lum"
            if msg.sender:
                if isinstance(msg.sender, User):
                    sender_name = f"{msg.sender.first_name} {msg.sender.last_name or ''}".strip()
                    if msg.sender.username:
                        sender_name += f" (@{msg.sender.username})"
                elif hasattr(msg.sender, 'title'):
                    sender_name = msg.sender.title

            date_str = msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else ""
            media_str = get_media_description(msg)
            text = msg.text or "(matnsiz xabar)"
            lines.append(f"[{date_str}] (ID: `{msg.id}`) **{sender_name}**: {text}{media_str}")

        return "\n".join(lines)
    except Exception as e:
        return f"Xabarlarni o'qishda xatolik ({chat_id}): {str(e)}"


@mcp.tool()
async def get_chat_files(chat_id: str, limit: int = 15, file_type: str = "all") -> str:
    """
    Muayyan chatdagi barcha fayllar, hujjatlar, rasmlar, audio va videolarni saralab ro'yxatini chiqaradi.
    chat_id: Chat ID, username yoki 'me'.
    file_type: 'all' (barcha fayllar), 'documents' (faqat hujjatlar/PDF/ZIP), 'photos' (rasmlar), 'audio' (musiqa/ovoz).
    limit: Nechta fayl topish kerak (standart: 15).
    MUHIM (Claude uchun): Foydalanuvchidan qidirilayotgan fayllar limiti haqida aniqlik kiritishni so'rang.
    """
    try:
        tg = await get_client()
        target = parse_chat_id(chat_id)
        entity = await tg.get_entity(target)
        entity_name = getattr(entity, 'title', None) or getattr(entity, 'first_name', str(chat_id))

        # Media xabarlarni o'qish
        messages = await tg.get_messages(entity, limit=limit * 3)

        file_list = []
        file_type = file_type.lower()

        for msg in messages:
            if not msg.media:
                continue

            is_photo = isinstance(msg.media, MessageMediaPhoto)
            is_doc = isinstance(msg.media, MessageMediaDocument)

            if file_type == "photos" and not is_photo:
                continue
            if file_type == "documents" and not is_doc:
                continue

            date_str = msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else ""
            desc = get_media_description(msg)
            caption = f" - Izoh: '{msg.text}'" if msg.text else ""
            file_list.append(f"• [ID: `{msg.id}` | {date_str}]{desc}{caption}")

            if len(file_list) >= limit:
                break

        if not file_list:
            return f"'{entity_name}' chatida '{file_type}' turidagi fayllar topilmadi."

        return f"📁 '{entity_name}' chatidagi fayllar ro'yxati ({len(file_list)} ta):\n\n" + "\n".join(file_list)
    except Exception as e:
        return f"Fayllarni olishda xatolik: {str(e)}"


@mcp.tool()
async def send_message(chat_id: str, message: str, reply_to_msg_id: Optional[int] = None) -> str:
    """
    Foydalanuvchi, guruh, kanal yoki 'me' ga shaxsiy akkauntingiz nomidan yangi xabar yuboradi.
    chat_id: Chat ID raqami, username yoki 'me' (Saved Messages).
    message: Yuboriladigan xabar matni.
    reply_to_msg_id: Ixtiyoriy, agar muayyan bir xabarga javob (reply) berilayotgan bo'lsa xabar ID raqami.
    """
    try:
        if not message.strip():
            return "Xatolik: Xabar matni bo'sh bo'lishi mumkin emas."

        tg = await get_client()
        target = parse_chat_id(chat_id)
        entity = await tg.get_entity(target)

        sent = await tg.send_message(entity, message, reply_to=reply_to_msg_id)
        entity_name = getattr(entity, 'title', None) or getattr(entity, 'first_name', str(chat_id))

        reply_info = f" (Javob berilgan xabar ID: {reply_to_msg_id})" if reply_to_msg_id else ""
        return f"✅ Xabar muvaffaqiyatli yuborildi!\n- Qabul qiluvchi: {entity_name}\n- Xabar ID: `{sent.id}`{reply_info}"
    except Exception as e:
        return f"Xabar yuborishda xatolik: {str(e)}"


@mcp.tool()
async def search_messages(query: str, limit: int = 10, chat_id: str = "") -> str:
    """
    Telegram xabarlari orasidan kalit so'z bo'yicha qidiradi.
    query: Qidirilayotgan so'z yoki ibora.
    limit: Natijalar soni (standart: 10).
    chat_id: Agar berilsa, faqat shu chat ichidan qidiradi (masalan 'me' Saved Messages uchun); bo'sh bo'lsa barcha chatlardan qidiradi.
    MUHIM (Claude uchun): Agar limit ko'rsatilmagan bo'lsa, foydalanuvchidan qidiruv chegarasini so'rang.
    """
    try:
        tg = await get_client()
        target_entity = None
        if chat_id.strip():
            target = parse_chat_id(chat_id)
            target_entity = await tg.get_entity(target)

        messages = await tg.get_messages(target_entity, search=query, limit=limit)

        if not messages:
            return f"'{query}' so'rovi bo'yicha xabarlar topilmadi."

        lines = [f"🔍 '{query}' bo'yicha topilgan {len(messages)} ta xabar:\n"]
        for msg in messages:
            chat_title = "Chat"
            if msg.chat and hasattr(msg.chat, 'title'):
                chat_title = msg.chat.title
            elif msg.chat and hasattr(msg.chat, 'first_name'):
                chat_title = msg.chat.first_name

            date_str = msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else ""
            media_str = get_media_description(msg)
            lines.append(f"• [{date_str}] [{chat_title}] (ChatID: `{msg.chat_id}` | MsgID: `{msg.id}`): {msg.text}{media_str}")

        return "\n".join(lines)
    except Exception as e:
        return f"Qidiruvda xatolik: {str(e)}"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Open-source Telegram MCP Connector")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"], help="MCP transport turi (stdio yoki sse)")
    parser.add_argument("--host", default="0.0.0.0", help="SSE host manzili")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")), help="SSE port raqami")
    args = parser.parse_args()

    # Render yoki SSE rejimida ishga tushirish
    if "PORT" in os.environ or args.transport == "sse":
        print(f"🚀 Telegram MCP server SSE rejimida ishga tushmoqda: {args.host}:{args.port}")
        mcp.run(transport="sse")
    else:
        # Claude Desktop uchun standart stdio rejimi
        mcp.run()
