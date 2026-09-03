# Mordheim Utils

Monorepo con las utilidades de Mordheim: un **motor de duelos dirigido por base de
conocimiento** y un **gestor de campaña**, sobre paquetes compartidos y una única KB
canónica. Las dos aplicaciones se distribuyen por separado y comparten dominio,
carga de reglas, construcción legal y capa de interfaz.

## Aplicaciones

| App | Paquete | Entry point | Descripción |
| --- | --- | --- | --- |
| Combat Lab | `mordheim_combat_lab` | `mordheim-combat-lab` | Simulador de duelos 1 contra 1 con motor modular (oráculo) y motor vectorizado (análisis), verificación semántica, paridad y benchmark. |
| Campaign Manager | `mordheim_campaign` | `mordheim-campaign-manager` | Prototipo GUI *campaign-timeline-first*: estados inmutables de banda, batallas y secuencia post-batalla. Bandas, perfiles y equipo provienen de la KB canónica vía `KnowledgePort`; las campañas se guardan/cargan como ficheros `.mordheim`. |

## Paquetes compartidos

```text
mordheim_core          tipos puros, dados inyectables, composición de efectos
mordheim_knowledge     carga y validación de la KB (sources/knowledge), rutas de recursos
mordheim_construction  compilación de perfiles y legalidad de equipo/elecciones
mordheim_combat        fases, motor modular (oráculo), motor vectorizado, kernel, backend nativo
mordheim_ui            tema Tkinter compartido y widgets genéricos
```

La base de conocimiento vive una sola vez en `sources/knowledge/` (371 YAMLs:
bandas, catálogos, mecánicas y registro). El corpus de verificación —contrato
estructural y escenarios semánticos— es material de test y vive en `tests/specs/`.

## Empezar

Requiere Python 3.10 o posterior.

```powershell
python -m pip install -e ".[dev]"
```

### Combat Lab

```powershell
python -m mordheim_combat_lab
python -m mordheim_combat_lab validate
python -m mordheim_combat_lab verify
python -m mordheim_combat_lab parity --require-complete
python -m mordheim_combat_lab test-report
python -m mordheim_combat_lab audit
python -m mordheim_combat_lab benchmark -n 100000
python -m pytest -q
```

`validate` comprueba estructura y conexiones (incluido el contrato de
`tests/tests/specs/structural/phase-verification.yaml`). `verify` ejecuta evidencia
semántica independiente; `verify --require-complete` es la puerta estricta.
`audit` genera el CSV de estado por regla en `outputs/audit/`. El informe
ejecutable, no una cifra copiada aquí, es la fuente del estado actual.

`parity` certifica el motor vectorizado contra el modular. `benchmark` mide
motores con líneas base y puertas de mejora/regresión. `test-report` escribe
los CSV humanos de paridad y tests técnicos en `outputs/test-report/`.

### Campaign Manager

```powershell
mordheim-campaign-manager
python -m mordheim_campaign
```

El prototipo es *interface-first*: los widgets consumen view-models a través de
`AppController`, que a su vez obtiene bandas, perfiles, límites y ofertas de
equipo de la KB canónica mediante `KnowledgePort` (`mordheim_knowledge`). Las
campañas gestionadas se guardan y cargan como ficheros JSON `.mordheim` (y se
exportan como resumen Markdown) desde `mordheim_campaign/persistence`. Véase
[la guía del manager](docs/campaign-manager.md) y
[su dirección de arquitectura](docs/campaign-architecture.md).

## Mapa del repositorio

```text
sources/knowledge/        KB única canónica consumida por el runtime
src/
  mordheim_core/          dominio compartido (sin YAML, sin UI, sin motores)
  mordheim_knowledge/     loaders + validadores + rutas de la KB
  mordheim_construction/  CompiledFighter y legalidad
  mordheim_combat/        fases y motores (modular y vectorizado)
  mordheim_ui/            tema y widgets Tk compartidos
  mordheim_combat_lab/    app 1: cli, ui, application, persistence, verification
  mordheim_campaign/      app 2: shell, views, moments, dialogs
tests/
  specs/                  contrato estructural + escenarios semánticos (corpus de verificación)
  architecture/           límites entre paquetes, ejecutables
docs/                     arquitectura y guías de tareas
tools/windows/            builds PyInstaller (dos EXE independientes)
archive/                  código histórico no mantenido ni empaquetado
```

Consulte [la arquitectura](docs/architecture.md) y [las guías de tareas](docs/README.md).

## Distribución en Windows

```powershell
tools\windows\build_MordheimCombatLab_ONEFILE.bat
tools\windows\build_MordheimCampaignManager.bat
```

Cada build genera un EXE independiente que incluye la aplicación y la KB
compartida (`sources/knowledge/`), y ninguno incluye `tests/` ni `archive/`.
