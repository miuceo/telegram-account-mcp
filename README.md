<p align="center">
  <img src="assets/banner.jpg" alt="Telegram Account MCP Connector" width="100%" />
</p>

# 🚀 Telegram Account MCP Connector for Claude

<p align="center">
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-Protocol-blue.svg" alt="MCP" /></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-yellow.svg" alt="Python" /></a>
  <a href="https://github.com/LonamiWebs/Telethon"><img src="https://img.shields.io/badge/Telethon-MTProto-blue.svg" alt="Telethon" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT" /></a>
</p>

An open-source **Model Context Protocol (MCP)** server that connects your personal **Telegram** account to **Claude Desktop**, **Claude Code**, or any MCP-compatible AI client.

Give Claude superpowers to read your chats, check your Saved Messages, inspect files and media, summarize channel feeds, search history, and send messages on your behalf.

---

## ✨ Features

- 📁 **Saved Messages ("Избранное")**: Full access to read and write notes, links, and snippets into your personal Saved Messages.
- 📎 **Files & Media Inspection**: View file names, sizes (KB/MB), MIME types, photos, and documents across your chats.
- 📊 **Account Statistics**: Overview of total chats, joined channels, supergroups, private chats, bots, and unread counts.
- 🔍 **Global & Scoped Search**: Search across all your Telegram chats or within a specific conversation.
- 🎯 **Intelligent Limit Management**: Prompt-guided tools ensure Claude asks you for limits rather than overwhelming your conversation context.
- ⚡️ **Dual Deployment Modes**:
  - **Local `stdio`**: Runs seamlessly as a child process of Claude Desktop.
  - **Remote `SSE`**: Deployable 24/7 to [Render](https://render.com), Railway, or Docker.

---

## 🛠 Available MCP Tools

| Tool | Parameters | Description |
| :--- | :--- | :--- |
| `get_me` | *none* | Returns logged-in Telegram user info (Name, Username, ID, Phone). |
| `get_telegram_stats` | *none* | Account overview (channels count, groups, private chats, unread counter). |
| `get_saved_messages` | `limit` (default: 15) | Read messages and notes from your personal **Saved Messages**. |
| `send_to_saved_messages` | `message` | Store a note or message into **Saved Messages**. |
| `get_dialogs` | `limit`, `filter_type` (`all`, `channels`, `groups`, `private`, `bots`) | List recent chats filtered by category. |
| `get_messages` | `chat_id`, `limit` (default: 20) | Read message history with rich media and document metadata. |
| `get_chat_files` | `chat_id`, `limit`, `file_type` (`all`, `documents`, `photos`, `audio`) | Inspect files and media shared in a specific chat. |
| `send_message` | `chat_id`, `message`, `reply_to_msg_id` | Send a new message or reply to a specific message. |
| `search_messages` | `query`, `limit`, `chat_id` | Search messages globally or inside a specific chat. |

---

## 🚀 Quickstart Guide

### 1. Clone & Install

```bash
git clone https://github.com/miuceo/telegram-account-mcp.git
cd telegram-account-mcp
pip install -r requirements.txt
```

### 2. Get Telegram API Credentials

1. Go to [my.telegram.org](https://my.telegram.org) and log in with your phone number.
2. Navigate to **API development tools**.
3. Create a new application and copy your `api_id` and `api_hash`.

### 3. One-Time Login (Session Creation)

Run the interactive authentication script:

```bash
python auth_setup.py
```

- Enter your `API_ID` and `API_HASH` (saved automatically to `.env`).
- Enter your phone number (e.g. `+998880084506`) and the 5-digit verification code sent to your Telegram app.
- This creates your secure `telegram_user.session` file locally.

---

## 🖥 Claude Desktop Setup (Local stdio)

Open or create `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "telegram": {
      "command": "python",
      "args": [
        "C:\\path\\to\\telegram-mcp-connector\\server.py"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

Restart **Claude Desktop**. You will see the 🔨 hammer icon with all 9 Telegram tools ready!

---

## ☁️ 24/7 Hosting on Render (Remote SSE Mode)

Because Render containers have ephemeral storage, generate a persistent `TELEGRAM_STRING_SESSION` first:

```bash
python generate_string_session.py
```

Copy the generated `TELEGRAM_STRING_SESSION` string.

### Deploying to Render:
1. Push this repository to your GitHub.
2. Go to [Render Dashboard](https://dashboard.render.com/) -> **New +** -> **Web Service**.
3. Connect your repository.
4. Set:
   - **Environment**: `Python` (or `Docker`)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py --transport sse`
5. Add **Environment Variables**:
   - `TELEGRAM_API_ID` = `your_api_id`
   - `TELEGRAM_API_HASH` = `your_api_hash`
   - `TELEGRAM_STRING_SESSION` = `your_generated_string_session`
6. Deploy! Render will give you a public URL (e.g., `https://my-telegram-mcp.onrender.com`).

---

## 🔒 Security Best Practices

- **Never commit `.env` or `*.session` files**: They grant full access to your Telegram account. The provided `.gitignore` prevents them from being tracked.
- **Flood Limits**: Telegram enforces rate limits. The tools are designed to fetch targeted batches.
- **Review Permissions**: When using Claude to send messages, ask Claude to confirm recipient and message before sending.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
