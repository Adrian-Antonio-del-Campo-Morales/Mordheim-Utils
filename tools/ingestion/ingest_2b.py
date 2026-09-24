"""Staged ingestion of Broheim Grade 2b (Supplemental) warbands.

The tooling for ``sources/2B`` — the isolated staging area described in
``sources/2B/README.md``. It **never writes to ``sources/knowledge``**:
discovery and downloads write only to ``sources/2B/manifest.yaml`` and the
ignored local cache ``build/cache/2b-pdfs/``.

Commands::

    python tools/ingestion/ingest_2b.py discover    # compare Broheim rows to the manifest
    python tools/ingestion/ingest_2b.py download    # fetch PDFs, compute SHA-256, log redirects
    python tools/ingestion/ingest_2b.py extract     # draft text extraction into the cache
    python tools/ingestion/ingest_2b.py validate    # validate the staging tree
    python tools/ingestion/ingest_2b.py report      # progress by band and source

Manifest rows progress through::

    discovered -> pdf-verified -> text-extracted -> modeled
      -> english-reviewed -> translated -> validated -> promotable

Extraction is a **draft aid only**: the reviewed PDF is the source of truth.
PDF libraries (``pypdf``) are optional; without them ``extract`` reports what
must be installed and everything else keeps working. Escaped or non-PDF
responses are recorded in the manifest instead of being silently overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
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
STAGING = ROOT / "sources" / "2B"
MANIFEST = STAGING / "manifest.yaml"
CACHE = ROOT / "build" / "cache" / "2b-pdfs"
KNOWLEDGE = ROOT / "sources" / "knowledge"
BROHEIM_WARBANDS_URL = "https://broheim.net/warbands.html"
GRADE_2B_TABLE_ID = "grade2b"

STATUS_ORDER = (
    "discovered", "pdf-verified", "text-extracted", "modeled",
    "english-reviewed", "translated", "validated", "promotable",
)
BLOCKING_STATUSES = set(STATUS_ORDER) - {"discovered"}

BAND_DOCUMENTS = ("band.yaml", "profiles.yaml", "equipment-access.yaml", "special-rules.yaml")

USER_AGENT = {"User-Agent": "Mozilla/5.0 (knowledge-ingest; broheim 2b staging)"}


# --------------------------------------------------------------------------
# discovery
# --------------------------------------------------------------------------

ROW_RE = re.compile(
    r"<tr>\s*<td>(?P<name>.*?)</td>\s*<td>(?P<race>.*?)</td>\s*"
    r"<td>(?P<source>[A-Z0-9]+)\s*\|\s*<a[^>]*href=\"(?P<href>[^\"]+)\"[^>]*>\s*PDF\s*</a>\s*</td>\s*</tr>",
    re.S,
)
TAG_RE = re.compile(r"<[^>]+>")
PAGE_ANCHOR_RE = re.compile(r"#page=(\d+)$")


def unescape(text: str) -> str:
    """Minimal entity unescaping for the known Broheim page."""
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&apos;", "'")
    return text.strip()


def fetch_html(url: str) -> str:
    request = urllib.request.Request(url, headers=USER_AGENT)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", "replace")


def discover_rows(html: str) -> list[dict]:
    """Extract the Grade 2b table rows from the raw Broheim HTML."""
    match = re.search(
        rf"<table[^>]*id=\"{GRADE_2B_TABLE_ID}\"[^>]*>(.*?)</table>", html, re.S | re.I,
    )
    if not match:
        raise ValueError(f"Grade 2b table #{GRADE_2B_TABLE_ID} not found in {BROHEIM_WARBANDS_URL}")
    rows = []
    for row in ROW_RE.finditer(match.group(1)):
        name = unescape(TAG_RE.sub("", row.group("name")))
        race = unescape(TAG_RE.sub("", row.group("race")))
        href = unescape(row.group("href"))
        page = PAGE_ANCHOR_RE.search(href)
        if page:
            href = href[: href.rfind("#page=")]
        rows.append({
            "broheim_name": name,
            "race": race,
            "source_code": row.group("source"),
            "pdf_path": href,
            "pdf_page": int(page.group(1)) if page else None,
        })
    if not rows:
        raise ValueError(f"Grade 2b table #{GRADE_2B_TABLE_ID} parsed to zero rows")
    return rows


def source_code_slug(source_code: str) -> str:
    return source_code.lower()


def provisional_id(name: str, source_code: str) -> str:
    words = re.findall(r"[a-z0-9]+", name.lower())
    return "-".join(["-".join(words or ["unnamed"]), source_code_slug(source_code)])


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
        "source_page": BROHEIM_WARBANDS_URL,
        "grade": "2b",
        "bands": rows,
    }
    text = yaml.safe_dump(
        document, sort_keys=False, allow_unicode=True, default_flow_style=False, width=100,
    )
    MANIFEST.write_text(text, encoding="utf-8", newline="\n")


def match_manifest(rows: list[dict], observed: list[dict]) -> tuple[list[dict], list[str]]:
    """Merge Broheim rows into the manifest by ``broheim_name``+``source_code``."""
    problems: list[str] = []
    index = {
        (row["broheim_name"], row["source_code"]): row for row in rows
    }
    duplicates = len(index) != len(rows)
    seen = set()
    updated = list(rows)
    for item in observed:
        key = (item["broheim_name"], item["source_code"])
        if key in seen:
            problems.append(f"duplicate Broheim row: {key[0]} ({key[1]})")
            continue
        seen.add(key)
        row = index.get(key)
        if row is None:
            if duplicates:
                problems.append(f"manifest has duplicate keys; cannot match {key[0]} ({key[1]})")
                continue
            row = {
                "id": provisional_id(item["broheim_name"], item["source_code"]),
                "broheim_name": item["broheim_name"],
                "race": item["race"],
                "source_code": item["source_code"],
                "status": "discovered",
                "sha256": None,
                "pdf_size": None,
                "pdf_is_text": None,
                "blockers": [],
                "notes": [],
            }
            updated.append(row)
            index[key] = row
        row["race"] = item["race"]
        row["pdf_url"] = BROHEIM_WARBANDS_URL.rsplit("/", 1)[0] + "/" + item["pdf_path"]
        row["pdf_start_page"] = item["pdf_page"]
        if row.get("id") is None:
            row["id"] = provisional_id(item["broheim_name"], item["source_code"])
    for row in updated:
        if (row.get("broheim_name"), row.get("source_code")) not in seen:
            problems.append(
                f"manifest row no longer on Broheim: {row.get('broheim_name')} "
                f"({row.get('source_code')})"
            )
    return updated, problems


def cmd_discover(args: argparse.Namespace) -> int:
    html = fetch_html(BROHEIM_WARBANDS_URL)
    observed = discover_rows(html)
    rows = load_manifest()
    updated, problems = match_manifest(rows, observed)
    if args.dry_run:
        for problem in problems:
            print(f"PROBLEM {problem}")
        print(f"broheim rows: {len(observed)}; manifest rows: {len(rows)}; would write {MANIFEST}")
        return 1 if problems else 0
    save_manifest(updated)
    for problem in problems:
        print(f"PROBLEM {problem}")
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
    CACHE.mkdir(parents=True, exist_ok=True)
    failures = 0
    for row in rows:
        if row.get("sha256") and not args.refresh:
            continue
        url = row.get("pdf_url")
        if not url:
            print(f"SKIP  {row['id']}: no pdf_url")
            continue
        target = CACHE / f"{row['id']}.pdf"
        request = urllib.request.Request(
            urllib.parse.quote(str(url), safe=":/?#%=&")
        , headers=USER_AGENT)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = response.read()
        except (urllib.error.URLError, OSError, TimeoutError) as error:
            print(f"ERROR {row['id']}: {error}")
            failures += 1
            continue
        if not data.startswith(b"%PDF"):
            print(f"ERROR {row['id']}: response is not a PDF ({url})")
            failures += 1
            continue
        target.write_bytes(data)
        row["sha256"] = sha256_of(target)
        row["pdf_size"] = len(data)
        row["pdf_is_text"] = None  # decided by 'extract'
        row["status"] = STATUS_ORDER[max(STATUS_ORDER.index(row["status"]), STATUS_ORDER.index("pdf-verified"))]
        print(f"OK    {row['id']}: {len(data)} bytes  sha256={row['sha256'][:12]}…")
    save_manifest(rows)
    return 1 if failures else 0


# --------------------------------------------------------------------------
# extraction (draft aid only)
# --------------------------------------------------------------------------

def cmd_extract(args: argparse.Namespace) -> int:
    try:
        from pypdf import PdfReader
    except ImportError:
        print(
            "pypdf is not installed; extraction is unavailable.\n"
            "Install it with: pip install pypdf\n"
            "Everything else in this tool works without it.",
            file=sys.stderr,
        )
        return 1
    rows = load_manifest()
    if not rows:
        print("manifest is empty; run 'discover' and 'download' first", file=sys.stderr)
        return 1
    text_dir = CACHE / "text"
    text_dir.mkdir(parents=True, exist_ok=True)
    failures = 0
    for row in rows:
        pdf_path = CACHE / f"{row['id']}.pdf"
        if not pdf_path.exists():
            print(f"SKIP  {row['id']}: PDF not in cache")
            continue
        try:
            reader = PdfReader(str(pdf_path))
            page_count = len(reader.pages)
            draft = []
            for number, page in enumerate(reader.pages, start=1):
                draft.append(f"\n===== page {number} =====\n")
                draft.append(page.extract_text() or "")
            text = "".join(draft)
        except Exception as error:  # noqa: BLE001 — log and continue per band
            print(f"ERROR {row['id']}: extraction failed: {error}")
            failures += 1
            continue
        # A near-empty extraction on a multi-page document means the pages
        # are scanned images: draft text is useless and OCR is required.
        # (Page markers alone add ~20 chars per page.)
        printable = page_count > 0 and len(text.strip()) >= 40 * page_count
        row["pdf_is_text"] = printable
        row["pdf_pages"] = page_count
        if not printable:
            row["blockers"] = sorted(set((row.get("blockers") or [])) | {"ocr-required"})
            # A doubt reverts the row to its previous state: the draft text
            # does not exist, so 'text-extracted' has not been reached.
            row["status"] = "pdf-verified"
            print(f"OCR?  {row['id']}: no extractable text ({page_count} pages)")
        else:
            row["blockers"] = [b for b in (row.get("blockers") or []) if b != "ocr-required"]
            (text_dir / f"{row['id']}.txt").write_text(text, encoding="utf-8")
            row["status"] = STATUS_ORDER[max(
                STATUS_ORDER.index(row["status"]), STATUS_ORDER.index("text-extracted"),
            )]
            print(f"OK    {row['id']}: {page_count} pages -> {text_dir / (row['id'] + '.txt')}")
    save_manifest(rows)
    return 1 if failures else 0


# --------------------------------------------------------------------------
# validation
# --------------------------------------------------------------------------

def validate(rows: list[dict]) -> list[str]:
    """Structural checks over the staging tree; returns a list of problems."""
    problems: list[str] = []

    seen_ids: set[str] = set()
    claimed: set[str] = set()
    for row in rows:
        band_id = str(row.get("id") or "")
        label = band_id or str(row.get("broheim_name"))
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
        # A source document may print more than one warband list; 'packages' declares
        # every band package the row produced (defaults to the row id itself).
        packages = [str(package) for package in row.get("packages") or [] if str(package).strip()]
        if packages and band_id not in packages:
            problems.append(f"{band_id}: 'packages' must include the row's own id")
        packages = packages or [band_id]
        for package in packages:
            if package in claimed:
                problems.append(f"{package}: package claimed by more than one manifest row")
            claimed.add(package)
        if status == "discovered":
            continue
        if not row.get("sha256"):
            problems.append(f"{band_id}: status {status} but no sha256 recorded")
        if status not in {"modeled", "english-reviewed", "translated", "validated", "promotable"}:
            continue
        for package in packages:
            documents = STAGING / "bands" / "mordheim" / package
            for document in BAND_DOCUMENTS:
                path = documents / document
                if not path.exists():
                    problems.append(f"{package}: missing {document}")
                    continue
                try:
                    yaml.safe_load(path.read_text(encoding="utf-8"))
                except yaml.YAMLError as error:
                    problems.append(f"{package}: {document} is not valid YAML: {error}")
            missing = [d for d in BAND_DOCUMENTS
                       if not (documents / d).exists()]
            if missing:
                continue  # already reported above
            validate_band_references(package, documents, problems)
    bands_root = STAGING / "bands" / "mordheim"
    if bands_root.exists():
        for directory in sorted(bands_root.iterdir()):
            if directory.is_dir() and directory.name not in claimed:
                problems.append(
                    f"{directory.name}: staging package is not declared by any manifest row "
                    f"(add it to that row's 'packages')"
                )
    return problems


def validate_runtime(
    rule_id: str, runtime: dict, band_id: str, problems: list[str], rule_kind: object = None
) -> None:
    """Hardened runtime contract (2A sweep lessons): schema scopes/grant,/kinds only."""
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
    if band.get("grade") != "2b" or "2b" not in (band.get("categories") or []):
        problems.append(f"{band_id}: band.yaml must carry grade 2b / categories [2b]")
    if band.get("ruleset") != "mordheim":
        problems.append(f"{band_id}: band.yaml ruleset must be mordheim")

    # KB conformance: no fields outside the KB band.yaml pattern
    kb_band_keys = {
        "schema_version", "id", "canonical_family", "name", "name_i18n",
        "original_locale", "ruleset", "categories", "grade", "setting",
        "publication", "status", "sources", "roster", "rule_ids", "variants",
    }
    stray = sorted(set(band) - kb_band_keys)
    if stray:
        problems.append(f"{band_id}: band.yaml has non-KB keys {stray}")
    if "rule_ids" not in band:
        problems.append(f"{band_id}: band.yaml is missing the KB rule_ids field")

    # KB conformance: roster key set and member key set (KB: profile_id/min/max/group_size)
    kb_roster_keys = {"minimum_models", "maximum_models", "starting_gold", "members"}
    stray_roster = sorted(set(roster := (band.get("roster") or {})) - kb_roster_keys)
    if stray_roster:
        problems.append(f"{band_id}: roster has non-KB keys {stray_roster}")
    for member in (band.get("roster") or {}).get("members") or ():
        stray_member = sorted(set(member) - {"profile_id", "minimum", "maximum", "group_size"})
        if stray_member:
            problems.append(
                f"{band_id}: roster member {member.get('profile_id')!r} has non-KB keys {stray_member}"
            )

    profile_ids = {str(p.get("id") or "") for p in profiles_doc.get("profiles") or ()}
    profile_ids.discard("")
    characteristics_keys = ["M", "WS", "BS", "S", "T", "W", "I", "A", "Ld"]
    for profile in profiles_doc.get("profiles") or ():
        profile_id = profile.get("id")
        if profile.get("type") not in ("hero", "henchman", "animal"):
            problems.append(
                f"{band_id}: profile {profile_id!r} type {profile.get('type')!r} is not a KB value "
                f"(hero/henchman/animal)"
            )
        if "references" in profile:
            problems.append(
                f"{band_id}: profile {profile_id!r} uses the non-KB 'references' field; KB profiles "
                f"are self-contained"
            )
        chars = profile.get("characteristics") or {}
        if list(chars) != characteristics_keys:
            problems.append(
                f"{band_id}: profile {profile_id!r} characteristics must list all nine KB keys, "
                f"got {list(chars)}"
            )

    roster_members = band.get("roster") or {}
    for member in roster_members.get("members") or ():
        profile_id = str(member.get("profile_id") or "")
        if not profile_id:
            problems.append(f"{band_id}: roster member without profile_id")
        elif profile_id not in profile_ids:
            problems.append(f"{band_id}: roster references unknown profile {profile_id!r}")

    rule_ids = {str(r.get("id") or "") for r in rules_doc.get("rules") or ()}
    rule_ids.discard("")
    kb_rule_ids: set[str] = set()
    for rule in rules_doc.get("rules") or ():
        rule_id = str(rule.get("id") or "?")
        runtime = rule.get("runtime") or {}
        # KB conformance: rule-id grammar and runtime-schema values
        if "--" not in rule_id:
            problems.append(
                f"{band_id}: rule id {rule_id!r} does not follow the KB <owner>--<name> grammar"
            )
        else:
            owner = rule_id.split("--")[0]
            if owner != "band" and owner not in profile_ids:
                problems.append(
                    f"{band_id}: rule {rule_id!r} owner {owner!r} is neither 'band' nor a profile id"
                )
        if not isinstance(runtime, dict):
            problems.append(f"{band_id}: rule {rule_id!r} has a non-dict runtime block")
            continue
        validate_runtime(rule_id, runtime, band_id, problems, rule.get("kind"))
        if "effects" in rule:
            problems.append(
                f"{band_id}: rule {rule_id!r} carries a rule-level 'effects' key; "
                f"effects belong inside runtime"
            )
        if rule.get("applies_to") and "profiles" in (rule.get("applies_to") or {}):
            problems.append(
                f"{band_id}: rule {rule_id!r} applies_to uses 'profiles'; the KB key is 'profile_ids'"
            )
        if rule.get("rule_ref"):
            ref = str(rule["rule_ref"])
            kb_rule_ids.add(ref)
            if ref not in _kb_rule_ids():
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
            continue
        if not rule.get("effect"):
            problems.append(f"{band_id}: rule {rule_id!r} has no effect and no rule_ref")
    owners = [band, *(band.get("variants") or ())]
    band_level_rules = {rid for rid in rule_ids if rid.startswith("band--")}
    all_listed: set[str] = set()
    for owner in owners:
        # KB pattern (Tileans): the band lists its own band-- rules and each variant
        # lists the rules it introduces; together they must cover every band-- rule.
        for rule_id in owner.get("rule_ids") or ():
            all_listed.add(rule_id)
            if rule_id not in rule_ids:
                problems.append(f"{band_id}: rule_ids reference unknown rule {rule_id!r}")
            elif not rule_id.startswith("band--"):
                problems.append(
                    f"{band_id}: band.yaml rule_ids lists profile rule {rule_id!r}; "
                    f"the KB lists only band-- rules there"
                )
    for rule_id in sorted(band_level_rules - all_listed):
        problems.append(f"{band_id}: band rule {rule_id!r} missing from band.yaml rule_ids")

    band_profile_ids = profile_ids
    for rule in rules_doc.get("rules") or ():
        for profile_id in (rule.get("applies_to") or {}).get("profile_ids") or ():
            if profile_id not in band_profile_ids:
                problems.append(
                    f"{band_id}: rule {rule.get('id')!r} applies to unknown profile {profile_id!r}"
                )
    for profile in profiles_doc.get("profiles") or ():
        for rule_id in profile.get("rule_ids") or ():
            if rule_id.startswith("band--"):
                problems.append(
                    f"{band_id}: profile {profile.get('id')!r} lists band rule {rule_id!r}; "
                    f"the KB lists band rules only in band.yaml"
                )
            elif rule_id not in rule_ids:
                problems.append(
                    f"{band_id}: profile {profile.get('id')!r} references unknown rule {rule_id!r}"
                )

    known_items = active_item_ids()
    for item_id in equipment_doc.get("starting_items") or ():
        if item_id not in known_items:
            problems.append(f"{band_id}: equipment references unknown item {item_id!r}")
    for equipment_list in equipment_doc.get("equipment_lists") or ():
        list_id = str(equipment_list.get("id") or "?")
        for entry in equipment_list.get("items") or ():
            if not isinstance(entry, dict):
                continue
            item_id = str(entry.get("item_id") or "")
            if item_id and item_id not in known_items:
                problems.append(
                    f"{band_id}: equipment list {list_id!r} references unknown item {item_id!r}"
                )
            stray_keys = sorted(set(entry) - {"item_id", "cost", "notes", "price_override"})
            if stray_keys:
                problems.append(
                    f"{band_id}: equipment list {list_id!r} item {item_id!r} has non-KB keys "
                    f"{stray_keys}; availability remarks belong in 'notes'"
                )
        stray_list_keys = sorted(set(equipment_list) - {"id", "name", "items", "source", "loadouts"})
        if stray_list_keys:
            problems.append(
                f"{band_id}: equipment list {list_id!r} carries non-KB key(s) {stray_list_keys}"
            )
    for profile in profiles_doc.get("profiles") or ():
        for item_id in profile.get("fixed_equipment") or ():
            if isinstance(item_id, str) and item_id and item_id not in known_items:
                problems.append(
                    f"{band_id}: profile {profile.get('id')!r} fixed_equipment references "
                    f"unknown item {item_id!r}"
                )


_KB_RULE_IDS: set[str] | None = None


_ACTIVE_ITEMS: list[str] | None = None


def _kb_rule_ids() -> set[str]:
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


def active_item_ids() -> set[str]:
    """IDs of the active knowledge base plus the 2B provisional catalogue."""
    global _ACTIVE_ITEMS
    if _ACTIVE_ITEMS is None:
        ids: set[str] = set()
        for path in (KNOWLEDGE / "catalog/items").glob("*.yaml"):
            try:
                document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                continue
            for item in document.get("items") or ():
                if isinstance(item, dict) and item.get("id"):
                    ids.add(str(item["id"]))
        provisional = STAGING / "catalog/items"
        if provisional.exists():
            for path in provisional.rglob("*.yaml"):
                try:
                    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                except yaml.YAMLError:
                    continue
                for item in document.get("items") or ():
                    if isinstance(item, dict) and item.get("id"):
                        ids.add(str(item["id"]))
        _ACTIVE_ITEMS = sorted(ids)
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
                    "name": row.get("broheim_name"),
                    "source": row.get("source_code"),
                    "status": row.get("status"),
                    "pdf": bool(row.get("sha256")),
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
            pdf = "PDF" if row.get("sha256") else "-- "
            blockers = ",".join(row.get("blockers") or []) or "-"
            print(f"  {str(row.get('id')):36s} {pdf:4s} {str(row.get('status')):16s} {blockers}")
    print(f"\ntotal: {len(rows)}")
    return 0


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    discover = sub.add_parser("discover", help="fetch Broheim and reconcile the manifest")
    discover.add_argument("--dry-run", action="store_true")
    download = sub.add_parser("download", help="fetch PDFs into the ignored cache")
    download.add_argument("--refresh", action="store_true", help="re-download even if hashed")
    download.add_argument("--purge", action="store_true", help="empty the cache first")
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
