"""Guards for the permanent hireling source cotejo (``tools/knowledge/check_hireling_sources``).

El cotejo compara cada entrada impresa de una página o de un PDF con el perfil de su
catálogo y con su entrada de contratación. Vale la pena por tres cosas, y este módulo
fija las tres:

1. **La entrada impresa se lee como la imprime el documento**: en una página, un bloque
   por personaje (``div.fighter``) y las celdas de su tabla; en un PDF, por geometría, con
   la columna izquierda antes que la derecha. La tarifa, la fila y el rating del vecino
   nunca cuentan para la entrada cotejada —la lectura plana daba a ``“Busty” Gwen`` los
   75/30 del Dark Jester y al Foole los 70/35 de Sigmund, y la columna vecina de un PDF
   daba al Fire-Eater el +30 de la hermana—;
2. **el paquete que se separa de la fuente tiene que verse**: las mutaciones corren contra
   copias de usar y tirar en ``tmp_path``, así que la KB y el staging sólo se leen;
3. **cada entrada resuelve su documento**: la URL de sus ``source_refs`` resuelve en el
   registro de documentos fuente —el de la KB, no una tabla del tool— y el registro se
   exige completo sobre los catálogos de las dos familias.

Las dos familias que cubre la orden de la KB (``hired-swords`` y ``dramatis-personae``) y
el staging de 2B se cotejan con la misma lectura: es la misma herramienta con otro catálogo
(``--tree kb`` por defecto, ``--tree 2b`` para el staging). Las pruebas de integración leen
las copias del espejo (``build/cache``, no versionadas) y se saltan cuando faltan, igual que
las herramientas que guardan; los fixtures no necesitan nada cacheado.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
# El cotejo y sus dos piezas viven en el utillaje permanente de la KB.
TOOLS = ROOT / "tools" / "knowledge"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

cotejo = pytest.importorskip("check_hireling_sources")
source_documents = pytest.importorskip("source_documents")

#: El catálogo publicado de la KB y el staging que se promociona a él.
KB = cotejo.CATALOGUES["kb"]
STAGING = cotejo.CATALOGUES["2b"]

# El registro declara los documentos; el espejo dice si la copia está descargada y dónde.
DOCUMENTS = cotejo.SOURCE_DOCUMENTS
GRADE_2A_PAGE = DOCUMENTS.by_id("mordheimer.net.dramatis-personae.grade-2a")
SPECIALISTS = DOCUMENTS.by_id("broheim.mutinyinmarienburg.specialists")
KARAK_AZGAL = DOCUMENTS.by_id("broheim.karak-azgal")

KB_CACHED = pytest.mark.skipif(
    cotejo.MIRROR.reader(GRADE_2A_PAGE) is None,
    reason="mordheimer.net page snapshot is not cached (offline checkout)")
STAGING_CACHED = pytest.mark.skipif(
    cotejo.MIRROR.reader(SPECIALISTS) is None or cotejo.MIRROR.reader(KARAK_AZGAL) is None,
    reason="2B source PDFs are not cached (offline checkout)")

GRADE_2A = (
    "Aksho'akhash the Vile Dreadwing, Lord of the Carrion Throne",
    "\u201cBusty\u201d Gwen",
    "The Dark Jester in Mordheim",
    "The Headless Horseman",
    "The Foole",
    "Sigmund Spindle, the Harvester of Flesh",
    "William Sch\u00e4kestange, Master Bard",
)
# La cobertura que el cotejo tiene que declarar: el Horseman imprime tarifa y tabla de
# jinete y montura y el catálogo no lo modela (está adjudicado `out_of_scope`), así que su
# tarifa y su fila no son comparables y se anotan.
COVERAGE = {"block": 7, "fee": 6, "stats": 6, "rating": 7, "rules": 7}

# Los siete hallazgos que la pasada de adjudicación de 2B cerró: seis eran artefactos del
# extractor (el dato del paquete era el impreso) y uno una divisa convertida.
ADJUDICATED = (
    "Bog Hunter", "Midshipman", "Halfling Pimp", "Albino Stormvermin",
    "Norse Bearman Bodyguard", "Fire-Eater", "Priest of Verena",
)


def line(text: str, words: list[tuple[int, int, str]]) -> dict:
    """Una línea física tal y como la devuelve la lectura por geometría."""
    return {"text": text, "top": 0, "left": min((w[0] for w in words), default=0),
            "words": words}


def run_cotejo(tmp_path, monkeypatch, *, catalogue=KB, names=(), campaign=None,
               root=None) -> list[dict]:
    """El informe del cotejo de un catálogo, con su salida fuera del árbol de build."""
    monkeypatch.setattr(catalogue, "out", tmp_path / "catalogue")
    if campaign is not None:
        monkeypatch.setattr(catalogue, "campaign", campaign)
    if root is not None:
        monkeypatch.setattr(catalogue, "root", root)
    assert cotejo.main(["--tree", catalogue.name, *names]) == 0
    return json.loads((catalogue.report).read_text(encoding="utf-8"))


def grade_2a(rows: list[dict]) -> dict[str, dict]:
    return {row["name"]: row for row in rows if row["name"] in GRADE_2A}


# --------------------------------------------------------------------------- #
# De la entrada al documento fuente: el registro, no una tabla del tool
# --------------------------------------------------------------------------- #

def test_the_public_catalogue_has_both_families() -> None:
    """El cotejo permanente cubre las dos familias y todos los grados del catálogo.

    Los dos drivers de la fase de ingesta cubrían una familia cada uno —los Dramatis
    Personae de la KB por un lado y los hirelings de 2B por otro— y los 72 hired
    swords publicados no los cotejaba nadie; la orden de la KB los recorre todos.
    """
    families = {profile["_file"].split("/")[0] for profile in KB.profiles()}
    assert families == {"hired-swords", "dramatis-personae"}
    # Los grados publicados hoy: 30 Dramatis Personae y 72 hired swords.
    assert len(KB.profiles()) >= 102


def test_every_kb_profile_resolves_through_the_registry() -> None:
    """Ningún perfil del catálogo publicado cita un documento que el registro no declare.

    Es la mitad permanente del cotejo: qué documento imprime a cada personaje sale del
    registro de documentos fuente, no de una tabla del tool, y una cita nueva sin
    declarar se ve aquí en vez de degradar a «sin documento que cotejar», que se lee
    como «no hay nada que comparar».
    """
    profiles = KB.profiles()
    for profile in profiles:
        assert DOCUMENTS.undeclared(profile) == [], profile["name"]
        assert DOCUMENTS.resolve(profile), profile["name"]


def test_the_dramatis_personae_print_on_the_four_grade_pages() -> None:
    """El registro declara las cuatro páginas de grado que cita la familia de Dramatis."""
    documents = {resolution.document.id.split(".")[-1]
                 for profile in KB.profiles()
                 if profile["_file"].startswith("dramatis-personae")
                 for resolution in DOCUMENTS.resolve(profile)}
    assert documents == {"grade-1a", "grade-1b", "grade-1c", "grade-2a"}


def test_every_staging_profile_resolves_through_the_registry() -> None:
    """Y ningún perfil del staging de 2B cita un PDF que el registro no declare."""
    profiles = STAGING.profiles()
    assert len(profiles) == 28
    for profile in profiles:
        assert DOCUMENTS.undeclared(profile) == [], profile["name"]
        assert DOCUMENTS.resolve(profile), profile["name"]


def test_a_profile_takes_the_document_from_the_registry() -> None:
    """El Albino Stormvermin sale en el PDF de Specialists, con su copia del espejo."""
    profiles = {profile["name"]: profile for profile in STAGING.profiles()}
    resolved = DOCUMENTS.resolve(profiles["Albino Stormvermin"])
    assert [resolution.document.id for resolution in resolved] == [SPECIALISTS.id]
    assert resolved[0].document.mirror == SPECIALISTS.mirror


def test_the_registry_keeps_the_2b_mirror_names() -> None:
    """Los nombres de la copia local son los del manifest que la descargó.

    El espejo de 2B guarda cada PDF bajo el id de la banda que lo descargó
    (``build/cache/2b-pdfs/<banda>.pdf``) y el registro declara ese mismo nombre;
    probarlo aquí deja la pareja URL→copia atada mientras el árbol exista.
    """
    manifest = yaml.safe_load((ROOT / "sources/2B/manifest.yaml").read_text(encoding="utf-8"))
    bands: dict[str, list[str]] = {}
    for band in manifest["bands"]:
        bands.setdefault(source_documents.normalize_url(band["pdf_url"]), []).append(band["id"])
    checked = 0
    for document in DOCUMENTS:
        for url in document.urls:
            band_ids = bands.get(source_documents.normalize_url(url))
            if not band_ids:
                continue
            checked += 1
            assert Path(document.mirror).name in {f"{band_id}.pdf" for band_id in band_ids}, document.id
    assert checked >= 3


# --------------------------------------------------------------------------- #
# La lectura del lector compartido, sin documento delante
# --------------------------------------------------------------------------- #

def test_flat_undoes_the_dotted_filler() -> None:
    """Relics imprime el punto del formulario entre las palabras de la tarifa."""
    assert cotejo.fees_in("Hire Fee: .85.dinars.to.hire;.+.45.dinars.upkeep.cost .") \
        == [(85, "dinars", 45, "dinars")]


def test_fees_in_reads_both_printed_forms() -> None:
    assert cotejo.fees_in("75 warp tokens to hire +30 warp tokens upkeep") \
        == [(75, "warp tokens", 30, "warp tokens")]
    assert cotejo.fees_in("Hire Fee : 40GC, upkeep: 25GC") \
        == [(40, "gold crowns", 25, "gold crowns")]
    assert cotejo.fees_in("30 gold crowns to hire +15 upkeep") \
        == [(30, "gold crowns", 15, None)]


def test_unit_of_sees_the_unit_glued_to_the_amount() -> None:
    assert cotejo.unit_of("Hire Fee : 40GC") == "gold crowns"
    assert cotejo.unit_of("75 warp tokens") == "warp tokens"


def test_entries_keep_the_neighbour_column_out() -> None:
    """Dos entradas a dos columnas: cada una con su tarifa y su rating."""
    def block(left: int, name: str, fee: str, rating: str) -> list[dict]:
        return [
            line(name, [(left, 10, name.split()[0]), (left + 48, 10, name.split()[-1])]),
            line(fee, [(left + i, 20, token) for i, token in
                       enumerate(fee.split())]),
            line(f"Rating: A {name.title()} increases the warband's",
                 [(left, 30, "Rating:"), (left + 128, 30, "rating")]),
            line(f"rating by {rating} points, plus 1 point for each",
                 [(left, 40, "rating"), (left + 28, 40, rating), (left + 48, 40, "points,")]),
        ]

    found = cotejo.entries(block(72, "Halfling fence", "30 gold crowns to hire +15 gold crowns upkeep", "+15")
                           + block(470, "Halfling pimp", "20 gold crowns to hire +10 gold crowns upkeep", "+10"))
    assert [entry["heading"] for entry in found] == ["Halfling fence", "Halfling pimp"]
    assert cotejo.fees_in(found[1]["text"]) == [(20, "gold crowns", 10, "gold crowns")]
    assert cotejo.ratings_in(found[1]["text"]) == [10]
    assert "30 gold crowns" not in found[1]["text"]


def test_stat_row_is_read_in_table_order() -> None:
    """El Fire-Eater imprime ``4(6)`` y el extractor suelta la fila en dos líneas."""
    entry = {"line_words": [
        [(106, 100, "Profile"), (150, 100, "M"), (170, 100, "WS"), (200, 100, "BS"),
         (230, 100, "S"), (250, 100, "T"), (270, 100, "W"), (290, 100, "I"),
         (310, 100, "A"), (330, 100, "Ld")],
        [(121, 112, "(6)"), (150, 112, "2"), (162, 112, "3"), (174, 112, "3"),
         (186, 112, "4"), (198, 112, "2"), (210, 112, "2"), (222, 112, "1"),
         (234, 112, "7")],
        [(106, 124, "Fire-eater"), (200, 124, "4")],
    ], "text": ""}
    assert cotejo.stat_rows(entry) == ["423342217"]


def test_stat_row_without_the_word_profile() -> None:
    """Los Dramatis de Karak Azgal empiezan la tabla directamente en las columnas."""
    entry = {"line_words": [
        [(135, 700, "M"), (160, 700, "WS"), (185, 700, "BS"), (210, 700, "S"),
         (230, 700, "T"), (250, 700, "WI"), (280, 700, "A"), (300, 700, "LD")],
        [(129, 712, "Aldred"), (200, 712, "4"), (212, 712, "6"), (224, 712, "4"),
         (236, 712, "4"), (248, 712, "4"), (260, 712, "2"), (272, 712, "4"),
         (284, 712, "2"), (296, 712, "8")],
    ], "text": ""}
    assert cotejo.stat_rows(entry) == ["464442428"]


# --------------------------------------------------------------------------- #
# La lectura del documento real
# --------------------------------------------------------------------------- #

@KB_CACHED
def test_the_page_is_read_one_entry_per_printed_block() -> None:
    """Cada personaje con su tarifa y su fila, sin la del vecino de columna."""
    reader = cotejo.MIRROR.reader(GRADE_2A_PAGE)
    assert reader.kind == "html"
    entries = {entry["heading"]: entry for entry in reader.corpus.entries()}
    assert "\u201cBusty\u201d Gwen" in entries
    gwen = entries["\u201cBusty\u201d Gwen"]
    jester = entries["The Dark Jester in Mordheim"]
    # Gwen cobra por el escenario: su entrada no imprime tarifa, y los 75/30 que el
    # cotejo anterior le atribuía son los del Dark Jester, que es el vecino.
    assert cotejo.fees_in(gwen["text"]) == []
    assert cotejo.fees_in(jester["text"]) == [(75, "gold crowns", 30, "gold crowns")]
    # Y la fila de dos cifras (Ld 10) del Aksho se conserva entera.
    aksho = entries["Aksho'akhash the Vile Dreadwing, Lord of the Carrion Throne"]
    assert cotejo.stat_rows(aksho) == ["4534335210"]


@KB_CACHED
def test_the_seven_grade_2a_entries_verify_without_findings(tmp_path, monkeypatch) -> None:
    rows = grade_2a(run_cotejo(tmp_path, monkeypatch))
    assert set(rows) == set(GRADE_2A)
    for name, row in rows.items():
        assert row["findings"] == [], name
        assert row["comparable"] is True, name
        assert {"block", "rating", "rules"} <= set(row["checks"]), name


@KB_CACHED
def test_the_report_declares_its_coverage(tmp_path, monkeypatch) -> None:
    """Un «0 hallazgos» sin filas comparadas no es un «0 comprobado»."""
    rows = run_cotejo(tmp_path, monkeypatch)
    comparable = [row for row in rows
                  if row["comparable"] and row["file"].startswith("dramatis-personae")]
    counts = {check: sum(1 for row in comparable if check in row["checks"])
              for check in cotejo.CHECKS}
    assert counts == COVERAGE
    assert all(row["findings"] == [] for row in comparable)


@KB_CACHED
def test_the_profile_without_a_modelled_table_is_not_compared(tmp_path, monkeypatch) -> None:
    """El Horseman es jinete y montura y el catálogo lo deja sin tabla: se anota."""
    horseman = grade_2a(run_cotejo(tmp_path, monkeypatch))["The Headless Horseman"]
    assert horseman["checks"] == ["block", "rating", "rules"]
    notes = " ".join(horseman["notes"])
    assert "out_of_scope" in notes
    assert "la fuente imprime la tarifa 100 gold crowns" in notes
    assert "ni la fuente ni el paquete declaran características" in notes


@KB_CACHED
def test_an_editorial_rule_label_is_a_note_and_not_a_finding(tmp_path, monkeypatch) -> None:
    """La etiqueta que el árbol escribe para un hecho que la fuente imprime aparte."""
    william = grade_2a(run_cotejo(tmp_path, monkeypatch))[
        "William Sch\u00e4kestange, Master Bard"]
    assert "rules" in william["checks"]
    assert william["findings"] == []
    assert any("Conditional Acceptance" in note for note in william["notes"])


@STAGING_CACHED
def test_adjudicated_cases_verify_every_check(tmp_path, monkeypatch) -> None:
    """Los siete casos adjudicados de 2B cotejan hoy sin hallazgos ni chequeos de menos."""
    report = {entry["name"]: entry
              for entry in run_cotejo(tmp_path, monkeypatch, catalogue=STAGING,
                                      names=sorted(ADJUDICATED))}
    assert set(report) == set(ADJUDICATED)
    for name, entry in report.items():
        assert entry["findings"] == [], name
        assert set(entry["checks"]) == set(cotejo.CHECKS), name


# --------------------------------------------------------------------------- #
# El cotejo tiene que poder fallar
# --------------------------------------------------------------------------- #

@KB_CACHED
def test_a_fee_that_drifts_from_the_page_is_a_finding(tmp_path, monkeypatch) -> None:
    """La mutación: cambiar la tarifa de Sigmund en el contrato exige el hallazgo."""
    document = yaml.safe_load(KB.campaign.read_text(encoding="utf-8"))
    for entry in document["dramatis_personae"]:
        if entry["profile_id"] == "hireling.dramatis.sigmund-spindle-the-harvester-of-flesh":
            entry["hiring_fee"]["resources"]["gold_crowns"]["cost"] = 35
    mutated = tmp_path / "hired-swords-and-dramatis.yaml"
    mutated.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False),
                       encoding="utf-8")
    row = grade_2a(run_cotejo(tmp_path, monkeypatch, campaign=mutated))[
        "Sigmund Spindle, the Harvester of Flesh"]
    assert "fee" not in row["checks"]
    assert any("tarifa impresa" in finding and "70" in finding
               for finding in row["findings"])


@KB_CACHED
def test_a_stat_row_that_drifts_from_the_page_is_a_finding(tmp_path, monkeypatch) -> None:
    """Y una fila de stats: la del Foole contra la de su vecino."""
    document = yaml.safe_load((KB.root / "dramatis-personae/grade-2a.yaml").read_text(
        encoding="utf-8"))
    for profile in document["profiles"]:
        if profile["id"].endswith("the-foole"):
            profile["characteristics"]["Ld"] = 8
    sandbox = tmp_path / "dramatis-personae"
    sandbox.mkdir()
    (sandbox / "grade-2a.yaml").write_text(
        yaml.safe_dump(document, allow_unicode=True, sort_keys=False), encoding="utf-8")
    row = grade_2a(run_cotejo(tmp_path, monkeypatch, root=sandbox))["The Foole"]
    assert "stats" not in row["checks"]
    assert any("444431417" in finding for finding in row["findings"])


@STAGING_CACHED
def test_currency_regression_is_a_finding(tmp_path, monkeypatch) -> None:
    """La mutación: devolver la tarifa del Albino a coronas exige el hallazgo.

    Es el caso que la pasada cerró, así que la batería que hoy pasa tiene que fallar si
    alguien vuelve a convertir la divisa impresa: la tarifa impresa son 75 *warp tokens*,
    no 75 coronas.
    """
    document = yaml.safe_load(STAGING.campaign.read_text(encoding="utf-8"))
    for entry in document["hired_swords"]:
        if entry["profile_id"] == "hireling.hired-sword.albino-stormvermin":
            entry["hiring_fee"]["resources"]["gold_crowns"]["cost"] = 75
            entry["upkeep"]["resources"]["gold_crowns"]["cost"] = 30
    mutated = tmp_path / "campaign.yaml"
    mutated.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False),
                       encoding="utf-8")
    report = run_cotejo(tmp_path, monkeypatch, catalogue=STAGING, names=["Albino Stormvermin"],
                        campaign=mutated)
    assert report and "fee" not in report[0]["checks"]
    assert "warp tokens" in " ".join(report[0]["findings"])
