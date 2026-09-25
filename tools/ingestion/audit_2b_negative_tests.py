# -*- coding: utf-8 -*-
"""Negative tests for audit_2b.py: each one breaks one fact in a package and
proves the audit reports the matching kind. Files are restored afterwards.

A check that never fires is worse than no check (the cost and experience checks
of this audit were dead for weeks: they matched a lowercase name against
capitalized text). This battery pins every dimension - prices, hero costs,
experience, gold, skill tables, rule anchoring, spells, hireling access,
delegated figures, the geometry-read costs of the two-column supplements - by
breaking one fact at a time, and it also proves the three new reading paths are
load bearing: with the display-face reader, the page geometry or the recorded
read-off-the-image figures removed, the costs they read stop being verifiable.
"""
import importlib.util
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BANDS = ROOT / "sources/2B/bands/mordheim"
MAGIC = ROOT / "sources/2B/catalog/magic-2b.yaml"

# El lector compartido es permanente y vive en ``tools/knowledge``; la herramienta
# cotejada (``audit_2b.py``) es de esta fase y un módulo cargado por ruta no tiene
# su directorio en ``sys.path``.
for _tools in (ROOT / "tools" / "knowledge", ROOT / "tools" / "ingestion"):
    if str(_tools) not in sys.path:
        sys.path.insert(0, str(_tools))

import printed_entries

