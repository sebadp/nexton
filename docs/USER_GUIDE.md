# LinkedIn Agent - Guía de Usuario

Guía completa para configurar y usar el LinkedIn Agent con el dashboard web.

## Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Instalación Rápida](#instalación-rápida)
3. [Configuración Inicial](#configuración-inicial)
4. [Iniciar la Aplicación](#iniciar-la-aplicación)
5. [Usando el Dashboard](#usando-el-dashboard)
6. [Flujo de Trabajo](#flujo-de-trabajo)
7. [Solución de Problemas](#solución-de-problemas)

---

## Requisitos Previos

### Software Requerido

- **Docker** y **Docker Compose** (v2.0+)
- **Ollama** (para LLM local) o API key de OpenAI/Anthropic
- Cuenta de **LinkedIn** con mensajes de reclutadores

### Puertos Utilizados

| Puerto | Servicio |
|--------|----------|
| 3000 | Frontend (Dashboard) |
| 8000 | Backend API |
| 5432 | PostgreSQL |
| 6379 | Redis |
| 5555 | Flower (Monitor Celery) |
| 8025 | Mailpit (Emails dev) |

---

## Instalación Rápida

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd nexton
```

### 2. Crear archivo de configuración

```bash
cp .env.example .env
```

### 3. Configurar credenciales de LinkedIn

Edita el archivo `.env`:

```env
# LinkedIn Credentials (REQUERIDO)
LINKEDIN_EMAIL=tu-email@ejemplo.com
LINKEDIN_PASSWORD=tu-contraseña

# LLM Provider (elige uno)
LLM_PROVIDER=ollama          # Local (gratis)
# LLM_PROVIDER=openai        # Requiere API key
# LLM_PROVIDER=anthropic     # Requiere API key

# Si usas Ollama (recomendado para empezar)
LLM_MODEL=llama3.1
OLLAMA_URL=http://host.docker.internal:11434

# Si usas OpenAI
# OPENAI_API_KEY=sk-...

# Si usas Anthropic
# ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Iniciar Ollama (si usas LLM local)

```bash
# Instalar Ollama: https://ollama.ai
ollama pull llama3.1
ollama serve
```

### 5. Iniciar la aplicación

```bash
docker-compose up -d
```

### 6. Acceder al Dashboard

Abre tu navegador en: **http://localhost:3000**

---

## Configuración Inicial

### Configurar tu Perfil

El perfil determina cómo se evalúan las oportunidades. Es **crítico** configurarlo bien.

1. Abre **http://localhost:3000/profile**
2. Completa cada sección:

#### Información Personal
- **Name**: Tu nombre completo
- **Years of Experience**: Años de experiencia
- **Current Seniority**: Junior, Mid, Senior, Staff, Principal
- **Tech Stack**: Agrega tus tecnologías (Python, React, AWS, etc.)

#### Compensación
- **Minimum Salary (USD)**: Mínimo aceptable anual
- **Ideal Salary (USD)**: Tu objetivo salarial

#### Preferencias de Trabajo
- **Remote Policy**: Remote, Hybrid, Flexible, On-site
- **Work Week**: 4-days, 5-days, flexible
- **Company Size**: Startup, Mid-size, Enterprise
- **Locations**: Ubicaciones preferidas (ej: "Remote", "Argentina", "USA")
- **Industries**: Industrias de interés (ej: "AI/ML", "Fintech", "SaaS")

#### Estado de Búsqueda
- **Currently Employed**: ¿Estás empleado actualmente?
- **Actively Looking**: ¿Estás buscando activamente?
- **Urgency**: urgent, moderate, selective, not_looking
- **Situation**: Describe tu situación brevemente
- **Must Have**: Requisitos obligatorios (ej: "4-day work week", "Remote")
- **Nice to Have**: Preferencias (ej: "Equity", "Learning budget")
- **Reject If**: Deal breakers (ej: "Crypto only", "Consulting firms")

3. Click en **Save Changes**

---

## Iniciar la Aplicación

### Modo Desarrollo (con hot-reload del frontend)

```bash
# Backend + servicios
docker-compose up -d postgres redis mailpit app celery-worker celery-beat

# Frontend en modo desarrollo
cd frontend
npm install
npm run dev
```

### Modo Producción

```bash
docker-compose up -d
```

### Ver logs

```bash
# Todos los servicios
docker-compose logs -f

# Solo el backend
docker-compose logs -f app

# Solo el worker (scraping)
docker-compose logs -f celery-worker
```

### Detener todo

```bash
docker-compose down
```

---

## Usando el Dashboard

### Dashboard Principal (`/dashboard`)

El dashboard muestra:

1. **LinkedIn Scanner** - Botón para escanear mensajes
2. **Stats Cards** - Resumen de oportunidades
3. **Tier Chart** - Distribución por prioridad
4. **Recent Opportunities** - Últimas oportunidades

#### Escanear LinkedIn

1. Click en **"Scan LinkedIn"**
2. Confirma en el dialog
3. Espera mientras escanea (puedes ver el progreso)
4. Las nuevas oportunidades aparecerán automáticamente

### Oportunidades (`/opportunities`)

Lista todas las oportunidades con filtros:

- **Buscar** por empresa
- **Filtrar** por tier (High Priority, Interesting, etc.)
- **Filtrar** por estado (new, processed, etc.)
- **Filtrar** por score mínimo

#### Detalle de Oportunidad

Click en cualquier oportunidad para ver:

- Información extraída (empresa, rol, salario, tech stack)
- Desglose de scores
- Mensaje original del reclutador
- Respuesta generada por AI

### Respuestas (`/responses`)

Gestiona las respuestas pendientes:

1. **Pending** - Respuestas esperando tu aprobación
2. **Approved** - Respuestas aprobadas (listas para enviar)
3. **Declined** - Respuestas rechazadas

#### Aprobar una respuesta

1. Revisa el texto generado
2. Click **"Approve"** para aprobar como está
3. O click **"Edit"** para modificar antes de aprobar
4. Click **"Decline"** si no quieres responder

### Perfil (`/profile`)

Edita tus preferencias de búsqueda (ver sección de configuración).

### Settings (`/settings`)

Configura:

- **LLM**: Provider, modelo, temperatura
- **LinkedIn**: Credenciales
- **Email**: Configuración SMTP
- **Notifications**: Habilitar/deshabilitar

---

## Flujo de Trabajo

### Flujo Típico Diario

```
1. Abrir Dashboard (http://localhost:3000)
           ↓
2. Click "Scan LinkedIn"
           ↓
3. Esperar escaneo (1-2 min típicamente)
           ↓
4. Revisar nuevas oportunidades en el Dashboard
           ↓
5. Click en oportunidades interesantes para ver detalle
           ↓
6. Ir a "Responses" para ver respuestas pendientes
           ↓
7. Aprobar/Editar/Rechazar cada respuesta
           ↓
8. Las respuestas aprobadas se envían a LinkedIn automáticamente
```

### Sistema de Tiers

Las oportunidades se clasifican automáticamente:

| Tier | Color | Significado |
|------|-------|-------------|
| **HIGH_PRIORITY** | Verde | Match excelente (>80%) - Responder rápido |
| **INTERESANTE** | Amarillo | Buen match (60-80%) - Vale la pena revisar |
| **POCO_INTERESANTE** | Naranja | Match bajo (40-60%) - Revisar si hay tiempo |
| **NO_INTERESA** | Rojo | Sin match (<40%) - Probablemente ignorar |

### Sistema de Scoring

Cada oportunidad recibe puntuación en 4 áreas:

1. **Tech Stack Score** - ¿Usan tus tecnologías preferidas?
2. **Salary Score** - ¿Está en tu rango salarial?
3. **Seniority Score** - ¿Corresponde a tu nivel?
4. **Company Score** - ¿Es el tipo de empresa que buscas?

**Total Score** = Promedio ponderado de las 4 áreas

---

## Solución de Problemas

### El scraping falla

**Problema**: Error al conectar a LinkedIn

**Soluciones**:
1. Verifica credenciales en `.env`
2. LinkedIn puede pedir verificación - ingresa manualmente una vez
3. No uses VPN durante el primer login
4. Espera unos minutos si hay rate limiting

```bash
# Ver logs del worker
docker-compose logs -f celery-worker
```

### No se procesan mensajes

**Problema**: Scraping funciona pero no hay oportunidades

**Soluciones**:
1. Verifica que Ollama esté corriendo: `ollama list`
2. Revisa logs del worker para errores de LLM
3. Verifica conexión a Ollama: `curl http://localhost:11434/api/tags`

### El frontend no carga

**Problema**: http://localhost:3000 no responde

**Soluciones**:
```bash
# Verificar que el contenedor esté corriendo
docker-compose ps

# Reconstruir si es necesario
docker-compose up -d --build frontend
```

### Base de datos vacía

**Problema**: No hay datos después de reiniciar

**Solución**: Los datos persisten en volúmenes Docker
```bash
# Ver volúmenes
docker volume ls | grep nexton

# Si necesitas resetear todo
docker-compose down -v  # CUIDADO: borra todos los datos
docker-compose up -d
```

### Health check falla

**Problema**: El header muestra "Unhealthy"

**Revisar cada servicio**:
```bash
# Base de datos
docker-compose exec postgres pg_isready

# Redis
docker-compose exec redis redis-cli ping

# Ollama (fuera de Docker)
curl http://localhost:11434/api/tags
```

---

## Comandos Útiles

### Docker

```bash
# Ver estado de servicios
docker-compose ps

# Reiniciar un servicio
docker-compose restart app

# Ver logs en tiempo real
docker-compose logs -f

# Reconstruir todo
docker-compose up -d --build

# Limpiar todo (BORRA DATOS)
docker-compose down -v
```

### Celery (tareas en background)

```bash
# Ver tareas activas
docker-compose exec celery-worker celery -A app.tasks.celery_app inspect active

# Ver tareas programadas
docker-compose exec celery-worker celery -A app.tasks.celery_app inspect scheduled

# Monitor web de Celery
open http://localhost:5555  # Usuario: admin, Password: admin
```

### Base de datos

```bash
# Conectar a PostgreSQL
docker-compose exec postgres psql -U user -d linkedin_agent

# Ver oportunidades
SELECT id, company, role, tier, total_score FROM opportunities ORDER BY created_at DESC LIMIT 10;

# Ver respuestas pendientes
SELECT * FROM pending_responses WHERE status = 'pending';
```

---

## URLs de Acceso

| URL | Descripción |
|-----|-------------|
| http://localhost:3000 | Dashboard principal |
| http://localhost:8000/docs | API Documentation (Swagger) |
| http://localhost:8000/redoc | API Documentation (ReDoc) |
| http://localhost:5555 | Flower (Celery monitor) |
| http://localhost:8025 | Mailpit (emails en dev) |

---

## Próximos Pasos

1. **Configura tu perfil** completamente para mejores resultados
2. **Ejecuta el primer scan** y revisa las oportunidades
3. **Ajusta tu perfil** basándote en los resultados
4. **Configura el scraping automático** si lo deseas (9 AM UTC por defecto)

---

## Soporte

- **Issues**: Reporta problemas en el repositorio de GitHub
- **Docs**: Revisa `/docs` para documentación técnica adicional
