# 🤖 LinkedIn Message Generation Test

Script para probar el pipeline completo de generación de respuestas sin enviar nada a LinkedIn.

---

## 🎯 Qué hace este script

1. **Scrapea mensajes reales** de tu LinkedIn (últimos 3 mensajes)
2. **Analiza cada mensaje** con DSPy:
   - Extrae: empresa, rol, salario, tech stack, ubicación
   - Calcula scores de match
   - Asigna tier (A/B/C/D)
3. **Genera respuesta automática** personalizada con IA
4. **Muestra todo en la terminal** - NO envía nada

---

## 🚀 Cómo usar

### Requisitos previos

Asegúrate de tener en tu `.env`:

```bash
# LinkedIn credentials
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=yourpassword

# LLM Configuration - Ollama (Local, Gratis)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_URL=http://localhost:11434

# O usa Anthropic Claude (API, Paid)
# LLM_PROVIDER=anthropic
# LLM_MODEL=claude-3-5-sonnet-20241022
# ANTHROPIC_API_KEY=sk-ant-...

# O usa OpenAI (API, Paid)
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4
# OPENAI_API_KEY=sk-...
```

**Para usar Ollama (recomendado para testing):**
```bash
# 1. Instala Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Descarga el modelo
ollama pull llama3.2

# 3. Inicia Ollama
ollama serve
```

### Ejecutar el test

```bash
python test_message_generation.py
```

---

## 📋 Output esperado

```
================================================================================
  🤖 LinkedIn Message Generation Test
================================================================================

📧 Email: your@email.com
🔒 Password: **********
📍 Using DSPy model: ollama/llama3.2

--------------------------------------------------------------------------------
  🔧 Initializing Components
--------------------------------------------------------------------------------

🧠 Initializing DSPy OpportunityAnalyzer...
✅ OpportunityAnalyzer ready
✍️  Initializing DSPy ResponseGenerator...
✅ ResponseGenerator ready

--------------------------------------------------------------------------------
  📥 Step 1: Scraping LinkedIn Messages
--------------------------------------------------------------------------------

🔐 Logging in to LinkedIn...
✅ Login successful!

📨 Fetching messages...
✅ Found 3 messages

--------------------------------------------------------------------------------
  📩 Message 1/3
--------------------------------------------------------------------------------

👤 From: Sarah Johnson - Tech Recruiter
📅 Date: 2026-01-18 10:30
🔗 URL: https://www.linkedin.com/messaging/thread/2-ABC123.../

💬 Original Message:
----------------------------------------
Hi! I came across your profile and was
impressed by your experience with Python
and FastAPI. We have an exciting Senior
Backend Engineer position at TechCorp
($160k-$200k) that I think would be
perfect for you...
----------------------------------------

🔍 Analyzing opportunity...

📊 Analysis Results:
   Company: TechCorp
   Role: Senior Backend Engineer
   Salary: $160k-$200k
   Location: Remote
   Work Mode: remote
   Tech Stack: Python, FastAPI, PostgreSQL

   📈 Scores:
      Tech Match: 90/100
      Salary Match: 85/100
      Seniority Match: 95/100
      Company Score: 75/100
      TOTAL: 86/100

   🎯 Tier: A
   📝 Summary: High-match opportunity for Senior Backend role...

✍️  Generating AI response...

🤖 Generated Response:
========================================
Hi Sarah,

Thank you for reaching out! I'm
definitely interested in learning more
about the Senior Backend Engineer
position at TechCorp. The tech stack
aligns well with my experience...

Would you be available for a quick call
this week to discuss the role in more
detail?

Best regards,
Sebastian
========================================

   Tone: professional_interested
   Length: 287 characters
   Key Points: interest, availability, tech_stack_match
   Reasoning: High tier opportunity with strong match...
```

---

## ⚙️ Personalización

### Cambiar número de mensajes

Edita línea 97 en `test_message_generation.py`:

```python
# De 3 a 5 mensajes
messages = await scraper.scrape_messages(limit=5, unread_only=False)

# Solo mensajes no leídos
messages = await scraper.scrape_messages(limit=3, unread_only=True)
```

### Cambiar modelo

En tu `.env`:

