---
description: Optimización de queries SQL en SQLAlchemy - usar GROUP BY en lugar de queries individuales
---

# Optimización de Queries SQL

## ❌ Anti-patrón: Queries Individuales en Loops

```python
# MAL: N+1 queries problem
tier_stats = {}
for tier in ["A", "B", "C", "D"]:
    tier_stats[tier] = await self.count(tier=tier)  # 4 queries!
```

**Problemas:**
- N queries por N valores
- Alta latencia (round-trips a la DB)
- Carga innecesaria en la base de datos

## ✅ Patrón Correcto: GROUP BY

```python
# BIEN: 1 query para todos los valores
result = await self.session.execute(
    select(Model.tier, func.count(Model.id))
    .group_by(Model.tier)
)

tier_stats = {tier: 0 for tier in ["A", "B", "C", "D"]}
for tier, count in result:
    if tier in tier_stats:
        tier_stats[tier] = count
```

## Reglas

1. **Nunca hagas queries en un loop** - Usa `GROUP BY`
2. **Combina agregados relacionados** en una sola query:
   ```python
   select(
       func.count(Model.id),
       func.avg(Model.score),
       func.max(Model.score),
   )
   ```
3. **Inicializa diccionarios con valores default** antes de iterar resultados
4. **Usa `.filter()` dentro de agregados** cuando sea posible:
   ```python
   func.avg(Model.score).filter(Model.score.is_not(None))
   ```

## Ejemplo Completo

```python
async def get_stats(self) -> dict:
    # 1 query: totales + promedios
    agg = await self.session.execute(
        select(
            func.count(Model.id),
            func.avg(Model.score),
        )
    )
    row = agg.one()
    total, avg_score = row[0], row[1] or 0

    # 1 query: count por status (en lugar de N queries)
    status_result = await self.session.execute(
        select(Model.status, func.count(Model.id))
        .group_by(Model.status)
    )
    status_stats = {s: 0 for s in ["new", "processing", "done"]}
    for status, count in status_result:
        status_stats[status] = count

    return {"total": total, "avg": avg_score, "by_status": status_stats}
```

## Cuándo Aplicar

- Endpoints de estadísticas (`/stats`, `/analytics`)
- Dashboards que muestran conteos por categoría
- Cualquier lugar donde veas un `for` con queries adentro
