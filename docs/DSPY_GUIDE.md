# Guía de Aprendizaje: DSPy Optimizers

Esta guía explica qué son los DSPy Optimizers, por qué son fundamentales para "programar" LLMs en lugar de solo promptearlos, y cómo implementarlos en tu proyecto.

---

## 1. ¿Qué es un DSPy Optimizer?

Un **Optimizer** (antes llamado "Teleprompter") es un algoritmo que **mejora automáticamente** tu programa DSPy.

En el paradigma tradicional de LLM, tú escribes el prompt manualmente, lo pruebas, lo corriges, y repites ("Prompt Engineering"). En DSPy, tú defines la **lógica** (Módulos) y la **calidad deseada** (Métricas), y el Optimizer se encarga de "compilar" el prompt perfecto para ti.

### ¿Qué optimiza exactamente?
1. **Instrucciones**: Reescribe la descripción de la tarea para que el LLM la entienda mejor.
2. **Ejemplos (Few-Shot)**: Selecciona, genera y refina los mejores ejemplos para incluir en el prompt.
3. **Pesos (Fine-tuning)**: En casos avanzados, puede fine-tunear un modelo pequeño (ej. Llama-3-8B) para que actúe como GPT-4.

---

## 2. Los 3 Pilares de la Optimización

Para ejecutar cualquier optimizer, necesitas tres cosas:

### A. El Programa (`dspy.Module`)
Tu código actual. Por ejemplo, tu `OpportunityPipeline`.
```python
class MiPipeline(dspy.Module):
    def forward(self, message):
        # ... lógica de análisis ...
        return resultado
```

### B. La Métrica (`Metric`)
Una función que recibe la salida y `truth` (la verdad esperada) y devuelve un puntaje (numérico o booleano).
```python
def mi_metrica(example, pred, trace=None):
    # ¿El estado detectado (NEW_OPPORTUNITY) es correcto?
    return example.expected_state == pred.conversation_state.state
```

### C. El Dataset (`Trainset`)
Una lista de ejemplos (`dspy.Example`) para que el optimizer aprenda.
- **BootstrapFewShot**: Funciona bien con **10-20 ejemplos**.
- **MIPROv2**: Idealmente **50+ ejemplos** (aunque tiene modo "light").

---

## 3. Principales Optimizers (2024/2025)

DSPy tiene muchos, pero hoy en día solo necesitas conocer estos dos para el 95% de los casos:

### 🌟 1. BootstrapFewShot (El "Caballito de Batalla")
**Ideal para:** Empezar. Pocos datos (10 ejemplos).
**Cómo funciona:**
1. Toma tus preguntas de entrenamiento.
2. Usa un "Teacher" (usualmente el mismo modelo potente) para generar respuestas.
3. Verifica si las respuestas pasan tu `Métrica`.
4. Si pasan, guarda ese par (Pregunta + Respuesta Generada) como un "Demo" verificado.
5. Inyecta estos Demos probados en tu prompt final.

### 🚀 2. MIPROv2 (Multiprompt Instruction Proposal Optimizer)
**Ideal para:** Máximo rendimiento. Optimizar pipeline completo.
**Cómo funciona:**
Es mucho más inteligente. Usa Optimización Bayesiana para buscar la mejor combinación de:
- **Instrucciones**: Reescribe tus `docstrings` y descripciones de campos.
- **Ejemplos**: Selecciona qué demos mostrar y en qué orden.
**Coste:** Requiere más llamadas al LLM durante el entrenamiento, pero produce mejores resultados.

---

## 4. Cómo Implementar un Optimizer Paso a Paso

Aquí tienes un flujo de trabajo estándar para tu proyecto `nexton`.

### Paso 1: Definir Datos de Entrenamiento
Crea un archivo `training_data.py`.
```python
import dspy

trainset = [
    dspy.Example(
        message="Hola, busco un Java Dev...",
        expected_state="NEW_OPPORTUNITY"
    ).with_inputs("message"),
    
    dspy.Example(
        message="Gracias por tu tiempo",
        expected_state="COURTESY_CLOSE"
    ).with_inputs("message"),
    # ... más ejemplos
]
```

### Paso 2: Configurar y Ejecutar (BootstrapFewShot)
```python
from dspy.teleprompt import BootstrapFewShot
from app.dspy_modules.pipeline import OpportunityPipeline
from app.dspy_modules.training_data import trainset

# 1. Definir métrica
def validate_state(example, pred, trace=None):
    return example.expected_state == pred.conversation_state.state

# 2. Configurar Optimizer
optimizer = BootstrapFewShot(
    metric=validate_state,
    max_bootstrapped_demos=4,  # Cuántos ejemplos inventados incluir en el prompt
    max_labeled_demos=4,       # Cuántos ejemplos reales tuyos usar
)

# 3. Compilar (Aquí ocurre la magia ✨)
# El optimizer ejecuta el pipeline, prueba variantes y aprende.
compiled_pipeline = optimizer.compile(OpportunityPipeline(), trainset=trainset)
```

### Paso 3: Guardar y Cargar
Una vez optimizado, guardas el resultado. Ya no necesitas re-entrenar cada vez.
```python
# Guardar
compiled_pipeline.save("app/dspy_modules/optimized_pipeline.json")

# Cargar en producción
pipeline_prod = OpportunityPipeline()
pipeline_prod.load("app/dspy_modules/optimized_pipeline.json")
```

---

## 5. Buenas Prácticas ("The DSPy Zen")

1. **Empieza sin Optimizar (Zero-Shot)**: Asegúrate que tus signatures y lógica básica funcionan bien "a secas" antes de optimizar.
2. **La Métrica es el Jefe**: Si tu métrica es mala, la optimización será mala. Dedica tiempo a definir qué es el "éxito". Para generación de texto (ResponseGenerator), usa métricas LLM-as-a-Judge (usar otro LLM para puntuar).
3. **MIPROv2 es el Rey**: Si tienes presupuesto de tokens y ~50 ejemplos, usa MIPROv2. Es capaz de encontrar matices en las instrucciones que a ti se te pasarían por alto.
4. **Itera sobre los Datos, no los Prompts**: Si el modelo falla, no cambies el prompt manual. Añade un ejemplo al `trainset` que cubra ese caso de fallo y re-compila. **Esto es DSPy.**

## Resumen para tu Caso de Uso (Nexton)

Dado que tienes módulos de clasificación (`ConversationState`) y extracción (`MessageAnalyzer`), el plan ideal es:

1. Crear ~20 ejemplos manuales variados.
2. Usar **BootstrapFewShot** primero para asegurar que el formato de salida sea siempre perfecto.
3. Evaluar resultados.
4. Si quieres mejorar el tono de las respuestas (`ResponseGenerator`), pasar a MIPROv2 para que encuentre el "estilo" de instrucción perfecto.