spec = importlib.util.spec_from_file_location(
    "audit_2b", ROOT / "tools/ingestion/audit_2b.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

CASES: list[tuple] = []


def case(title: str, band: str | None, expected: str):
    def wrap(fn):
        CASES.append((title, band, expected, fn))
        return fn
    return wrap


@case("price mismatch (equipment list)", "night-goblins-kaz", "equipment-price-mismatch")
def _price():
    """A plain row: the dagger is priced 2 gc with no formula of its own."""
    path = BANDS / "night-goblins-kaz/equipment-access.yaml"
    text = path.read_text(encoding="utf-8")
    m = re.search(r"(- item_id: dagger\n    cost: )(\d+)", text)
    assert m, "no priced dagger row"
    return (path, text, text[:m.start(2)] + str(int(m.group(2)) + 7) + text[m.end(2):],
            f"dagger cost {m.group(2)} -> {int(m.group(2)) + 7}")


@case("hero cost mismatch (name beside the figure)", "bretonnian-brigands-mou", "cost-mismatch")
def _cost():
    path = BANDS / "bretonnian-brigands-mou/profiles.yaml"
    text = path.read_text(encoding="utf-8")
    m = re.search(r"(- id: scarface\n(?:  .*\n)*?  cost: )(\d+)", text)
    assert m, "no hero cost"
    return (path, text, text[:m.start(2)] + str(int(m.group(2)) + 9) + text[m.end(2):],
            f"Scarface cost {m.group(2)} -> {int(m.group(2)) + 9}")


@case("hero cost mismatch (figure on its own line, two columns)",
       "lords-of-the-marsh-mim", "cost-mismatch")
def _mim_cost():
    """The MIM supplements print the figure between the heading and the profile.

    Nothing on that line names the fighter, so only the page's own geometry
    pairs the two (and keeps them apart from the neighbouring column).
    """
    path = BANDS / "lords-of-the-marsh-mim/profiles.yaml"
    text = path.read_text(encoding="utf-8")
    m = re.search(r"(- id: daemon-fimm\n(?:  .*\n)*?  cost: )(\d+)", text)
    assert m, "no Daemon-Fimm cost"
    return (path, text, text[:m.start(2)] + str(int(m.group(2)) + 11) + text[m.end(2):],
            f"Daemon-Fimm cost {m.group(2)} -> {int(m.group(2)) + 11}")


@case("hero cost mismatch (scanned page, read off the image)",
       "crooked-moon-kep", "cost-mismatch")
def _kep_cost():
    """The scan has no text layer: the figure is pinned by the recorded reading."""
    path = BANDS / "crooked-moon-kep/profiles.yaml"
    text = path.read_text(encoding="utf-8")
    m = re.search(r"(- id: squig-hopper\n(?:  .*\n)*?  cost: )(\d+)", text)
    assert m, "no Squig Hopper cost"
    return (path, text, text[:m.start(2)] + str(int(m.group(2)) + 8) + text[m.end(2):],
            f"Squig Hopper cost {m.group(2)} -> {int(m.group(2)) + 8}")


@case("hero experience mismatch", "bretonnian-brigands-mou", "experience-mismatch")
def _exp():
    path = BANDS / "bretonnian-brigands-mou/profiles.yaml"
    text = path.read_text(encoding="utf-8")
    m = re.search(r"(- id: scarface\n(?:  .*\n)*?  experience: )(\d+)", text)
    assert m, "no hero experience"
    return (path, text, text[:m.start(2)] + str(int(m.group(2)) + 3) + text[m.end(2):],
            f"Scarface experience {m.group(2)} -> {int(m.group(2)) + 3}")


@case("starting gold mismatch", "bretonnian-brigands-mou", "starting-gold-mismatch")
def _gold():
    path = BANDS / "bretonnian-brigands-mou/band.yaml"
    text = path.read_text(encoding="utf-8")
    m = re.search(r"(starting_gold: )(\d+)", text)
    assert m, "no starting gold"
    return (path, text, text[:m.start(2)] + str(int(m.group(2)) + 50) + text[m.end(2):],
            f"starting gold {m.group(2)} -> {int(m.group(2)) + 50}")


@case("skill mark mismatch (printed table)", "bretonnian-brigands-mou", "skill-table-mismatch")
def _skill():
    path = BANDS / "bretonnian-brigands-mou/profiles.yaml"
    text = path.read_text(encoding="utf-8")
    idx = text.index("- id: green-jack\n")
    m = re.search(r"(  skill_access:\n)", text[idx:])
    assert m, "no skill_access for Green Jack"
    at = idx + m.end(1)
    return (path, text, text[:at] + "  - strength\n" + text[at:],
            "Green Jack skill_access += strength")


@case("rule name absent from source", "savage-orcs-kaz", "rule-name-absent")
def _rule():
    """Renamed to a string the document never prints.

    The audit anchors a rule by the printed words of its name or of the section
    it cites, allowing a four-letter prefix so inflections still match ("Sea
    Elf" / "Sea Elves"); a plausible-looking word would anchor on an unrelated
    prefix ("Nonexistent" on the ordinary word "none"), so the invented name
    shares no prefix with anything.
    """
    path = BANDS / "savage-orcs-kaz/special-rules.yaml"
    text = path.read_text(encoding="utf-8")
    mutated = text.replace("  name: Hired Swords\n", "  name: Zqwx Kettle Hymn\n", 1)
    mutated = mutated.replace("    section: Hired Swords\n",
                              "    section: Zqwx Kettle Hymn\n", 1)
    assert mutated != text
    return path, text, mutated, "rule name+section -> a string the source never prints"


@case("hireling named in source, not in package", "savage-orcs-kaz", "hireling-name-absent")
def _hname():
    path = BANDS / "savage-orcs-kaz/special-rules.yaml"
    text = path.read_text(encoding="utf-8")
    # The effect is a folded scalar, so the printed sentence wraps across lines.
    mutated, count = re.subn(r"Black Orc\s+Bodyguard and Snerik\.",
                             "Hired Swords and Dramatis Personae: none.", text, count=1)
    assert count == 1, "hireling names not found in the effect"
    return path, text, mutated, "package prose stops naming Black Orc / Snerik"


@case("hireling access rule missing", "night-goblins-kaz", "hireling-access-missing")
def _haccess():
    """Strip the hireling wording out of the rule that grants the access.

    The effect is a folded scalar, so the mutator rewrites the rule's whole
    effect block (located by its id) instead of replacing a parsed string.
    """
    path = BANDS / "night-goblins-kaz/special-rules.yaml"
    text = path.read_text(encoding="utf-8")
    doc = audit.yaml.safe_load(text)
    target = next((r for r in doc["rules"]
                   if re.search(r"hire|dramatis", r.get("effect") or "", re.I)), None)
    assert target, "no hireling rule"
    at = text.index(f"- id: {target['id']}\n")
    m = re.search(r"  effect:.*?(?=\n  [a-z_]+:|\n- |\Z)", text[at:], re.S)
    assert m, "no effect block"
    body = text[at + m.start():at + m.end()]
    assert body.count("\n") > 1, "effect block is not folded"
    guard = "    None of the warband's fighters may be joined."
    mutated = text[:at + m.start()] + "  effect: >-\n" + guard + text[at + m.end():]
    return path, text, mutated, f"effect of {target['id']} loses hireling wording"


@case("delegated figure disagrees with the KB", "savage-orcs-sar", "cost-mismatch")
def _delegated():
    path = BANDS / "savage-orcs-sar/profiles.yaml"
    text = path.read_text(encoding="utf-8")
    m = re.search(r"(- id: orc-boss\n(?:  .*\n)*?  cost: )(\d+)", text)
    assert m, "no Orc Boss cost"
    return (path, text, text[:m.start(2)] + str(int(m.group(2)) + 5) + text[m.end(2):],
            f"delegated Orc Boss cost {m.group(2)} -> {int(m.group(2)) + 5}")


def spell_list_end(text: str, start: int) -> int:
    """Dónde termina el conjuro que empieza en ``start``: el punto de inserción.

    La línea que cierra el ítem es la que abre otro conjuro de la misma lista
    (``  - id:``), una clave del lore a dos espacios o el documento siguiente a
    columna cero. Guiarse por la primera línea sin sangría acierta sólo mientras
    el lore no imprima nada más después de sus conjuros, y los lore llevan sus
    ``source_refs`` al final: la lista de conjuros se cierra antes.
    """
    lines = text[start:].split("\n")
    offset = start + len(lines[0]) + 1
    for line in lines[1:]:
        if line.startswith("  - ") or re.match(r"^  [a-z_]+:", line) or line.startswith("- "):
            return offset
        offset += len(line) + 1
    return len(text)


@case("spell absent from source", None, "spell-absent-from-source")
def _spell():
    text = MAGIC.read_text(encoding="utf-8")
    anchor = "  - id: spell.songs-of-sorrow.hymn-of-rebirth\n"
    assert anchor in text, "anchor spell not found"
    end = text.index(anchor)
    at = spell_list_end(text, end)
    block = ("  - id: spell.songs-of-sorrow.invented-by-test\n"
             "    roll: 6\n"
             "    name: Invented By Test\n"
             "    name_i18n:\n"
             "      es: Inventado Por Test\n"
             "    difficulty: 9\n"
             "    effect: >-\n"
             "      Written only by the negative test.\n")
    return (MAGIC, text, text[:at] + block + text[at:],
            "fabricated spell appended to lore.songs-of-sorrow")


def run_audit(band: str | None = None) -> dict:
    cmd = [sys.executable, "-X", "utf8", str(ROOT / "tools/ingestion/audit_2b.py")]
    if band:
        cmd.append(band)
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, encoding="utf-8")
    assert out.stdout.strip(), out.stderr[-400:]
    return json.loads(out.stdout)


