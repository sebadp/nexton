# 👤 Configuración de Perfil de Usuario

## 📝 Descripción

El sistema ahora usa el archivo `config/profile.yaml` para cargar dinámicamente la información del usuario, incluyendo su nombre para la detección automática de mensajes propios.

---

## 🎯 Beneficios

1. **✅ Sin Código Hardcodeado**: Tu nombre ya no está en el código
2. **✅ Fácil Configuración**: Cambia tu perfil editando un archivo YAML
3. **✅ Reutilizable**: Funciona para cualquier usuario
4. **✅ Detección Inteligente**: Genera automáticamente variaciones de tu nombre

---

## 📁 Archivo de Configuración

**Ubicación:** `config/profile.yaml`

### Estructura

```yaml
# Personal Information
name: "Sebastián Dávila"

# Skills and Experience
preferred_technologies:
  - Python
  - FastAPI
  - Docker
  # ...

years_of_experience: 5
current_seniority: "Senior"

# Compensation Expectations (in USD)
minimum_salary_usd: 80000
ideal_salary_usd: 120000

# Work Preferences
preferred_remote_policy: "Remote"
preferred_locations:
  - "Remote"
  - "Argentina"

# Company Preferences
preferred_company_size: "Mid-size"
industry_preferences:
  - "Technology"
  - "AI/ML"
  # ...
```

---

## 🔍 Detección de Mensajes Propios

### Cómo Funciona

El sistema detecta si un mensaje es tuyo usando **4 estrategias**:

#### 1. **Clases CSS de LinkedIn**
Busca clases con "self" en el mensaje.

#### 2. **Indicador "You"**
Busca atributos `data-test-link-to-profile-for="self"`.

#### 3. **Texto del Remitente**
Busca "You", "Tú", "Tu" en el texto del remitente.

#### 4. **Detección por Firma** ⭐ **USA TU PERFIL**
Busca tu nombre o frases comunes al final del mensaje.

### Variaciones de Nombre

El sistema genera automáticamente variaciones de tu nombre:

**Ejemplo:** Si tu nombre es `"Sebastián Dávila"`:

- ✅ `Sebastián Dávila` (nombre completo)
- ✅ `Sebastián` (primer nombre)
- ✅ `Sebastian` (sin acento)
- ✅ `sebastián` (lowercase)
- ✅ `sebastian` (lowercase sin acento)

### Frases Comunes

También detecta frases comunes de cierre:

- `¡abrazo!`, `abrazo!`
- `saludos`
- `thanks`, `thank you`
- `regards`, `best regards`
- `cheers`
- `cordialmente`
- `un abrazo`
- `muchas gracias`

---

## 🚀 Cómo Usar

### 1. Edita tu perfil

```bash
nano config/profile.yaml
# O usa tu editor favorito
```

### 2. Actualiza tu nombre

```yaml
name: "Tu Nombre Completo"
```

### 3. Ejecuta el scraper

```bash
python test_message_generation.py
```

El sistema automáticamente:
1. ✅ Carga tu perfil
2. ✅ Genera variaciones de tu nombre
3. ✅ Detecta tus mensajes usando tu nombre

---

## 📊 Ejemplo de Output

```
2026-01-18T22:06:55.445123Z [debug] loaded_user_profile
    name='Sebastián Dávila'
    variations=['Sebastián Dávila', 'Sebastián', 'Sebastian', 'sebastián dávila', 'sebastián', 'sebastian']

2026-01-18T22:06:55.445234Z [debug] signature_detected
    is_from_user=True
    signature='sebastián'

2026-01-18T22:06:55.445345Z [info] message_sender_detection_result
    is_from_user=True
```

```
📩 Message 1/3
👤 From: Recruiter Name
⚠️  Last message is FROM YOU - Skipping response generation

💬 Original Message:
...
¡Abrazo!
Sebastián
----------------------------------------

⏭️  Skipping - waiting for recruiter's response
```

---

## 🔧 API de Profile

### Cargar el Perfil

```python
from app.core.profile import get_user_profile

# Get profile (singleton - loads once)
profile = get_user_profile()

# Access fields
print(profile.name)                    # "Sebastián Dávila"
print(profile.first_name)              # "Sebastián"
print(profile.name_variations)         # ['Sebastián', 'Sebastian', ...]
print(profile.years_of_experience)     # 5
print(profile.current_seniority)       # "Senior"
print(profile.preferred_technologies)  # ['Python', 'FastAPI', ...]
```

### Propiedades Disponibles

```python
profile.name                      # Nombre completo
profile.first_name               # Primer nombre
profile.name_variations          # Lista de variaciones
profile.preferred_technologies   # Lista de tecnologías
profile.years_of_experience      # Años de experiencia
profile.current_seniority       # Junior/Mid/Senior/Staff/Principal
profile.minimum_salary_usd      # Salario mínimo
profile.ideal_salary_usd        # Salario ideal
profile.preferred_remote_policy # Remote/Hybrid/Flexible
profile.preferred_locations     # Lista de ubicaciones
profile.preferred_company_size  # Startup/Mid-size/Enterprise
profile.industry_preferences    # Lista de industrias
profile.open_to_relocation      # bool
profile.looking_for_change      # bool
profile.notes                   # Notas adicionales
```

---

## 🔮 Uso Futuro

Este perfil se usará también para:

1. **Análisis de Oportunidades**
   - Matching de tech stack con `preferred_technologies`
   - Scoring basado en salario vs `minimum_salary_usd`
   - Matching de seniority con `current_seniority`

2. **Generación de Respuestas**
   - Personalizar respuestas con tu información
   - Mencionar tecnologías que conoces
   - Incluir expectativas de salario relevantes

3. **Filtrado Automático**
   - Filtrar por ubicación
   - Filtrar por tipo de empresa
   - Filtrar por industria

---

## ⚠️ Notas Importantes

1. **No Commitear Datos Personales**
   - El `profile.yaml` debe estar en `.gitignore`
   - Usa `profile.yaml.example` como template

2. **Validación**
   - El sistema valida que el archivo existe
   - Registra errores si falta información
   - Usa valores por defecto si es necesario

3. **Singleton Pattern**
   - El perfil se carga una vez por ejecución
   - Cambios en el archivo requieren reiniciar

---

## 🧪 Testing

Puedes probar que tu perfil se carga correctamente:

```bash
python -c "
from app.core.profile import get_user_profile

profile = get_user_profile()
print('Name:', profile.name)
print('First Name:', profile.first_name)
print('Variations:', profile.name_variations)
print('Seniority:', profile.current_seniority)
print('Technologies:', profile.preferred_technologies[:5])
"
```

---

**Última actualización:** 2026-01-18
