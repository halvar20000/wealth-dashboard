"""A document archive the app pulls statements from — Paperless-ngx.

Somebody who scans every letter into Paperless-ngx has years of
statements in it, tagged by bank and by kind. Uploading them one by one
to the import page is work the archive has already done. So the app
asks the archive instead: every account says which documents are its —
by tag, by correspondent, by a query — and on the daily sync each new
one is fetched and run through exactly the recognisers an upload goes
through. The archive is read; never written.

Three things worth knowing.

**Every document is remembered, whatever became of it.** One row per
document and account: imported, or not read, or the fetch failed. A
second pull costs one listing and nothing is imported twice — and a
document no reader understood is listed by name with a link back, not
skipped in silence. When a reader for its layout arrives, *Try again*
forgets the not-read rows so the next pull has another go.

**A scan has no text; Paperless already made some.** A PDF that is only
an image is nothing to the readers, but Paperless ran OCR on it and
serves the result. When the original is not recognised, its OCR text is
offered to the statement readers before the document is given up on —
a clean scan of a known layout reads the same way its download would.

**The pull is generic; the reading is not.** A document becomes
transactions only when there is a reader for what it is — the CSV and
PDF importers in `importers/`, the mappings the user drew. Pulling a
statement from a bank the app has never seen changes nothing about
that, and the page says so rather than implying otherwise.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from . import importers, settings
from .db import get_conn, get_state, set_state

TOKEN_FILE = "paperless_token"
TIMEOUT = 30
PAGE_SIZE = 100
USER_AGENT = "wealth-dashboard"


class ArchiveError(Exception):
    pass


# ─── Set-up ──────────────────────────────────────────────────────────

def url() -> str:
    return (settings.get("archive_url") or "").strip().rstrip("/")


def configured() -> bool:
    return bool(url()) and (settings.SECRETS_DIR / TOKEN_FILE).exists()


def save(base_url: str, token: str) -> None:
    """The archive's address in settings, the token beside the bank key.
    A token left blank keeps the one already saved, so changing the URL
    does not mean pasting the token again."""
    base_url = (base_url or "").strip().rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        raise ValueError("The archive's address needs to start with http:// or https://.")
    token = (token or "").strip()
    if not token and not (settings.SECRETS_DIR / TOKEN_FILE).exists():
        raise ValueError("The archive needs an API token — Paperless makes one under "
                         "My Profile.")
    cfg = settings.load()
    cfg["archive_url"] = base_url
    settings.save(cfg)
    if token:
        settings.ensure_dirs()
        path = settings.SECRETS_DIR / TOKEN_FILE
        path.write_text(token)
        try:
            path.chmod(0o600)
        except OSError:
            pass


def forget() -> None:
    cfg = settings.load()
    cfg.pop("archive_url", None)
    settings.save(cfg)
    try:
        (settings.SECRETS_DIR / TOKEN_FILE).unlink()
    except FileNotFoundError:
        pass


def _token() -> str:
    try:
        return (settings.SECRETS_DIR / TOKEN_FILE).read_text().strip()
    except OSError:
        raise ArchiveError("The archive is not set up — add its address and token "
                           "under Settings.") from None


# ─── The client ──────────────────────────────────────────────────────

def _urllib_transport(method: str, full_url: str, headers: dict, body: bytes | None):
    req = urllib.request.Request(full_url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), exc.read()
    except (urllib.error.URLError, OSError) as exc:
        raise ArchiveError(f"Could not reach the archive: {exc.reason if hasattr(exc, 'reason') else exc}")


class Client:
    def __init__(self, base_url: str, token: str, transport=None):
        self.base = base_url.rstrip("/")
        self.token = token
        self.transport = transport or _urllib_transport

    def _get(self, path: str, params: dict | None = None, raw: bool = False):
        full = self.base + path
        if params:
            full += ("&" if "?" in full else "?") + urllib.parse.urlencode(params)
        headers = {"Authorization": f"Token {self.token}", "User-Agent": USER_AGENT,
                   "Accept": "application/octet-stream" if raw else "application/json"}
        status, resp_headers, body = self.transport("GET", full, headers, None)
        if status == 401 or status == 403:
            raise ArchiveError("The archive refused the token — make a new one under "
                               "My Profile in Paperless and paste it again.")
        if status >= 400:
            raise ArchiveError(f"The archive answered {status} for {path}.")
        if raw:
            return body, resp_headers
        try:
            return json.loads(body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise ArchiveError(f"The archive did not answer with JSON for {path} — is the "
                               "address the Paperless root, without /api?") from None

    def _all(self, path: str, params: dict) -> list[dict]:
        """Every page of a list endpoint."""
        out: list[dict] = []
        page = 1
        while True:
            data = self._get(path, {**params, "page": page, "page_size": PAGE_SIZE})
            out.extend(data.get("results") or [])
            if not data.get("next") or not data.get("results"):
                return out
            page += 1

    def tags(self) -> list[dict]:
        return self._all("/api/tags/", {"ordering": "name"})

    def correspondents(self) -> list[dict]:
        return self._all("/api/correspondents/", {"ordering": "name"})

    def documents(self, filt: dict) -> list[dict]:
        """The documents a filter matches, newest first.

        Tags and a correspondent are given by name and resolved to ids
        here, because names are what a person types and ids are what
        Paperless filters by; every named tag must be on the document.
        """
        params: dict = {"ordering": "-created",
                        "fields": "id,title,created,original_file_name,archived_file_name"}
        names = [t.strip() for t in (filt.get("tags") or "").split(",") if t.strip()]
        if names:
            by_name = {t["name"].lower(): t["id"] for t in self.tags()}
            missing = [n for n in names if n.lower() not in by_name]
            if missing:
                raise ArchiveError("No such tag in the archive: " + ", ".join(missing))
            params["tags__id__all"] = ",".join(str(by_name[n.lower()]) for n in names)
        if (filt.get("correspondent") or "").strip():
            want = filt["correspondent"].strip().lower()
            match = [c for c in self.correspondents() if c["name"].lower() == want]
            if not match:
                raise ArchiveError(f"No such correspondent in the archive: {filt['correspondent']}")
            params["correspondent__id"] = match[0]["id"]
        if (filt.get("query") or "").strip():
            params["query"] = filt["query"].strip()
        return self._all("/api/documents/", params)

    def download(self, doc_id: int) -> tuple[bytes, str]:
        """The original file, and its name."""
        body, headers = self._get(f"/api/documents/{doc_id}/download/", {"original": "true"}, raw=True)
        disposition = headers.get("Content-Disposition") or headers.get("content-disposition") or ""
        name = ""
        for part in disposition.split(";"):
            part = part.strip()
            if part.startswith("filename*="):
                name = urllib.parse.unquote(part.split("''", 1)[-1])
            elif part.startswith("filename=") and not name:
                name = part[len("filename="):].strip('"')
        return body, name or f"document-{doc_id}"

    def content(self, doc_id: int) -> str:
        """Paperless's OCR text of the document."""
        return (self._get(f"/api/documents/{doc_id}/", {"fields": "id,content"}).get("content") or "")


