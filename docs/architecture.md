# Arquitectura

## Dependencias permitidas

```text
domain
  ↑
knowledge → construction → combat
                  ↑          ↑
                  └ application ← persistence
                         ↑
                         ui

verification → knowledge + construction + combat + specs
```

`domain` no conoce YAML, UI ni verificadores. `combat` recibe `CompiledFighter` y no carga la KB. `application` ejecuta casos de uso sin Tkinter. `ui` presenta resultados y coordina hilos. `verification` está fuera del runtime y utiliza el motor real como sistema bajo prueba.

## Recorrido de una regla

1. La regla editorial y su binding están en `sources/knowledge/`.
2. `knowledge` valida y carga documentos por IDs estables.
3. `construction` valida accesos y compila el binding en `CompiledFighter`.
4. El motor consume el efecto en una fase o handler con estado.
5. Un escenario de `specs/` comprueba concesión, compilación y resultado observable.

El motor modular divide estado, preparación de contextos, ataques, pools, efectos posteriores, rondas y duelo. El vectorizado es el runtime de análisis de la UI, pero no el oráculo de corrección del modular.

La legalidad pertenece a `construction`; la composición a `domain.effects`; las fases a `combat.phases`; workbooks y preferencias a `persistence`. Los tests de `tests/architecture/` hacen ejecutables estos límites.