def machinery_cases() -> list[tuple]:
    """The two new reading paths, proved load bearing by removing each."""

    def without_display_face() -> list[str]:
        original = audit.display_font_text
        audit.display_font_text = lambda text: None          # noqa: ARG005
        try:
            rows = audit.package_rows()
            return [i["kind"] for i in audit.check_band(
                "metal-mongers-mim", rows["metal-mongers-mim"])]
        finally:
            audit.display_font_text = original

    def without_page_geometry() -> list[str]:
        """Quita la capa de geometría del lector: las páginas se leen planas.

        Es la lectura anterior a este cambio (``pdftotext`` por página, sin
        posiciones): sin palabras con su posición no hay línea física ni celda, la
        cifra suelta de «40 gold crowns» queda sin el nombre que la encabeza y el
        coste de la promoción deja de ser verificable.
        """
        original = printed_entries.PdfCorpus.word_lines
        printed_entries.PdfCorpus.word_lines = lambda self, stem, page: []   # noqa: ARG005
        audit.CORPUS._lines.clear()
        audit.EXTRA_CORPUS._lines.clear()
        audit._BARE_COST_CACHE.clear()
        try:
            rows = audit.package_rows()
            return [i["kind"] for i in audit.check_band(
                "lords-of-the-marsh-mim", rows["lords-of-the-marsh-mim"])]
        finally:
            printed_entries.PdfCorpus.word_lines = original
            audit.CORPUS._lines.clear()
            audit.EXTRA_CORPUS._lines.clear()
            audit._BARE_COST_CACHE.clear()

    def without_recorded_readings() -> list[str]:
        original = dict(audit.READ_OFF_PAGE)
        audit.READ_OFF_PAGE.clear()
        try:
            rows = audit.package_rows()
            return [i["kind"] for i in audit.check_band(
                "crooked-moon-kep", rows["crooked-moon-kep"])]
        finally:
            audit.READ_OFF_PAGE.update(original)

    return [
        ("display-face headings decoded (Engineer Adept)", without_display_face,
         "cost-unverifiable"),
        ("page geometry reads the bare cost lines (Fimir Nobles)", without_page_geometry,
         "cost-unverifiable"),
        ("scanned page readings recorded (Crooked Moon)", without_recorded_readings,
         "cost-unverifiable"),
    ]


