"""Staged ingestion of Mordheimer Grade 2a (Fan-tested) warbands.

The tooling for ``sources/2A`` — the isolated staging area described in
``sources/2A/README.md``. It **never writes to ``sources/knowledge``** and
never reads ``sources/2B`` except as a read-only item catalog for reference
resolution. Discovery and downloads write only to ``sources/2A/manifest.yaml``
and the ignored local cache ``build/cache/2a-sources/``.

Commands::

    python tools/knowledge/ingest_2a.py discover    # index table + dedicated pages
    python tools/knowledge/ingest_2a.py download    # snapshot pages (and cited PDFs)
    python tools/knowledge/ingest_2a.py extract     # draft text extraction into the cache
    python tools/knowledge/ingest_2a.py validate    # validate the staging tree
    python tools/knowledge/ingest_2a.py report      # progress by band and source

Unlike the 2B flow (PDF-first), the **primary source document of every 2A band
is its dedicated page** at ``https://mordheimer.net/docs/warbands/grade-2a-warbands/<slug>``.
The page snapshot is hashed into the manifest; PDFs of provenance cited by a
page are optional contrast documents. Page-declared metadata (``Grade``,
``Source``, ``Setting``, ``Version``) is recorded verbatim — including the two
known index/page grade discrepancies (snotlings declares "Grade: 2b",
order-of-the-mare declares "Grade: Heroic") — and must be resolved explicitly
before a row may reach ``promotable``.

Extraction is a **draft aid only**: the reviewed page (and its PDF of
provenance, when present) is the source of truth.
"""
from __future__ import annotations

import argparse
import hashlib
import html as html_module
import json
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
STAGING = ROOT / "sources" / "2A"
MANIFEST = STAGING / "manifest.yaml"
CACHE = ROOT / "build" / "cache" / "2a-sources"
KNOWLEDGE = ROOT / "sources" / "knowledge"
STAGING_2B = ROOT / "sources" / "2B"  # read-only item catalog cross-reference

MORDHEIMER_WARBANDS_URL = "https://mordheimer.net/docs/warbands"
GRADE_2A_PAGE_BASE = "https://mordheimer.net/docs/warbands/grade-2a-warbands/"

STATUS_ORDER = (
    "discovered", "source-verified", "text-extracted", "modeled",
    "english-reviewed", "translated", "validated", "promotable",
)

BAND_DOCUMENTS = ("band.yaml", "profiles.yaml", "equipment-access.yaml", "special-rules.yaml")

USER_AGENT = {"User-Agent": "Mozilla/5.0 (knowledge-ingest; mordheimer 2a staging)"}

EXPECTED_ROW_COUNT = 19

# Declared-source string -> stable source code (index wording varies;
# unmapped sources fall back to WEB).
SOURCE_CODES = {
    "mordheim facebook group": "FBG",
    "mordheimer's information centre": "MIC",
    "mordheimer's information centre web": "MIC",
    "sylvania supplement": "SYLV",
    "letters of the damned #1": "LOTD1",
    "letters of the damned #3": "LOTD3",
    "letters of the damned #4": "LOTD4",
    "letters of the damned #5": "LOTD5",
    "web": "WEB",
}


# --------------------------------------------------------------------------
# discovery
# --------------------------------------------------------------------------

TAG_RE = re.compile(r"<[^>]+>")
SECTION_RE = re.compile(
    r"id=\"grade-2a\".*?<table[^>]*>(.*?)</table>", re.S | re.I,
)
ROW_RE = re.compile(
    r"<tr[^>]*>\s*<td[^>]*>(?P<name>.*?)</td>\s*<td[^>]*>(?P<race>.*?)</td>\s*"
    r"<td[^>]*>(?P<setting>.*?)</td>\s*<td[^>]*>(?P<source>.*?)</td>\s*</tr>",
    re.S | re.I,
)
HREF_RE = re.compile(r"href=\"([^\"]*)\"", re.I)
META_RE = re.compile(
    r"Grade:\s*(?P<grade>.*?)\s+Source:\s*(?P<source>.*?)\s+Setting:\s*(?P<setting>.*?)"
    r"(?=(?:Version:|Lore|Special Rules|Last updated)|$)",
    re.S,
)


