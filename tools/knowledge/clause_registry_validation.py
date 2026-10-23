"""Maintained structural checks for the clause register.

No Git baseline or generated audit files are required. Conservation against the
current snapshot is enforced by clause_registry.py, not reconstructed from historical data.
"""
import collections
import csv
import io
import json

FIELDS = ["id", "clause_id", "source_file", "source_fingerprint",
          "clause_text", "clause_scope", "semantic_contract", "effect_id", "relation",
          "parameters", "conditions", "consumer", "pending", "verification", "notes", "status"]

SCOPES = {"YES", "NO", "LATER", "UNCLASSIFIED"}
REL = {"equivalent", "independent", "related", "unresolved", "parameterized_variant"}
WORK = {"", "none", "connection", "assessment", "data", "behavior", "projection", "product"}
STATUS = {"reviewed", "source_blocked", "needs_clarification"}
EV = {"inspection", "none", "executed"}
BACKENDS = ("numpy", "native")
BACKEND_STATES = {"pending", "in_progress", "implemented", "verified", "blocked"}
OBJ_FIELDS = ("parameters", "conditions", "pending", "status")
ARR_FIELDS = ("consumer", "verification")


def check(raw, base, audit_rows=None, *, legacy=False):
    """Return a list of violation strings for the CSV bytes `raw`.

    `base` maps (id, clause_id) -> baseline row dict.  `audit_rows`, when
    given, is the generated inventory; each id must be covered by an origin or
    current identity unless its scope is explicitly NO.
    """
    fields = FIELDS[:-1] if legacy else FIELDS
    v = []
    if raw[:3] == b"\xef\xbb\xbf":
        v.append("UTF-8 BOM present (expected none)")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return ["not valid UTF-8: %s" % exc]
    if b"\r" in raw:
        v.append("CR byte present (expected LF-only line endings)")
    if raw and not raw.endswith(b"\n"):
        v.append("file does not end with a newline")

    records = list(csv.reader(io.StringIO(text)))
    if not records:
        return ["file is empty"]
    if records[0] != fields:
        v.append("header is not the exact %d-column sequence: %r" % (len(fields), records[0]))
        return v  # a wrong header invalidates every later position check
    bad_width = False
    for i, rec in enumerate(records[1:], start=2):
        if len(rec) != len(fields):
            v.append("record on line %d has %d fields (expected %d)" % (i, len(rec), len(fields)))
            bad_width = True
    if bad_width:
        return v

    rows = list(csv.DictReader(io.StringIO(text)))

    for r in rows:
        where = "%s / %s" % (r["id"], r["clause_id"])
        if r["clause_scope"] not in SCOPES:
            v.append("invalid clause_scope %r at %s" % (r["clause_scope"], where))
        if r["relation"] not in REL:
            v.append("invalid relation %r at %s" % (r["relation"], where))
        try:
            pending = json.loads(r["pending"])
        except (ValueError, TypeError):
            pending = None
        if isinstance(pending, dict):
            if set(pending) - {"work", "review", "requires"}:
                v.append("unknown pending keys at " + where)
            if pending.get("work", "none") not in WORK:
                v.append("invalid pending.work at " + where)
            if pending.get("review", "reviewed") not in STATUS:
                v.append("invalid pending.review at " + where)
            required = pending.get("requires", [])
            if not isinstance(required, list) or not all(isinstance(x, str) for x in required):
                v.append("pending.requires is not an array of strings at " + where)
        if not legacy:
            try:
                status = json.loads(r["status"])
            except (ValueError, TypeError):
                status = None
            if isinstance(status, dict):
                if set(status) - set(BACKENDS):
                    v.append("unknown status backend at " + where)
                if any(not isinstance(value, str) or value not in BACKEND_STATES
                       for value in status.values()):
                    v.append("invalid backend status at " + where)
                expected = set(BACKENDS) if r["clause_scope"] == "YES" else set()
                if set(status) != expected:
                    v.append("status keys disagree with clause_scope at " + where)
        for f in (OBJ_FIELDS[:-1] if legacy else OBJ_FIELDS):
            try:
                val = json.loads(r[f])
            except Exception:
                v.append("%s is not valid JSON at %s" % (f, where))
                continue
            if not isinstance(val, dict):
                v.append("%s is not a JSON object at %s" % (f, where))
        for f in ARR_FIELDS:
            try:
                val = json.loads(r[f])
            except Exception:
                v.append("%s is not valid JSON at %s" % (f, where))
                continue
            if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
                v.append("%s is not a JSON array of strings at %s" % (f, where))
            elif f == "verification" and (not val or val[0] not in EV):
                v.append("verification must start with its evidence kind at " + where)

    counts = collections.Counter((r["id"], r["clause_id"]) for r in rows)
    for key, n in counts.items():
        if n > 1:
            v.append("duplicate (id, clause_id) x%d: %s" % (n, key))

    cur = {(r["id"], r["clause_id"]): r for r in rows}
    for key, brow in base.items():
        if key not in cur:
            v.append("historical clause lost: %s" % (key,))
        elif cur[key]["source_fingerprint"] != brow["source_fingerprint"]:
            v.append("source_fingerprint changed for %s" % (key,))

    if audit_rows is not None:
        legend = _audit_identities(rows, base)
        for a in audit_rows:
            if a["id"] in legend:
                continue
            if a.get("scope") == "NO":
                continue  # explicitly justified exclusion
            v.append("admitted audit identity without correspondence: id=%s scope=%s"
                     % (a["id"], a.get("scope")))
    return v


def _audit_identities(rows, base):
    """Reconcile a historical audit without keeping obsolete IDs in the CSV."""
    current = {row["id"] for row in rows}
    historical = {row["origin_id"] for row in base.values()
                  if "origin_id" in row
                  and (row.get("current_id") or row["origin_id"]) in current}
    return current | historical