def client(transport=None) -> Client:
    if not url():
        raise ArchiveError("The archive is not set up — add its address and token under Settings.")
    return Client(url(), _token(), transport)


def check(transport=None) -> dict:
    """A live look: the token works, and how much is there."""
    api = client(transport)
    docs = api._get("/api/documents/", {"page_size": 1, "fields": "id"})
    tags = api.tags()
    return {"documents": int(docs.get("count") or 0), "tags": [t["name"] for t in tags]}


# ─── Which documents are whose ───────────────────────────────────────

def filters() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT f.*, a.name AS account, a.currency FROM archive_filters f "
            "JOIN accounts a ON a.id = f.account_id ORDER BY a.name").fetchall()
    return [dict(r) for r in rows]


def filter_for(account_id: int) -> dict | None:
    with get_conn() as conn:
        r = conn.execute("SELECT * FROM archive_filters WHERE account_id = ?",
                         (account_id,)).fetchone()
    return dict(r) if r else None


def set_filter(account_id: int, tags: str, correspondent: str, query: str) -> None:
    """What the account pulls. All three blank means: nothing, and the
    row goes — an account with no filter is an account the pull skips."""
    tags = ", ".join(t.strip() for t in (tags or "").split(",") if t.strip())[:200]
    correspondent = " ".join((correspondent or "").split())[:120]
    query = " ".join((query or "").split())[:200]
    with get_conn() as conn:
        conn.execute("DELETE FROM archive_filters WHERE account_id = ?", (account_id,))
        if tags or correspondent or query:
            conn.execute("INSERT INTO archive_filters (account_id, tags, correspondent, query) "
                         "VALUES (?, ?, ?, ?)", (account_id, tags, correspondent, query))


# ─── The pull ────────────────────────────────────────────────────────

def _seen(conn, account_id: int) -> set[int]:
    return {r["doc_id"] for r in conn.execute(
        "SELECT doc_id FROM archive_documents WHERE account_id = ?", (account_id,))}


def _record(conn, doc: dict, account_id: int, result: str, note: str,
            import_id: int | None = None) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO archive_documents (doc_id, account_id, title, created, "
        "seen_at, result, note, import_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (doc["id"], account_id, (doc.get("title") or "")[:200], (doc.get("created") or "")[:10],
         datetime.now(timezone.utc).isoformat(timespec="seconds"), result, note[:500], import_id))


