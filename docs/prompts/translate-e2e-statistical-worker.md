# Prompt para un agente externo

Traduce UN caso E2E a escenario precompilado de paridad estadística.

Repositorio: D:\DEVEL\Mordheim\Mordheim-Utils
Rama: precompile-all
Caso asignado: <audit_id::id>

No accedas ni modifiques D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK.
Comprueba carpeta, rama y estado de Git; conserva cambios ajenos.

Lee AGENTS.md, docs/e2e-statistical-parity.md y
docs/e2e-statistical-delivery-contract.md. Sigue exactamente ese contrato y
consulta docs/examples/e2e-statistical-parity.json como ejemplo de formato.
Si falta la asignación, el contrato o el ejemplo, pide al coordinador lo que
falta; no elijas otro caso ni inventes un formato.

Localiza el E2E actual por audit_id e id. Prepara su entrega individual con las
entradas completas, origen verificable y huellas válidas, reutilizando los
formatos y el exportador existentes. Las tiradas y expectativas exactas no se
usan para paridad estadística. Si no puedes conservar alguna entrada o definir
la política según el contrato, entrega el bloqueo concreto; no lo ocultes.

Escribe únicamente el JSON individual asignado por el contrato. No modifiques
YAML, catálogo consolidado, motores, ejecutores ni archivos de otros agentes.
Realiza las comprobaciones mínimas del contrato. No ejecutes campañas, no hagas
commit ni push y no afirmes compatibilidad o paridad sin evidencia.

Devuelve el identificador, ruta del archivo, estado y comprobaciones realizadas.

## Mapa para trabajar sin contexto adicional

| Necesidad | Referencia |
|---|---|
| Declaración actual | `tests/integration/e2e/cases/**/*.yaml`, por `audit_id` e `id`. |
| Vocabulario y valores predeterminados | `tests/integration/e2e/corpus.py` y `tests/integration/e2e/execution/runner.py`: `_build`, `_duel_context`, `_apply_state`, `execute_case`. |
| Entradas existentes | `tests/engines/fixtures/compiled-cases.json`, clave `e2e/<audit_id>/<id>`. Las rutas históricas de origen pueden estar obsoletas. |
| Preparación | `tools/knowledge/export_compiled_cases.py`: función pública `export_cases`. |
| Codec y huellas | `tools/verification/compiled_cases.py`: `load_cases`, `encode_case`, `decode_case`, `CaseLimits`. |
| Conocimiento actual | `sources/knowledge/`. |

No cambies de rama si la comprobación inicial no coincide: informa al
coordinador. No necesitas otros chats. La asignación explícita evita que varios
agentes traduzcan el mismo caso; no hay reserva automática.

## Procedimiento y clasificación

1. Localiza exactamente una declaración con el identificador asignado. Lee solo
   ese caso y los auxiliares necesarios, no todo el conocimiento del repositorio.
2. Rechazo de construcción demostrado: `not-applicable`. Rechazo en ejecución,
   decisiones explícitas o entradas no representables: `blocked`, con motivo
   concreto. No investigues ni repares motores para completar la traducción.
3. Conserva todas las entradas y sus valores predeterminados reales. Las
   instrucciones de decisiones explícitas no pueden desaparecer bajo la
   etiqueta `engine-default`. No simplifiques estados, contexto o combatientes.
4. Reutiliza una entrada congelada solo si demuestras correspondencia con las
   entradas y construcción actuales. Una clave coincidente no es suficiente.
   Si demostrarlo cuesta más, compila únicamente el caso durante la preparación.
5. No escribas en el catálogo ni en su manifest. Se permiten temporales privados,
   eliminados al terminar, además del único JSON individual autorizado.

## Receta para un caso traducible

Desde la raíz del repositorio, en PowerShell, sustituye únicamente `TEST_ID`.
Compila desde el YAML actual sin ejecutar combate. No instala dependencias.
Si falla, interpreta el error y entrega un bloqueo; no borres campos hasta que
funcione. El exportador se encarga de construir combatientes y contexto.