def unescape(text: str) -> str:
    text = html_module.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def slugify(name: str) -> str:
    """Dedicated-page slug. Verified against all 19 index rows."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug


def source_code_for(declared: str) -> str:
    return SOURCE_CODES.get(declared.lower().strip(), "WEB")


def fetch(url: str, timeout: int = 60) -> tuple[bytes, str]:
    request = urllib.request.Request(
        urllib.parse.quote(url, safe=":/?#%=&"), headers=USER_AGENT,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read()
        ctype = str(response.headers.get("Content-Type") or "")
    return data, ctype


def fetch_html(url: str) -> str:
    data, _ = fetch(url)
    return data.decode("utf-8", "replace")


def discover_rows(index_html: str) -> list[dict]:
    """Extract the Grade 2a table rows from the raw index HTML and resolve
    each band's dedicated page URL and page-declared metadata."""
    match = SECTION_RE.search(index_html)
    if not match:
        raise ValueError("Grade 2a table not found on the mordheimer.net index page")
    observed: list[dict] = []
    seen: set[str] = set()
    for row in ROW_RE.finditer(match.group(1)):
        name = unescape(TAG_RE.sub("", row.group("name")))
        race = unescape(TAG_RE.sub("", row.group("race")))
        setting = unescape(TAG_RE.sub("", row.group("setting")))
        declared = unescape(TAG_RE.sub("", row.group("source")))
        if not name or name.lower() == "warband":
            continue
        if name in seen:
            observed.append({"_problem": f"duplicate index row: {name}"})
            continue
        seen.add(name)
        # The dedicated-page slug comes straight from the index anchor when
        # present; slugify is only the fallback for unlinked rows.
        link = HREF_RE.search(row.group("name"))
        slug = link.group(1).rstrip("/").rsplit("/", 1)[-1] if link else slugify(name)
        observed.append({
            "mordheimer_name": name,
            "race": race,
            "setting": setting,
            "declared_source": declared,
            "source_code": source_code_for(declared),
            "slug": slug,
            "page_url": GRADE_2A_PAGE_BASE + slug,
        })
    if not observed:
        raise ValueError("Grade 2a table parsed to zero rows")
    return observed


def parse_page_metadata(page_html: str) -> dict:
    """Grade / Source / Setting / Version as declared by a dedicated page."""
    text = TAG_RE.sub(" ", page_html)
    text = html_module.unescape(text)
    text = re.sub(r"\s+", " ", text)
    match = META_RE.search(text)
    if not match:
        return {}
    meta = {
        "page_grade": unescape(match.group("grade")),
        "page_source": unescape(match.group("source")),
        "page_setting": unescape(match.group("setting")),
    }
    version = re.search(r"Version:\s*([^L]+?)(?=(?:Lore|Special Rules|Last updated)|$)", text)
    if version:
        meta["page_version"] = unescape(version.group(1))
    return meta


def provisional_id(name: str, source_code: str) -> str:
    words = re.findall(r"[a-z0-9]+", name.lower())
    return "-".join(["-".join(words or ["unnamed"]), source_code.lower()])


def load_manifest() -> list[dict]:
    if not MANIFEST.exists():
        return []
    document = yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}
    rows = document.get("bands") or []
    if not isinstance(rows, list):
        raise ValueError("manifest.yaml 'bands' must be a list")
    return rows


def save_manifest(rows: list[dict]) -> None:
    STAGING.mkdir(parents=True, exist_ok=True)
    document = {
        "schema_version": 1,
        "source_page": MORDHEIMER_WARBANDS_URL,
        "grade": "2a",
        "bands": rows,
    }
    text = yaml.safe_dump(
        document, sort_keys=False, allow_unicode=True, default_flow_style=False, width=100,
    )
    MANIFEST.write_text(text, encoding="utf-8", newline="\n")


