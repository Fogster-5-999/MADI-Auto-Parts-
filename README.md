<h1 align="center">🚗 МАДИ Автозапчасти</h1>
<p align="center">Веб-приложение для подбора автозапчастей с AI-экспертом</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Yandex_Cloud_AI-Qwen3--235B-FC3F24?style=for-the-badge" alt="Yandex AI">
  <img src="https://img.shields.io/badge/Deploy-Render-4D68FF?style=for-the-badge&logo=render&logoColor=white" alt="Render">
</p>

<p align="center">
  <a href="https://madi-auto-parts.onrender.com/">🔗 Демо</a>
</p>

---


## О проекте

Веб-приложение для подбора автомобильных запчастей с интегрированным AI-экспертом. Пользователь выбирает марку → модель → категорию → деталь, а AI-бот консультирует по ремонту и удешевлению.

### Возможности

- 🔍 **Каталог запчастей** — каскадный подбор по марке, модели и модификации
- 🤖 **AI-эксперт** — чат-бот на базе Yandex Cloud AI (Qwen3-235B)
- 🛒 **Корзина** — сборка списка запчастей (клиент-сторон)
- 🌗 **Темы** — тёмный / светлый режим
- 📱 **Адаптивный дизайн** — glassmorphism, работает на мобильных

---

## Стек

| Слой | Технологии |
|---|---|
| Backend | FastAPI, Uvicorn, httpx |
| Frontend | Vanilla HTML/CSS/JS (один файл) |
| AI | Yandex Cloud AI (Qwen3-235B) через OpenAI SDK |
| Каталог | UMAPI.ru API (проксируется через бэкенд) |
| Деплой | Render.com (free tier) |
| БД | Нет — сессии in-memory |

---

## Быстрый старт

```bash
# Клонировать
git clone https://github.com/Fogster-5-999/MADI-Auto-Parts-.git
cd MADI-Auto-Parts-

# Установить зависимости
pip install -r requirements.txt

# Задать переменные окружения
export FOLDER_ID="ваш_yandex_folder_id"
export API_KEY="ваш_yandex_cloud_api_key"
export UMAPI_KEY="ваш_umapi_key"

# Запустить
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Откройте http://localhost:8000

---

## Структура

```
MADI-Auto-Parts-/
├── app/
│   ├── main.py              # Точка входа, CORS, роутеры
│   ├── config.py            # Переменные окружения
│   ├── sessions.py          # Хранилище диалогов (in-memory)
│   ├── text.py              # Очистка Markdown из ответов AI
│   ├── services/
│   │   └── ai.py            # Yandex Cloud AI клиент + промпт
│   ├── routers/
│   │   ├── health.py        # GET /health
│   │   ├── chat.py          # POST /chat
│   │   └── parts.py         # GET /api/parts/{lang}/{region}/{endpoint}
│   └── static/
│       └── MADIPARTS.html   # Весь фронтенд в одном файле
├── requirements.txt
└── render.yaml
```

---

## API

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/` | `MADIPARTS.html` |
| `GET` | `/health` | Статус AI и модель |
| `POST` | `/chat` | Отправить сообщение AI-эксперту |
| `GET` | `/api/parts/{lang}/{region}/{endpoint}` | Прокси к каталогу UMAPI.ru |

### POST /chat

```json
// Request
{ "message": "Какие тормозные колодки лучше для Toyota Camry?", "session_id": "optional" }

// Response
{ "reply": "Для Toyota Camry рекомендую...", "session_id": "madi_user_1234" }
```

---

## Переменные окружения

| Переменная | Описание | Обязательна |
|---|---|---|
| `FOLDER_ID` | ID папки Yandex Cloud | Да |
| `API_KEY` | API-ключ Yandex Cloud | Да |
| `UMAPI_KEY` | API-ключ UMAPI.ru | Да |
| `MODEL` | Модель AI (по умолчанию `qwen3-235b-a22b-fp8/latest`) | Нет |

---