```powershell
@'
from pathlib import Path
from dataclasses import replace
import hashlib, json, subprocess, sys, tempfile
import yaml

TEST_ID = "<audit_id::id>"
root = Path.cwd()
for rel in ("packages/python/core", "packages/python/combat-engine",
            "packages/python/knowledge", "packages/python/roster-construction"):
    sys.path.insert(0, str(root / rel))
from tools.knowledge.export_compiled_cases import export_cases
from tools.verification.compiled_cases import CaseLimits, load_cases, encode_case, decode_case

audit_id, scenario_id = TEST_ID.split("::", 1)
loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
found = []
for path in (root / "tests/integration/e2e/cases").rglob("*.yaml"):
    for row in yaml.load(path.read_text(encoding="utf-8"), Loader=loader) or []:
        if row.get("audit_id") == audit_id and row.get("id") == scenario_id:
            found.append((path, row))
assert len(found) == 1, f"Expected one E2E, found {len(found)}"
path, row = found[0]
assert "expect_error" not in row, "Expected refusal requires classification"
assert not row.get("decisions"), "Explicit decisions require a policy: blocked"
assert set(row.get("fighters", {})) == {"first", "second"}, "Missing fighters: review defaults; do not invent"
key = f"e2e/{audit_id}/{scenario_id}"
revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
source = {"revision": revision, "path": path.relative_to(root).as_posix(),
          "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "test_id": TEST_ID}
spec = {k: v for k, v in row.items()
        if k not in {"id", "audit_id", "covers", "rolls", "decisions"}
        and not k.startswith("expect_")}
spec.update(case_key=key, origin={"kind": "e2e", "node_id": TEST_ID,
                                 "path": source["path"], "sha256": source["sha256"]})
with tempfile.TemporaryDirectory(prefix="e2e-statistical-") as scratch:
    frozen = Path(scratch) / "case.json"
    export_cases({"cases": [spec], "revision": revision},
                 kb_root=root / "sources/knowledge", destination=frozen)
    case = load_cases(frozen)[key]
case = replace(case, limits=CaseLimits(maximum_rounds=case.limits.maximum_rounds))
encoded = encode_case(case)
assert encode_case(decode_case(encoded)) == encoded
assert encoded["limits"] == {"maximum_rounds": row.get("maximum_rounds", 1)}
assert encoded["determinism"] == {"dice": [], "decisions": []}
assert encoded["expectations"] is None and encoded["benchmark"] is None
delivery = {"schema": "mordheim-e2e-statistical-delivery/v1", "status": "translated",
            "source": source, "case_key": key, "case": encoded,
            "decision_policy": {"kind": "engine-default"}, "magnitudes": ["winner"],
            "reason": None}
target = root / "tests/engines/fixtures/e2e-statistical-deliveries" / (hashlib.sha256(key.encode("utf-8")).hexdigest() + ".json")
target.parent.mkdir(parents=True, exist_ok=True)
with target.open("x", encoding="utf-8") as stream:
    json.dump(delivery, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
assert json.loads(target.read_text(encoding="utf-8")) == delivery
print(target)
print("JSON, identity, source hash, codec round-trip and statistical fields checked")
'@ | python -
```

El modo `x` impide sobrescribir otra entrega. Si existe, revísala sin modificarla
y comunica duplicidad o desactualización. Si falta una dependencia, informa de
cuál; no cambies el entorno compartido ni instales paquetes por tu cuenta.

La receta no demuestra por sí sola equivalencia de valores predeterminados:
contrasta el resultado con el runner, especialmente contexto y estado inicial.
Si exportador y runner difieren, entrega `blocked` con el campo concreto.

## Cómo entregar un bloqueo

Usa los mismos campos superiores del ejemplo, con `case = null`,
`decision_policy = null`, estado y motivo apropiados. Mantén origen y huella
actuales. Por ejemplo, describe la clave REAL de una decisión prescrita y qué
política para trayectorias aleatorias falta. No copies decisiones del ejemplo.

Un fallo inesperado del exportador es un bloqueo, no prueba de no aplicabilidad.
Si no localizas el origen, informa sin inventar ruta, huella o entrega. Si solo
falta un dato del contrato, pregunta por ese dato y continúa las comprobaciones
independientes. No pidas confirmación para pasos ya autorizados aquí.

## Comprobación y cierre

- Comprueba campos del contrato, identidad, huella del YAML y nombre SHA-256.
- Para `translated`, comprueba conservación de entradas además del round-trip.
  Para los otros estados, comprueba campos nulos y motivo verificable.
- No ejecutes campañas, no crees tests ni cambies dependencias. No hagas commit
  ni push. La admisión por motor y la integración son del coordinador.
- Responde: identificador, archivo, estado, comprobaciones y bloqueo si hay.
  `translated` no significa compatibilidad de motores ni paridad aprobada.