def match_manifest(rows: list[dict], observed: list[dict]) -> tuple[list[dict], list[str]]:
    """Merge index rows into the manifest by ``mordheimer_name``."""
    problems: list[str] = []
    index = {row["mordheimer_name"]: row for row in rows if row.get("mordheimer_name")}
    duplicates = len(index) != len(rows)
    seen: set[str] = set()
    updated = list(rows)
    for item in observed:
        if "_problem" in item:
            problems.append(item["_problem"])
            continue
        name = item["mordheimer_name"]
        seen.add(name)
        row = index.get(name)
        if row is None:
            if duplicates:
                problems.append(f"manifest has duplicate keys; cannot match {name}")
                continue
            row = {
                "id": provisional_id(name, item["source_code"]),
                "mordheimer_name": name,
                "race": item["race"],
                "setting": item["setting"],
                "source_code": item["source_code"],
                "declared_source": item["declared_source"],
                "slug": item["slug"],
                "page_url": item["page_url"],
                "page_grade": None,
                "page_sha256": None,
                "page_size": None,
                "provenance_pdf_url": None,
                "provenance_sha256": None,
                "status": "discovered",
                "blockers": [],
                "notes": [],
            }
            updated.append(row)
            index[name] = row
        row["race"] = item["race"]
        row["setting"] = item["setting"]
        row["declared_source"] = item["declared_source"]
        row["slug"] = item["slug"]
        row["page_url"] = item["page_url"]
        if row.get("id") is None:
            row["id"] = provisional_id(name, item["source_code"])
    for row in updated:
        if row.get("mordheimer_name") not in seen:
            problems.append(
                f"manifest row no longer on mordheimer.net: {row.get('mordheimer_name')}"
            )
    if len(updated) != EXPECTED_ROW_COUNT:
        problems.append(
            f"index row count is {len(updated)}, expected {EXPECTED_ROW_COUNT}"
        )
    return updated, problems


def cmd_discover(args: argparse.Namespace) -> int:
    index_html = fetch_html(MORDHEIMER_WARBANDS_URL)
    observed = discover_rows(index_html)
    rows = load_manifest()
    updated, problems = match_manifest(rows, observed)
    if not args.dry_run:
        # Resolve dedicated pages now: verify the URL exists and record the
        # page-declared metadata (including grade discrepancies).
        for row in updated:
            try:
                page_html = fetch_html(str(row["page_url"]))
            except (urllib.error.URLError, OSError, TimeoutError) as error:
                row["blockers"] = sorted(set(row.get("blockers") or []) | {"source-unresolved"})
                problems.append(f"{row['id']}: dedicated page unreachable: {error}")
                continue
            meta = parse_page_metadata(page_html)
            row.update(meta)
            row["blockers"] = [
                b for b in (row.get("blockers") or []) if b != "source-unresolved"
            ]
    if args.dry_run:
        for problem in problems:
            print(f"PROBLEM {problem}")
        print(f"mordheimer rows: {len(observed)}; manifest rows: {len(rows)}; would write {MANIFEST}")
        return 1 if problems else 0
    save_manifest(updated)
    for problem in problems:
        print(f"PROBLEM {problem}")
    for row in updated:
        grade = row.get("page_grade")
        if grade and grade != "2a":
            print(f"GRADE  {row['id']}: page declares Grade {grade!r} (index says 2a)")
    print(f"manifest now tracks {len(updated)} rows -> {MANIFEST}")
    return 1 if problems else 0


# --------------------------------------------------------------------------
# download
# --------------------------------------------------------------------------

def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cmd_download(args: argparse.Namespace) -> int:
    rows = load_manifest()
    if not rows:
        print("manifest is empty; run 'discover' first", file=sys.stderr)
        return 1
    if CACHE.exists() and args.purge:
        shutil.rmtree(CACHE)
    (CACHE / "pages").mkdir(parents=True, exist_ok=True)
    (CACHE / "pdfs").mkdir(parents=True, exist_ok=True)
    failures = 0
    for row in rows:
        # 1. the dedicated page snapshot (primary source document)
        if not row.get("page_sha256") or args.refresh:
            url = str(row.get("page_url") or "")
            try:
                data, ctype = fetch(url, timeout=120)
            except (urllib.error.URLError, OSError, TimeoutError) as error:
                print(f"ERROR {row['id']}: page fetch failed: {error}")
                failures += 1
                continue
            if b"<html" not in data[:4096].lower():
                print(f"ERROR {row['id']}: response is not HTML ({url})")
                failures += 1
                continue
            target = CACHE / "pages" / f"{row['id']}.html"
            target.write_bytes(data)
            row["page_sha256"] = sha256_of(target)
            row["page_size"] = len(data)
            row["page_content_type"] = ctype.split(";")[0] or None
            meta = parse_page_metadata(data.decode("utf-8", "replace"))
            row.update(meta)
        # 2. the PDF of provenance, when one has been resolved (contrast doc)
        pdf_url = row.get("provenance_pdf_url")
        if pdf_url and (not row.get("provenance_sha256") or args.refresh):
            try:
                data, _ = fetch(str(pdf_url), timeout=180)
            except (urllib.error.URLError, OSError, TimeoutError) as error:
                print(f"ERROR {row['id']}: provenance PDF fetch failed: {error}")
                failures += 1
                continue
            if not data.startswith(b"%PDF"):
                print(f"ERROR {row['id']}: provenance response is not a PDF ({pdf_url})")
                failures += 1
                continue
            target = CACHE / "pdfs" / f"{row['id']}.pdf"
            target.write_bytes(data)
            row["provenance_sha256"] = sha256_of(target)
            row["provenance_size"] = len(data)
        if row.get("page_sha256"):
            row["status"] = STATUS_ORDER[max(
                STATUS_ORDER.index(row["status"]),
                STATUS_ORDER.index("source-verified"),
            )]
            print(f"OK    {row['id']}: page snapshot {row['page_size']} bytes  sha256={row['page_sha256'][:12]}…")
    save_manifest(rows)
    return 1 if failures else 0


