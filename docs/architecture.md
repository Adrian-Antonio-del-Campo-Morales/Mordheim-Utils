# Arquitectura

## Paquetes del monorepo y dependencias permitidas

```text
mordheim_core
  ↑
mordheim_knowledge → mordheim_construction → mordheim_combat
                  ↑          ↑
                  └ mordheim_combat_lab.application ← mordheim_combat_lab.persistence
                         ↑
                         mordheim_combat_lab.ui
                         mordheim_campaign (reutiliza mordheim_ui)

mordheim_combat_lab.verification → mordheim_knowledge + mordheim_construction
                                   + mordheim_combat + tests/specs
```

`mordheim_core` no conoce YAML, UI ni verificadores. `mordheim_combat` recibe
`CompiledFighter` y no carga la KB. `mordheim_combat_lab.application` ejecuta
casos de uso sin Tkinter. Las dos aplicaciones presentan resultados con la capa
compartida `mordheim_ui` y coordinan sus propios hilos. `verification` está
fuera del runtime y utiliza el motor real como sistema bajo prueba.

`mordheim_campaign` es *interface-first*: depende de view-models demo y de la
capa UI compartida; su conexión real con `mordheim_knowledge` y
`mordheim_construction` (KnowledgePort, legalidad, persistencia de campaña) es
la siguiente fase prevista.

## Recursos compartidos

La KB vive una sola vez en `sources/knowledge/`. La resolución de rutas
pertenece a `mordheim_knowledge.paths` (`knowledge_root()`), con override por
variable de entorno (`MORDHEIM_COMBAT_LAB_KNOWLEDGE_PATH`) y soporte de EXE
congelado para ambas aplicaciones. El corpus de verificación vive en
`tests/specs/` (`specifications_root()`), es material de test y no se distribuye.

## Recorrido de una regla

1. La regla editorial y su binding están en `sources/knowledge/`.
2. `mordheim_knowledge` valida y carga documentos por IDs estables.
3. `mordheim_construction` valida accesos y compila el binding en `CompiledFighter`.
4. El motor consume el efecto en una fase o handler con estado.
5. Un escenario de `tests/specs/` comprueba concesión, compilación y resultado observable.

El motor modular divide estado, preparación de contextos, ataques, pools, efectos
posteriores, rondas y duelo. El vectorizado es el runtime de análisis de la UI,
pero no el oráculo de corrección del modular.

La legalidad pertenece a `mordheim_construction`; la composición a
`mordheim_core.effects`; las fases a `mordheim_combat.phases`; workbooks y
preferencias a `mordheim_combat_lab.persistence`. Los tests de
`tests/architecture/` hacen ejecutables estos límites.
