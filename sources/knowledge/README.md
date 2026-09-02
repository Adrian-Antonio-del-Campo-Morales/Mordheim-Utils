# Base de conocimiento

Única fuente de reglas y datos del runtime: catálogos compartidos, bandas, perfiles, accesos y registro. Sus reglas editoriales conservan identidad propia y enlazan mediante bindings con mecanismos ejecutables estables.

El bloque `runtime` se valida contra `registry/runtime-schema.yaml`. `scope` indica si el efecto pertenece al duelo; `implemented` si tiene implementación; `grant` cómo se concede. Una ausencia de clasificación no significa fuera de alcance.

La KB no contiene evidencia de corrección. El contrato estructural y los escenarios semánticos viven en `tests/specs/`, para que el runtime no dependa de sus propias pruebas. Consulte [Modificar la KB](../../docs/tasks/modify-kb.md) y [Verificar reglas](../../docs/tasks/verify-rules.md).

```powershell
python -m mordheim_combat_lab validate
python -m mordheim_combat_lab verify
```