# --------------------------------------------------------------------------
# extraction (draft aid only)
# --------------------------------------------------------------------------

BLOCK_TAG_RE = re.compile(
    r"</?(?:p|div|h[1-6]|li|tr|td|th|table|section|article|header|footer|ul|ol|blockquote)[^>]*>",
    re.I,
)
SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def html_to_text(page_html: str) -> str:
    text = SCRIPT_STYLE_RE.sub(" ", page_html)
    text = COMMENT_RE.sub(" ", text)
    text = BLOCK_TAG_RE.sub("\n", text)
    text = TAG_RE.sub(" ", text)
    text = html_module.unescape(text)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def cmd_extract(args: argparse.Namespace) -> int:
    rows = load_manifest()
    if not rows:
        print("manifest is empty; run 'discover' and 'download' first", file=sys.stderr)
        return 1
    text_dir = CACHE / "text"
    text_dir.mkdir(parents=True, exist_ok=True)
    failures = 0
    for row in rows:
        page_path = CACHE / "pages" / f"{row['id']}.html"
        if not page_path.exists():
            print(f"SKIP  {row['id']}: page snapshot not in cache")
            continue
        try:
            text = html_to_text(page_path.read_text(encoding="utf-8", errors="replace"))
        except Exception as error:  # noqa: BLE001 — log and continue per band
            print(f"ERROR {row['id']}: extraction failed: {error}")
            failures += 1
            continue
        start = text.find("Grade:")
        if start > 0:
            text = text[start:]
        end = text.find("Last updated")
        if end > 0:
            text = text[:end]
        if len(text.strip()) < 500:
            row["blockers"] = sorted(set(row.get("blockers") or []) | {"html-difficult"})
            print(f"LOW?  {row['id']}: extracted draft is suspiciously short ({len(text)} chars)")
            failures += 1
            continue
        row["blockers"] = [b for b in (row.get("blockers") or []) if b != "html-difficult"]
        (text_dir / f"{row['id']}.txt").write_text(text, encoding="utf-8")
        row["status"] = STATUS_ORDER[max(
            STATUS_ORDER.index(row["status"]), STATUS_ORDER.index("text-extracted"),
        )]
        print(f"OK    {row['id']}: draft -> {text_dir / (row['id'] + '.txt')}")
        # Optional provenance PDF draft (contrast document)
        pdf_path = CACHE / "pdfs" / f"{row['id']}.pdf"
        if pdf_path.exists():
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(pdf_path))
                draft = []
                for number, page in enumerate(reader.pages, start=1):
                    draft.append(f"\n===== page {number} =====\n")
                    draft.append(page.extract_text() or "")
                (text_dir / f"{row['id']}-provenance.txt").write_text(
                    "".join(draft), encoding="utf-8",
                )
                print(f"OK    {row['id']}: provenance PDF draft ({len(reader.pages)} pages)")
            except ImportError:
                print(f"NOTE  {row['id']}: pypdf not installed; provenance PDF not extracted")
            except Exception as error:  # noqa: BLE001
                print(f"ERROR {row['id']}: provenance extraction failed: {error}")
                failures += 1
    save_manifest(rows)
    return 1 if failures else 0


