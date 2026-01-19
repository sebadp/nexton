# 🚀 Quick Start con Ollama

Guía rápida para comenzar a usar el LinkedIn Agent con Ollama (gratis y local).

---

## ⚡ Inicio Rápido (5 minutos)

### 1. Instala Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Descarga el modelo

```bash
ollama pull llama3.2
```

### 3. Inicia Ollama

```bash
ollama serve
```

O simplemente abre la app Ollama si la instalaste con instalador.

### 4. Configura el proyecto

```bash
# Copia el .env de ejemplo
cp .env.example .env

# Edita el .env y configura:
# - LINKEDIN_EMAIL=tu@email.com
# - LINKEDIN_PASSWORD=tupassword
# - LLM_PROVIDER=ollama
# - LLM_MODEL=llama3.2

# O usando comandos:
echo "LINKEDIN_EMAIL=tu@email.com" >> .env
echo "LINKEDIN_PASSWORD='tupassword'" >> .env
echo "LLM_PROVIDER=ollama" >> .env
echo "LLM_MODEL=llama3.2" >> .env
```

### 5. Instala dependencias

```bash
pip install -r requirements.txt
playwright install chromium
```

### 6. ¡Pruébalo!

```bash
python test_message_generation.py
```

---

## 🎯 Qué hace

1. Se conecta a tu LinkedIn
2. Scrapea 3 mensajes recientes
3. Analiza cada mensaje con IA (usando Ollama local)
4. Genera respuesta personalizada automática
5. Muestra todo en la terminal (NO envía nada)

---

## 📋 Output esperado

```
================================================================================
  🤖 LinkedIn Message Generation Test
================================================================================

📧 Email: tu@email.com
📍 Using DSPy model: ollama/llama3.2

🔧 Initializing Components
🧠 Initializing DSPy OpportunityAnalyzer...
✅ OpportunityAnalyzer ready
✍️  Initializing DSPy ResponseGenerator...
✅ ResponseGenerator ready

📥 Step 1: Scraping LinkedIn Messages
🔐 Logging in to LinkedIn...
✅ Login successful!
✅ Found 3 messages

📩 Message 1/3
👤 From: Sarah Johnson - Tech Recruiter
💬 Original Message: Hi! I came across your profile...

🔍 Analyzing opportunity...
📊 Analysis Results:
   Company: TechCorp
   Role: Senior Backend Engineer
   Salary: $160k-$200k
   Tech Stack: Python, FastAPI, PostgreSQL
   📈 Total Score: 86/100
   🎯 Tier: A

✍️  Generating AI response...
🤖 Generated Response:
========================================
Hi Sarah,

Thank you for reaching out! I'm very
interested in learning more about the
Senior Backend Engineer position at
TechCorp...
========================================
```

---

## ⚠️ Troubleshooting

### "Failed to connect to Ollama"

**Solución:**
```bash
# Verifica que Ollama esté corriendo
curl http://localhost:11434/api/tags

# Si no responde, inícialo:
ollama serve
```

### "Model not found"

**Solución:**
```bash
# Descarga el modelo
ollama pull llama3.2

# Verifica que esté instalado
ollama list
```

### "Login failed" o "Selector not found"

**Solución:**
```bash
# Ejecuta con browser visible para ver qué pasa
python test_scraper_quick.py

# LinkedIn podría necesitar verificación
# Inicia sesión manualmente primero en tu navegador
```

### Respuestas muy genéricas o malas

**Solución:**
```bash
# Usa un modelo más grande
ollama pull llama3.1:8b

# En .env:
LLM_MODEL=llama3.1:8b
```

---

## 🎛️ Personalización

### Usar modelo más rápido

```bash
# En .env
LLM_MODEL=llama3.2:1b
```

### Usar modelo más preciso

```bash
# En .env
LLM_MODEL=llama3.1:8b
```

### Analizar más mensajes

Edita `test_message_generation.py` línea 97:

```python
messages = await scraper.scrape_messages(limit=10, unread_only=False)
```

### Solo mensajes no leídos

```python
messages = await scraper.scrape_messages(limit=5, unread_only=True)
```

---

## 📚 Siguiente paso

Ver documentación completa:
- `OLLAMA_SETUP.md` - Setup detallado de Ollama
- `MESSAGE_GENERATION_TEST.md` - Guía completa del test script
- `SCRAPER_TESTING_README.md` - Testing del scraper

---

## 💡 Comandos útiles

```bash
# Test solo scraper
python test_scraper_quick.py

# Test con generación de respuestas
python test_message_generation.py

# Ver modelos instalados
ollama list

# Cambiar modelo
ollama pull mistral
# Edita .env: LLM_MODEL=mistral

# Ver logs de Ollama
# En macOS/Linux: Ver terminal donde corre ollama serve
# En Windows: Ver app de Ollama
```

---

**¡Listo para empezar!** 🎉

Si algo no funciona, revisa las guías detalladas o los logs de error.
