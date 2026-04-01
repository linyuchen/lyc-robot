# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cross-platform chatbot built on **NoneBot2** framework with AI integration. Supports QQ (OneBot V11), Telegram, and GitHub adapters. All user-facing text is in Chinese.

## Commands

### Run the bot
```bash
python bot.py
```

### Install dependencies
```bash
# Using uv (preferred):
uv sync

# Or pip:
pip install -r requirements.txt
```

### Docker
```bash
docker build -t qqrobot .
docker run -e ENVIRONMENT=prod -v /data:/app/data qqrobot
```

### Playwright (required for browser-based features)
```bash
python -m playwright install --with-deps chromium
```

### Tests
Test files are in `tests/`. No unified test runner is configured; run individual test files directly:
```bash
python -m pytest tests/test_ai_chat_yuanbao.py
```

## Architecture

### Entry Point
`bot.py` — initializes NoneBot2, registers all three adapters (OneBot, Telegram, GitHub), runs Alembic database migrations, then loads all plugins from `src/plugins/`.

### Source Layout
- **`src/plugins/`** — ~30 plugin modules, auto-discovered by `nonebot.load_plugins("src/plugins")`. Each plugin uses NoneBot2 decorators (`@on_command`, `@on_message`, `@on_fullmatch`) and declares `PluginMetadata`.
- **`src/plugins/common/`** — Shared plugin utilities: rules engine, session helpers, permission checks.
- **`src/common/`** — Non-plugin shared code: AI chat engines, bilibili integration, browser automation, config, fonts, game logic, utilities.
- **`src/db/`** — Database layer with SQLAlchemy ORM models (`models/`), Alembic migrations (`alembic_tools/`), and data access helpers (`model_utils/`).
- **`data/`** — Runtime data: SQLite databases, cookies, AI prompts (`data/chatgpt_prompt/`), screenshots.

### AI Chat System (`src/common/ai_chat/`)
Uses **LiteLLM** as a unified interface to multiple LLM providers (OpenAI, DeepSeek, Gemini, Tencent YuanBao). Key classes:
- `AIChat` (`base.py`) — manages conversation state, history, and prompts
- `chat_engine.py` — high-level API, context management, persistent prompt storage
- Custom LLM handlers for Tencent Cloud and YuanBao in dedicated submodules

AI model configuration is in `.env` via `AI_CHATS` (JSON array of `{api_key, base_url, model}`). Model strings follow LiteLLM provider format (e.g., `openai/gpt-4o-mini`, `deepseek/deepseek-chat`).

### Database
Two separate SQLite databases, both auto-migrated on startup:
- **common_db** — shared data across features
- **group_point_db** — group-specific points/activity data

Migration scripts: `src/db/alembic_tools/common_db/` and `src/db/alembic_tools/group_point_db/`.

### Plugin Management
Plugins support per-group and global enable/disable through the manager plugin (`src/plugins/manager/`). Commands: `启用插件 <名>`, `禁用插件 <名>`, `全局启用插件 <名>`, `全局禁用插件 <名>` (superuser only).

### Configuration
All config via `.env` file (loaded by NoneBot2). Key variables:
- `AI_CHATS` — AI model provider configs (JSON)
- `SUPERUSERS` — admin user IDs
- `HTTP_PROXY` — proxy for external API access
- `COMMAND_START=[""]` — no command prefix required
- Adapter-specific: `ONEBOT_WS_URLS`, `telegram_bots`, `GITHUB_APPS`

Runtime config model: `src/common/config.py` (Pydantic `Config` class with `ConfigAIChat`).

### Key Dependencies
NoneBot2 2.4.2, LiteLLM, Playwright (browser automation), SQLAlchemy + Alembic, Pillow (image processing), BeautifulSoup4, aiohttp/httpx.

Python version: >=3.11 (Docker uses 3.12).

### Adding a New Plugin
1. Create directory under `src/plugins/`
2. Add `__init__.py` with `PluginMetadata` and NoneBot2 event handlers
3. If database needed: add model to `src/db/models/`, operations to `src/db/model_utils/`, and create Alembic migration