# --------------------------------------------------------------------------
# validation
# --------------------------------------------------------------------------

def validate(rows: list[dict]) -> list[str]:
    """Structural checks over the staging tree; returns a list of problems."""
    problems: list[str] = []

    seen_ids: set[str] = set()
    for row in rows:
        band_id = str(row.get("id") or "")
        label = band_id or str(row.get("mordheimer_name"))
        if not band_id:
            problems.append(f"{label}: manifest row has no id")
            continue
        if band_id in seen_ids:
            problems.append(f"{band_id}: duplicate band id in manifest")
        seen_ids.add(band_id)
        status = row.get("status")
        if status not in STATUS_ORDER:
            problems.append(f"{band_id}: unknown status {status!r}")
        blockers = row.get("blockers") or []
        if blockers and status in {"validated", "promotable"}:
            problems.append(f"{band_id}: status {status} must be blocker-free (has {blockers})")
        # Grade discrepancies between index and dedicated page must be
        # resolved (not silently accepted) before promotion. The known
        # discrepancies carry an explicit user decision (grade_resolved +
        # grade_decision) and promote as 2a.
        if status in {"validated", "promotable"} and str(row.get("page_grade") or "2a") != "2a":
            if not row.get("grade_resolved"):
                problems.append(
                    f"{band_id}: page_grade {row.get('page_grade')!r} != index grade 2a; "
                    "resolve the discrepancy before promotion"
                )
        if status == "discovered":
            continue
        if not row.get("page_sha256"):
            problems.append(f"{band_id}: status {status} but no page snapshot sha256 recorded")
        documents = STAGING / "bands" / "mordheim" / band_id
        if status not in {"modeled", "english-reviewed", "translated", "validated", "promotable"}:
            continue
        for document in BAND_DOCUMENTS:
            path = documents / document
            if not path.exists():
                problems.append(f"{band_id}: missing {document}")
                continue
            try:
                yaml.safe_load(path.read_text(encoding="utf-8"))
            except yaml.YAMLError as error:
                problems.append(f"{band_id}: {document} is not valid YAML: {error}")
        missing = [d for d in BAND_DOCUMENTS if not (documents / d).exists()]
        if missing:
            continue  # already reported above
        validate_band_references(band_id, documents, problems)
    return problems


def validate_runtime(
    rule_id: str, runtime: dict, band_id: str, problems: list[str], rule_kind: object = None
) -> None:
    """Hardened runtime contract (2B sweep lessons): string scopes only,
    effects inside runtime, reason on every unbound effect."""
    scope = runtime.get("scope")
    if scope not in ("YES", "NO", "LATER"):
        problems.append(
            f"{band_id}: rule {rule_id!r} runtime.scope must be 'YES'/'NO'/'LATER', "
            f"got {scope!r}"
        )
    if str(runtime.get("implemented")) not in ("YES", "NO"):
        problems.append(f"{band_id}: rule {rule_id!r} runtime.implemented must be 'YES'/'NO'")
    if runtime.get("grant") not in ("profile", "band", "selectable", "none"):
        problems.append(
            f"{band_id}: rule {rule_id!r} runtime.grant {runtime.get('grant')!r} is not a "
            f"runtime-schema value (profile/band/selectable/none)"
        )
    if runtime.get("grant") == "selectable" and str(rule_kind or "") not in (
        "warband_skill", "mutation", "blessing", "virtue", "mark", "modification",
        "profile_ability", "warband_variant",
    ):
        problems.append(
            f"{band_id}: selectable rule {rule_id!r} must declare a runtime-schema kind"
        )
    effects = runtime.get("effects")
    if not effects:
        # runtime-schema required_fields: scope, implemented, grant, effects.
        # Every KB rule carries a non-empty effects list, rule_ref included.
        problems.append(
            f"{band_id}: rule {rule_id!r} runtime has no effects; every classified rule "
            f"declares at least one effect entry"
        )
        return
    for effect in effects:
        if not isinstance(effect, dict):
            problems.append(f"{band_id}: rule {rule_id!r} has a non-dict effect")
            continue
        if not effect.get("id"):
            problems.append(f"{band_id}: rule {rule_id!r} has an effect without id")
        binding = effect.get("binding")
        if isinstance(binding, dict) and binding.get("kind") not in (
            "mechanic", "trait", "profile", "compiler"
        ):
            problems.append(
                f"{band_id}: rule {rule_id!r} binding kind {binding.get('kind')!r} is not a "
                f"runtime-schema value (mechanic/trait/profile/compiler)"
            )
        esc = str(effect.get("scope"))
        if esc not in ("YES", "NO", "LATER"):
            problems.append(f"{band_id}: rule {rule_id!r} effect scope {esc!r} invalid")
        if esc in ("NO", "LATER") and not effect.get("reason"):
            problems.append(
                f"{band_id}: rule {rule_id!r} unbound effect {effect.get('id')!r} has no reason"
            )
        if esc == "YES" and runtime.get("implemented") == "YES" and not effect.get("binding"):
            problems.append(
                f"{band_id}: rule {rule_id!r} YES effect {effect.get('id')!r} has no binding"
            )