def write_with_retry(path: Path, text: str) -> None:
    """Write LF-only text, retrying while the path is transiently locked.

    ``audit_2b.py`` runs as a child process and reads every package, so Windows
    can still refuse a reopen of just-touched files with ``OSError: Invalid
    argument``. Retry briefly instead of corrupting a package (a mutation that
    is never restored is worse than a slow battery).
    """
    for attempt in range(6):
        try:
            path.write_text(text, encoding="utf-8", newline="\n")
            return
        except OSError:
            time.sleep(0.25 * (attempt + 1))
    path.write_text(text, encoding="utf-8", newline="\n")


def restore(path: Path, snapshot: bytes) -> None:
    """Put the file back byte-exactly (never through a text round-trip)."""
    for attempt in range(6):
        try:
            path.write_bytes(snapshot)
            return
        except OSError:
            time.sleep(0.25 * (attempt + 1))
    write_with_retry(path, snapshot.decode("utf-8"))


def main() -> int:
    failures = 0
    for title, band, expected, fn in CASES:
        path, _original, mutated, detail = fn()
        # Snapshot the bytes: the mutated write must be restored byte-exactly,
        # never through a text round-trip that would rewrite the line endings
        # (write_text without newline="\n" emits CRLF on Windows).
        snapshot = path.read_bytes()
        try:
            write_with_retry(path, mutated)
            report = run_audit(band)
            kinds = {i["kind"] for i in report["problems"]}
            ok = expected in kinds
            print(f"[{'ok  ' if ok else 'FAIL'}] {title:<52} {detail}")
            if not ok:
                print(f"          expected {expected!r}, open kinds: {sorted(kinds)}")
                failures += 1
        finally:
            try:
                restore(path, snapshot)
            except OSError as error:
                failures += 1
                print(f"[FAIL] could not restore {path}: {error}")
    for title, fn, expected in machinery_cases():
        kinds = fn()
        ok = expected in kinds
        print(f"[{'ok  ' if ok else 'FAIL'}] {title:<52} "
              f"removing the pass yields {expected}")
        if not ok:
            print(f"          expected {expected!r}, got {sorted(set(kinds))}")
            failures += 1
    print("failures:", failures)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