def read_document(content: bytes, name: str, ocr_text: str | None, account_id: int,
                  currency: str) -> tuple[dict | None, str]:
    """One document through the readers: (store report, label) or (None, why).

    The original first — it is what an upload would be. Then, for a PDF
    the readers did not know, Paperless's OCR text through the PDF
    readers, which is the scanned-paper case."""
    module = importers.sniff(content)
    if module is None and ocr_text and content.startswith(b"%PDF"):
        for candidate in importers.PDF_IMPORTERS:
            try:
                if candidate.matches([], ocr_text):
                    module = candidate
                    content = ocr_text            # the readers take text too
                    break
            except Exception:                       # noqa: BLE001
                continue
    if module is None:
        return None, "not recognised"
    if isinstance(module, importers.generic.Mapped):
        parsed = module.parse(content, account_currency=currency, account_id=account_id)
    else:
        parsed = module.parse(content, account_currency=currency)
    if not parsed.rows and parsed.problems:
        return None, parsed.problems[0]
    import_id = importers.begin_import(account_id, name, module.SLUG)
    report = importers.store(account_id, parsed, module.SLUG, import_id)
    report["import_id"] = import_id
    return report, module.LABEL


def pull(account_id: int | None = None, transport=None) -> list[dict]:
    """Every account with a filter — or one — against the archive.

    One result per account: what was listed, what was new, what came
    in, what could not be read, and an error if the listing itself
    failed. A document that fails is recorded and the next one is tried;
    a listing that fails stops that account and moves on to the next.
    """
    api = client(transport)
    out = []
    for f in filters():
        if account_id is not None and f["account_id"] != account_id:
            continue
        res = {"account": f["account"], "account_id": f["account_id"], "listed": 0,
               "new": 0, "imported": 0, "inserted": 0, "unread": 0, "failed": 0, "error": None}
        try:
            docs = api.documents(f)
        except ArchiveError as exc:
            res["error"] = str(exc)
            out.append(res)
            continue
        res["listed"] = len(docs)
        with get_conn() as conn:
            seen = _seen(conn, f["account_id"])
        for doc in docs:
            if doc["id"] in seen:
                continue
            res["new"] += 1
            try:
                content, name = api.download(doc["id"])
                ocr = None
                if content.startswith(b"%PDF") and importers.sniff(content) is None:
                    ocr = api.content(doc["id"])
                report, label = read_document(content, name, ocr, f["account_id"], f["currency"])
            except ArchiveError as exc:
                res["failed"] += 1
                with get_conn() as conn:
                    _record(conn, doc, f["account_id"], "failed", str(exc))
                continue
            except Exception as exc:                  # noqa: BLE001
                res["failed"] += 1
                with get_conn() as conn:
                    _record(conn, doc, f["account_id"], "failed", f"{type(exc).__name__}: {exc}")
                continue
            with get_conn() as conn:
                if report is None:
                    res["unread"] += 1
                    _record(conn, doc, f["account_id"], "unread", label)
                else:
                    res["imported"] += 1
                    res["inserted"] += report["inserted"]
                    _record(conn, doc, f["account_id"], "imported",
                            f"{label}: {report['inserted']} new, {report['duplicates']} already had",
                            report.get("import_id"))
        out.append(res)
    set_state("archive_last_pull", json.dumps({
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "results": out}))
    return out


def retry_unread(account_id: int | None = None) -> int:
    """Forget the documents no reader understood, so the next pull
    tries them again — the thing to press after a new reader ships."""
    with get_conn() as conn:
        if account_id is None:
            cur = conn.execute("DELETE FROM archive_documents WHERE result IN ('unread', 'failed')")
        else:
            cur = conn.execute("DELETE FROM archive_documents WHERE result IN ('unread', 'failed') "
                               "AND account_id = ?", (account_id,))
        return cur.rowcount


def describe() -> dict:
    """For the Settings page: set-up, the filters with their tallies,
    the last pull, and the documents that could not be read."""
    with get_conn() as conn:
        tallies: dict[int, dict] = {}
        for r in conn.execute("SELECT account_id, result, COUNT(*) AS n FROM archive_documents "
                              "GROUP BY account_id, result"):
            tallies.setdefault(r["account_id"], {})[r["result"]] = r["n"]
        unread = [dict(r) for r in conn.execute(
            "SELECT d.*, a.name AS account FROM archive_documents d "
            "JOIN accounts a ON a.id = d.account_id "
            "WHERE d.result IN ('unread', 'failed') ORDER BY d.seen_at DESC LIMIT 25")]
    try:
        last = json.loads(get_state("archive_last_pull") or "null")
    except (ValueError, TypeError):
        last = None
    return {"configured": configured(), "url": url(),
            "filters": [{**f, **tallies.get(f["account_id"], {})} for f in filters()],
            "unread": unread, "last": last}


def document_url(doc_id: int) -> str:
    return f"{url()}/documents/{doc_id}/details"