```bash
# Ollama (Local, Gratis)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2         # Balance velocidad/calidad ⭐
# LLM_MODEL=llama3.2:1b    # Más rápido
# LLM_MODEL=llama3.1:8b    # Más preciso
# LLM_MODEL=mistral        # Alternativa excelente

# Anthropic (Cloud, Paid)
# LLM_PROVIDER=anthropic
# LLM_MODEL=claude-3-5-sonnet-20241022  # Recomendado
# LLM_MODEL=claude-opus-4-20250514      # Más preciso

# OpenAI (Cloud, Paid)
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4          # Bueno
# LLM_MODEL=gpt-4-turbo    # Más rápido
```

Si cambias a un modelo Ollama diferente, descárgalo primero:
```bash
ollama pull llama3.1:8b
```

---

## 🐛 Troubleshooting

### Error: "Failed to initialize DSPy"

**Causa:** Ollama no está corriendo o modelo no instalado

**Solución:**
```bash
# Verifica que Ollama esté corriendo
curl http://localhost:11434/api/tags

# Si no responde, inícialo:
ollama serve

# Verifica que el modelo esté instalado
ollama list

# Si no está, descárgalo:
ollama pull llama3.2
```

Si usas Anthropic/OpenAI:
```bash
# Verifica que tengas la API key
echo $ANTHROPIC_API_KEY  # o $OPENAI_API_KEY

# Si no existe, agrégala a .env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
```

### Error: "No messages found"

**Causa:** No hay mensajes en tu LinkedIn o todos fueron filtrados

**Solución:**
```python
# Cambia unread_only a False para ver todos los mensajes
messages = await scraper.scrape_messages(limit=5, unread_only=False)
```

### Respuestas genéricas o de mala calidad

**Causa:** Modelo demasiado pequeño o prompt necesita ajuste

**Solución:**
```bash
# 1. Usa un modelo más grande
ollama pull llama3.1:8b

# En .env:
LLM_MODEL=llama3.1:8b

# O usa modelo cloud (más preciso pero de pago)
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-...
```

2. Revisa `app/dspy_pipeline/response_generator.py` y ajusta prompts
3. Añade ejemplos de few-shot learning si es necesario

---

## 📊 Qué mide el análisis

### Tech Match Score (0-100)
- Stack tecnológico coincidente
- Frameworks/herramientas que conoces
- Lenguajes de programación

### Salary Match Score (0-100)
- Comparación con tu rango esperado
- Configurado en `app/core/config.py`

### Seniority Match Score (0-100)
- Junior/Mid/Senior/Staff/Principal
- Comparado con tu nivel actual

### Company Score (0-100)
- Startup vs Enterprise
- Prestigio/reconocimiento
- Cultura/valores

### Total Score
- Promedio ponderado de los 4 scores
- Determina el tier (A/B/C/D)

---

## 🎯 Tiers

- **A (80-100)**: Alta prioridad - Respuesta entusiasta
- **B (60-79)**: Prioridad media - Respuesta interesada
- **C (40-59)**: Prioridad baja - Respuesta cortés
- **D (0-39)**: No interesa - Respuesta educada de rechazo

---

## 🔄 Flujo completo del sistema

Este test muestra solo los pasos 1-3:

```
1. 📥 Scrape LinkedIn     ← Este script
2. 🤖 Analyze with DSPy   ← Este script
3. ✍️  Generate response  ← Este script
4. 📧 Send email notification (no incluido)
5. 👤 User reviews/approves (no incluido)
6. 📤 Send to LinkedIn (no incluido)
```

Para el flujo completo, usa la aplicación web principal.

---

## 💡 Próximos pasos

Una vez que este test funcione bien:

1. ✅ **Integrar con la app principal**
   ```bash
   docker-compose up -d
   ```

2. ✅ **Configurar Celery para scraping automático**
   - Scrapea cada X horas
   - Procesa mensajes automáticamente
   - Envía notificaciones por email

3. ✅ **Agregar workflow de aprobación**
   - Web UI para revisar respuestas
   - Editar antes de enviar
   - Aprobar/rechazar con un click

4. ✅ **Monitoreo y métricas**
   - Prometheus + Grafana
   - Tasa de respuesta
   - Calidad de matches

---

## 📚 Archivos relacionados

- `test_scraper.py` - Test solo scraping
- `test_scraper_quick.py` - Test rápido scraping
- `test_scraper_demo.py` - Demo con datos mock
- `test_message_generation.py` - **Este script**
- `app/dspy_pipeline/opportunity_analyzer.py` - Lógica de análisis
- `app/dspy_pipeline/response_generator.py` - Lógica de generación

---

**Última actualización:** 2026-01-18
