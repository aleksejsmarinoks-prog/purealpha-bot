# 🧠 PureAlpha 3.1 MVP
## AI Investment Copilot using Causal AI

> Первый retail-доступный инвестиционный советник на основе причинно-следственного ИИ

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🚀 Быстрый старт (3 минуты)

### Способ 1: Docker (рекомендуется)

```bash
# Клонируй проект
git clone https://github.com/purealpha/mvp
cd purealpha-mvp

# Запусти всё одной командой
docker-compose up -d

# Готово! Открой:
# - UI: http://localhost:8501
# - API Docs: http://localhost:8000/docs
```

### Способ 2: Локальная установка

```bash
# Установи зависимости
pip install -r requirements.txt

# Скопируй конфиг
cp .env.example .env
# Отредактируй .env (добавь API keys)

# Запусти API
uvicorn src.api:app --reload

# В другом терминале: запусти UI
streamlit run ui/streamlit_app.py
```

---

## 💡 Первый запрос

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "capital": 5000,
    "years": 1,
    "risk_level": "MEDIUM"
  }'
```

**Ответ:**
```json
{
  "status": "success",
  "portfolio": {
    "VTI": 2100.00,
    "VXUS": 1400.00,
    "BND": 1000.00,
    "GLD": 500.00
  },
  "metrics": {
    "expected_return": 0.089,
    "volatility": 0.118,
    "sharpe_ratio": 0.37
  },
  "market_context": {
    "regime": "GOLDILOCKS",
    "lsi": 42.5
  }
}
```

---

## ✨ Ключевые возможности

- ✅ **Causal AI** — использует Do-Calculus, не корреляции
- ✅ **350+ параметров** — макро, геополитика, on-chain, sentiment
- ✅ **10 рыночных режимов** — динамическое распределение
- ✅ **CVaR оптимизация** — защита от хвостовых рисков
- ✅ **Blockchain timestamps** — проверяемые прогнозы
- ✅ **Explainable AI** — понимание каждого решения

---

## 📁 Структура проекта

```
purealpha_mvp/
├── src/                      # Основной код
│   ├── api.py               # FastAPI приложение
│   ├── causal_validation.py # Causal AI engine
│   ├── regime_detection.py  # Определение режимов
│   └── portfolio_builder.py # Построение портфелей
├── config/                   # Конфигурация
│   ├── config.json
│   └── asset_universe.json
├── tests/                    # Тесты (pytest)
├── ui/                       # Streamlit dashboard
├── docs/                     # Документация
└── docker/                   # Docker setup
```

---

## 🧪 Тестирование

```bash
# Запусти все тесты
pytest -v

# С coverage
pytest --cov=src --cov-report=html

# Только один модуль
pytest tests/test_causal.py -v
```

---

## 📚 Документация

- [Architecture](docs/ARCHITECTURE.md) — архитектура системы
- [API Documentation](docs/API_DOCUMENTATION.md) — все endpoints
- [Deployment Guide](docs/DEPLOYMENT.md) — деплой в production
- [Notion Presentation](docs/NOTION_PRESENTATION.md) — красивая презентация

---

## 🔧 Конфигурация

Отредактируй `.env`:

```bash
# API Keys
FRED_API_KEY=your-key-here

# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Logging
LOG_LEVEL=INFO
```

---

## 🐛 Troubleshooting

**Проблема:** `ModuleNotFoundError: No module named 'fastapi'`  
**Решение:** `pip install -r requirements.txt`

**Проблема:** API не стартует на порту 8000  
**Решение:** Порт занят, используй `uvicorn src.api:app --port 8001`

**Проблема:** Docker контейнеры не стартуют  
**Решение:** Проверь `docker-compose logs`

---

## 📞 Контакты

- **Email:** hello@purealpha.ai
- **Twitter:** @PureAlphaAI
- **Discord:** [Join community](https://discord.gg/purealpha)

---

## 📄 License

MIT License — см. [LICENSE](LICENSE)

---

**Сделано с ❤️ командой PureAlpha**