def validate_band_references(band_id: str, documents: Path, problems: list[str]) -> None:
    """Check roster/profile/rule references of a fully modeled band package."""
    try:
        band = yaml.safe_load((documents / "band.yaml").read_text(encoding="utf-8")) or {}
        profiles_doc = yaml.safe_load((documents / "profiles.yaml").read_text(encoding="utf-8")) or {}
        rules_doc = yaml.safe_load((documents / "special-rules.yaml").read_text(encoding="utf-8")) or {}
        equipment_doc = yaml.safe_load((documents / "equipment-access.yaml").read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as error:
        problems.append(f"{band_id}: YAML parse failure during reference check: {error}")
        return

    if str(band.get("id") or "") != band_id:
        problems.append(f"{band_id}: band.yaml id does not match the directory")
    if band.get("grade") != "2a" or "2a" not in (band.get("categories") or []):
        problems.append(f"{band_id}: band.yaml must carry grade 2a / categories [2a]")
    if band.get("ruleset") != "mordheim":
        problems.append(f"{band_id}: band.yaml ruleset must be mordheim")

    # KB conformance: no fields outside the KB band.yaml pattern
    kb_band_keys = {
        "schema_version", "id", "canonical_family", "name", "name_i18n",
        "original_locale", "ruleset", "categories", "grade", "setting",
        "publication", "status", "sources", "roster", "rule_ids",
    }
    stray = sorted(set(band) - kb_band_keys)
    if stray:
        problems.append(f"{band_id}: band.yaml has non-KB keys {stray}")
    if "rule_ids" not in band:
        problems.append(f"{band_id}: band.yaml is missing the KB rule_ids field")

    profile_ids = {str(p.get("id") or "") for p in profiles_doc.get("profiles") or ()}
    profile_ids.discard("")
    for member in (band.get("roster") or {}).get("members") or ():
        profile_id = str(member.get("profile_id") or "")
        if not profile_id:
            problems.append(f"{band_id}: roster member without profile_id")
        elif profile_id not in profile_ids:
            problems.append(f"{band_id}: roster references unknown profile {profile_id!r}")

    rule_ids = {str(r.get("id") or "") for r in rules_doc.get("rules") or ()}
    rule_ids.discard("")
    for owner in [band, *(band.get("variants") or ())]:
        for rule_id in owner.get("rule_ids") or ():
            if rule_id not in rule_ids:
                problems.append(f"{band_id}: rule_ids reference unknown rule {rule_id!r}")

    for rule in rules_doc.get("rules") or ():
        rule_id = str(rule.get("id") or "?")
        runtime = rule.get("runtime") or {}
        # KB conformance: rule-id grammar and runtime-schema grant values
        if "--" not in rule_id:
            problems.append(f"{band_id}: rule id {rule_id!r} does not follow the KB <owner>--<name> grammar")
        else:
            owner = rule_id.split("--")[0]
            known_owners = set(profile_ids) | {"band"}
            if owner not in known_owners:
                problems.append(f"{band_id}: rule {rule_id!r} owner {owner!r} is neither 'band' nor a profile id")
        if not isinstance(runtime, dict):
            problems.append(f"{band_id}: rule {rule_id!r} has a non-dict runtime block")
            continue
        validate_runtime(rule_id, runtime, band_id, problems, rule.get("kind"))
        if "effects" in rule:
            problems.append(
                f"{band_id}: rule {rule_id!r} carries a rule-level 'effects' key; "
                f"effects belong inside runtime"
            )
        if rule.get("rule_ref"):
            ref = str(rule["rule_ref"])
            if ref not in kb_rule_ids():
                problems.append(
                    f"{band_id}: rule {rule_id!r} rule_ref {ref!r} not found in active KB"
                )
            if rule.get("effect") or rule.get("effect_i18n"):
                # KB pattern: a referencing rule carries no effect; every consumer
                # renders the shared record and ignores the local prose.
                problems.append(
                    f"{band_id}: rule {rule_id!r} references {ref!r} and restates the prose; "
                    f"the KB keeps the shared rule's text, so a rule_ref rule carries no effect"
                )
        elif not rule.get("effect"):
            problems.append(f"{band_id}: rule {rule_id!r} has no effect and no rule_ref")
        applies_to = rule.get("applies_to") or {}
        for profile_id in applies_to.get("profile_ids") or ():
            if profile_id not in profile_ids:
                problems.append(
                    f"{band_id}: rule {rule_id!r} applies to unknown profile {profile_id!r}"
                )
        # KB pairing: profile_ids never pairs with grant band, and band: true
        # never pairs with grant profile (0 cases in the active KB).
        runtime_grant = (rule.get("runtime") or {}).get("grant") if isinstance(
            rule.get("runtime"), dict) else None
        if "profile_ids" in applies_to and runtime_grant == "band":
            problems.append(
                f"{band_id}: rule {rule_id!r} applies_to.profile_ids with grant 'band'; "
                f"the KB uses 'profile'"
            )
        elif applies_to.get("band") and runtime_grant == "profile":
            problems.append(
                f"{band_id}: rule {rule_id!r} applies_to.band with grant 'profile'; "
                f"the KB uses 'band'"
            )

    band_rule_ids = {str(r.get("id")) for r in rules_doc.get("rules") or ()
                     if str(r.get("id", "")).startswith("band--")}
    listed_band_rules: set[str] = set(band.get("rule_ids") or ())
    for variant in band.get("variants") or ():
        listed_band_rules |= set(variant.get("rule_ids") or ())
    for rule_id in sorted(band_rule_ids - listed_band_rules):
        problems.append(f"{band_id}: band rule {rule_id!r} missing from band.yaml rule_ids")
    for profile in profiles_doc.get("profiles") or ():
        for rule_id in profile.get("rule_ids") or ():
            if str(rule_id).startswith("band--"):
                problems.append(
                    f"{band_id}: profile {profile.get('id')!r} lists band rule {rule_id!r}; "
                    f"the KB lists band rules only in band.yaml"
                )

    known_items = active_item_ids()
    for item_id in equipment_doc.get("starting_items") or ():
        if item_id not in known_items:
            problems.append(f"{band_id}: equipment references unknown item {item_id!r}")
    for key in sorted(set(equipment_doc) - {"schema_version", "band_id", "equipment_lists",
                                          "starting_items"}):
        problems.append(f"{band_id}: equipment-access.yaml key {key!r} is not a KB key")
    for equipment_list in equipment_doc.get("equipment_lists") or ():
        list_id = str(equipment_list.get("id") or "?")
        stray_list_keys = sorted(set(equipment_list) - {"id", "name", "items", "source", "loadouts"})
        if stray_list_keys:
            problems.append(
                f"{band_id}: equipment list {list_id!r} carries non-KB key(s) {stray_list_keys}"
            )
        for entry in equipment_list.get("items") or ():
            if not isinstance(entry, dict):
                continue
            item_id = str(entry.get("item_id") or "")
            if item_id and item_id not in known_items:
                problems.append(
                    f"{band_id}: equipment list {list_id!r} references unknown item {item_id!r}"
                )
            stray_item_keys = sorted(set(entry) - {"item_id", "cost", "notes", "price_override"})
            if stray_item_keys:
                problems.append(
                    f"{band_id}: equipment list {list_id!r} entry {item_id!r} carries "
                    f"non-KB key(s) {stray_item_keys}; availability remarks belong in 'notes'"
                )
    for profile in profiles_doc.get("profiles") or ():
        for item_id in profile.get("fixed_equipment") or ():
            if isinstance(item_id, str) and item_id and item_id not in known_items:
                problems.append(
                    f"{band_id}: profile {profile.get('id')!r} fixed_equipment references "
                    f"unknown item {item_id!r}"
                )


_KB_RULE_IDS: set[str] | None = None


def kb_rule_ids() -> set[str]:
    """IDs of every rule/condition defined by the active knowledge base."""
    global _KB_RULE_IDS
    if _KB_RULE_IDS is None:
        ids: set[str] = set()
        for path in (KNOWLEDGE / "catalog/rules").glob("*.yaml"):
            try:
                document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                continue
            for key in ("rules", "conditions"):
                for rule in document.get(key) or ():
                    if isinstance(rule, dict) and rule.get("id"):
                        ids.add(str(rule["id"]))
        _KB_RULE_IDS = ids
    return set(_KB_RULE_IDS)


def _catalog_items(catalog_dir: Path) -> set[str]:
    ids: set[str] = set()
    if not catalog_dir.exists():
        return ids
    for path in catalog_dir.rglob("*.yaml"):
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        for item in document.get("items") or ():
            if isinstance(item, dict) and item.get("id"):
                ids.add(str(item["id"]))
    return ids


_ACTIVE_ITEMS: set[str] | None = None


def active_item_ids() -> set[str]:
    """KB items plus the 2A and 2B provisional catalogs (read-only cross-reference:
    a 2A band may point at a 2B provisional item instead of duplicating it —
    the promotion-merge notes materialize it once)."""
    global _ACTIVE_ITEMS
    if _ACTIVE_ITEMS is None:
        ids = _catalog_items(KNOWLEDGE / "catalog/items")
        ids |= _catalog_items(STAGING / "catalog/items")
        ids |= _catalog_items(STAGING_2B / "catalog/items")
        _ACTIVE_ITEMS = ids
    return set(_ACTIVE_ITEMS)


def cmd_validate(_: argparse.Namespace) -> int:
    rows = load_manifest()
    problems = validate(rows)
    for problem in problems:
        print(f"PROBLEM {problem}")
    print(f"validated {len(rows)} manifest rows; {len(problems)} problem(s)")
    return 1 if problems else 0


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------

def cmd_report(args: argparse.Namespace) -> int:
    rows = load_manifest()
    if not rows:
        print("manifest is empty; run 'discover' first")
        return 0
    by_source: dict[str, list[dict]] = {}
    for row in sorted(rows, key=lambda r: (str(r.get("source_code")), str(r.get("id")))):
        by_source.setdefault(str(row.get("source_code")), []).append(row)
    if args.json:
        payload = {
            "total": len(rows),
            "by_status": {
                status: sum(1 for row in rows if row.get("status") == status)
                for status in STATUS_ORDER
            },
            "bands": [
                {
                    "id": row.get("id"),
                    "name": row.get("mordheimer_name"),
                    "source": row.get("source_code"),
                    "page_grade": row.get("page_grade"),
                    "status": row.get("status"),
                    "snapshot": bool(row.get("page_sha256")),
                    "blockers": row.get("blockers") or [],
                }
                for row in rows
            ],
        }
        print(json.dumps(payload, indent=2))
        return 0
    for source in sorted(by_source):
        print(f"\n== {source} ==")
        for row in by_source[source]:
            snapshot = "SNAP" if row.get("page_sha256") else "--  "
            grade = str(row.get("page_grade") or "-")
            blockers = ",".join(row.get("blockers") or []) or "-"
            print(
                f"  {str(row.get('id')):40s} {snapshot:4s} {grade:8s} "
                f"{str(row.get('status')):16s} {blockers}"
            )
    print(f"\ntotal: {len(rows)}")
    return 0


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    discover = sub.add_parser("discover", help="parse the mordheimer.net index and dedicated pages")
    discover.add_argument("--dry-run", action="store_true")

    download = sub.add_parser("download", help="snapshot dedicated pages (and cited PDFs) into the cache")
    download.add_argument("--refresh", action="store_true")
    download.add_argument("--purge", action="store_true")

    sub.add_parser("extract", help="draft text extraction into the cache")

    sub.add_parser("validate", help="validate the staging tree")

    report = sub.add_parser("report", help="progress by band and source")
    report.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "discover":
        return cmd_discover(args)
    if args.command == "download":
        return cmd_download(args)
    if args.command == "extract":
        return cmd_extract(args)
    if args.command == "validate":
        return cmd_validate(args)
    if args.command == "report":
        return cmd_report(args)
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
