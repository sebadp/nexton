# 🦙 Ollama Setup Guide

Guía para configurar Ollama para usar con el LinkedIn Agent de forma local y gratuita.

---

## 🎯 ¿Por qué Ollama?

- ✅ **Gratis** - Sin API keys ni costos
- ✅ **Local** - Corre en tu máquina, privacidad total
- ✅ **Rápido** - Buena performance con modelos optimizados
- ✅ **Fácil** - Instalación simple

---

## 📥 Instalación

### macOS / Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### macOS con Homebrew

```bash
brew install ollama
```

### Windows

Descarga desde: https://ollama.com/download/windows

---

## 🚀 Configuración

### 1. Iniciar Ollama

```bash
# Inicia el servidor Ollama (corre en background)
ollama serve
```

O simplemente abre la app Ollama si la instalaste con el instalador.

### 2. Descargar Modelos

```bash
# Modelo recomendado: Llama 3.2 (3B) - Rápido y bueno
ollama pull llama3.2

# O Llama 3.2:1b - Más rápido, menos preciso
ollama pull llama3.2:1b

# O Llama 3.1:8b - Más preciso, más lento
ollama pull llama3.1:8b

# O Mistral - Alternativa muy buena
ollama pull mistral
```

### 3. Probar que funciona

```bash
# Chat interactivo
ollama run llama3.2

# Deberías ver:
>>> Hola, ¿cómo estás?
¡Hola! Estoy bien, gracias...

# Presiona Ctrl+D para salir
```

### 4. Configurar el proyecto

Edita tu `.env`:

```bash
# LLM Configuration
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
LLM_MAX_TOKENS=500
LLM_TEMPERATURE=0.7

# Ollama URL (default)
OLLAMA_URL=http://localhost:11434
```

---

## 🧪 Probar con el proyecto

```bash
python test_message_generation.py
```

Deberías ver:

```
🔧 Initializing Components
🧠 Initializing DSPy OpportunityAnalyzer...
✅ OpportunityAnalyzer ready
✍️  Initializing DSPy ResponseGenerator...
✅ ResponseGenerator ready

📥 Step 1: Scraping LinkedIn Messages
...
```

---

## 📊 Modelos Recomendados

### Para Testing / Desarrollo

**llama3.2:1b** (1.3 GB)
- Más rápido
- Bueno para desarrollo
- Respuestas básicas pero funcionales

```bash
ollama pull llama3.2:1b
```

**llama3.2** (2.0 GB) ⭐ **Recomendado**
- Balance perfecto velocidad/calidad
- Bueno para producción
- Respuestas de calidad

```bash
ollama pull llama3.2
```

### Para Producción

**llama3.1:8b** (4.7 GB)
- Mejor calidad
- Más lento
- Respuestas muy buenas

```bash
ollama pull llama3.1:8b
```

**mistral** (4.1 GB)
- Excelente alternativa
- Muy bueno para tareas de análisis
- Respuestas precisas

```bash
ollama pull mistral
```

---

## ⚙️ Modelos por Módulo

Puedes usar diferentes modelos para diferentes tareas:

```bash
# En .env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2

# Analyzer - Puede usar modelo más rápido
ANALYZER_LLM_MODEL=llama3.2:1b

# Scorer - Usa modelo default
# (no especificado = usa LLM_MODEL)

# Response Generator - Usa mejor modelo para respuestas
RESPONSE_LLM_MODEL=llama3.1:8b
```

---

## 🔧 Troubleshooting

### Error: "connection refused" o "Failed to connect to Ollama"

**Causa:** Ollama no está corriendo

**Solución:**
```bash
# Inicia Ollama
ollama serve

# O verifica que esté corriendo
curl http://localhost:11434/api/tags
```

### Error: "model not found"

**Causa:** No has descargado el modelo

**Solución:**
```bash
# Lista modelos disponibles
ollama list

# Si no está, descárgalo
ollama pull llama3.2
```

### Respuestas muy lentas

**Causa:** Modelo demasiado grande para tu hardware

**Solución:**
```bash
# Usa modelo más pequeño
ollama pull llama3.2:1b

# En .env
LLM_MODEL=llama3.2:1b
```

### Respuestas de mala calidad

**Causa:** Modelo demasiado pequeño

**Solución:**
```bash
# Usa modelo más grande
ollama pull llama3.1:8b

# En .env
LLM_MODEL=llama3.1:8b
```

### Error de memoria (Out of Memory)

**Causa:** Tu máquina no tiene suficiente RAM

**Solución:**
```bash
# Usa el modelo más pequeño
ollama pull llama3.2:1b

# O cierra otras aplicaciones
```

---

## 🚀 Comandos Útiles

```bash
# Listar modelos instalados
ollama list

# Ver información de un modelo
ollama show llama3.2

# Eliminar un modelo
ollama rm llama3.2

# Ver logs de Ollama
ollama logs

# Actualizar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Ver modelos disponibles
# Visita: https://ollama.com/library
```

---

## 📊 Comparación de Modelos

| Modelo | Tamaño | RAM Needed | Speed | Quality | Uso Recomendado |
|--------|--------|------------|-------|---------|-----------------|
| llama3.2:1b | 1.3 GB | 4 GB | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | Development/Testing |
| llama3.2 | 2.0 GB | 8 GB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | **General Use** |
| llama3.1:8b | 4.7 GB | 16 GB | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | Production |
| mistral | 4.1 GB | 16 GB | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | Analysis Tasks |

---

## 🔄 Cambiar de Ollama a Anthropic/OpenAI

Si luego quieres usar API en la nube:

```bash
# En .env, cambia a:
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-...

# O OpenAI:
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
OPENAI_API_KEY=sk-...
```

El código funciona igual con cualquier provider.

---

## 💡 Tips

1. **Primera vez:** Usa `llama3.2` (balance perfecto)
2. **Testing rápido:** Usa `llama3.2:1b`
3. **Producción:** Usa `llama3.1:8b` o `mistral`
4. **Análisis complejo:** Usa `llama3.1:8b`
5. **Respuestas simples:** Usa `llama3.2:1b`

---

## 📚 Recursos

- Ollama Homepage: https://ollama.com
- Modelos disponibles: https://ollama.com/library
- Ollama GitHub: https://github.com/ollama/ollama
- DSPy + Ollama: https://github.com/stanfordnlp/dspy

---

**¡Listo!** Ahora puedes usar el LinkedIn Agent sin costos de API 🎉
