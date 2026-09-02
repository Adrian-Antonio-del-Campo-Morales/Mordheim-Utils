# Especificaciones de verificación

Este directorio no es parte de la KB ni del runtime distribuido.

- `structural/phase-verification.yaml`: correspondencia entre efectos, fases y consumidores.
- `semantic/rules/`: comportamiento de mecanismos y reglas básicas.
- `semantic/grants/`: concesiones editoriales y destinatarios.
- `semantic/interactions/`: composiciones entre reglas.
- `interactions.yaml`: combinaciones de orden superior requeridas.
- `interaction-policy.yaml`: política de riesgo, exigencia y overrides revisados para interacciones.

Cada especificación semántica fija fuente, interpretación, categoría, estado inicial, dados, decisiones, expectativas y mutaciones. El motor modular es el sistema bajo prueba; nunca se usa su salida para generar el valor esperado.

Las fuentes de dados y decisiones son estrictas: una petición inesperada o sin consumir falla. Las probabilidades se expresan con fracciones exactas. Las mutaciones se aplican temporalmente en memoria y se restauran.

```powershell
python -m mordheim_combat_lab verify --inventory
python -m pytest tests/verification/test_semantics.py -q
python -m mordheim_combat_lab verify --json
python -m mordheim_combat_lab verify --require-complete
```

El último comando falla mientras quede cualquier obligación o interacción pendiente. Consulte [la guía completa](../docs/tasks/verify-rules.md).
