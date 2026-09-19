"""The weekly e-mail: what the week did, from the app's own figures.

Once a week, on a day of your choosing, a mail with the net worth and
its seven-day change, then every broker and crypto account with its
value, the week's price move, the gain since purchase, the holdings
with their own week, the dividends of the last thirty days and the
trailing twelve months — and the indices the app already tracks, so
"up 1.2 %" sits beside what the market did.

Two rules carried over from the pages.

**A week's move is the price effect only.** Quantity now × (price now −
price a week ago), in the holding's own currency: a top-up during the
week is not a gain and a sale is not a loss. The net worth line at the
top does include flows — it is the balance, and a balance moves when
money arrives — which is why the account sections say *price move* and
the headline says *change*.

**Nothing is re-priced for the mail.** The figures are the ones the
pages show: today's from the overview, the earlier ones from the same
records the net-worth line is drawn from. A holding with no market
price a week ago has no move, and says so with a dash.

The mail is the one thing this app sends anywhere but your own bank:
to your mailbox, through the SMTP server you name. The password is
kept beside the bank key, 0600, and the recipient list stays in
settings.json on your machine.
"""

from __future__ import annotations

import smtplib
import ssl
from datetime import date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

from . import benchmark, fx, history, i18n, overview, settings
from .db import get_conn, get_state, set_state

DEFAULT_TYPES = ("broker", "crypto")
RECENT_DAYS = 30
PASSWORD_FILE = "smtp_password"
STATE_KEY = "report_last_week"
STATE_LOG = "report_last_sent"


def lang() -> str:
    """The app's configured language; English when none is set. A mail
    has no browser to ask."""
    return i18n.resolve(settings.get("language"), None)


def _t(text: str) -> str:
    return i18n.translate(text, lang())


def _f(text: str, **values) -> str:
    return i18n.fill(text, lang(), **values)


def _n(count: int, one: str, many: str, **values) -> str:
    return i18n.plural(count, one, many, lang(), **values)


# ─── Building ────────────────────────────────────────────────────────

def _conv(amount: float | None, frm: str, to: str, when: str | None = None) -> float | None:
    if amount is None:
        return None
    return fx.convert(amount, frm, to, when)[0]


def _price_on(conn, isin: str, day: str) -> tuple[float, str] | None:
    r = conn.execute("SELECT price, currency FROM prices WHERE isin = ? AND as_of <= ? "
                     "ORDER BY as_of DESC LIMIT 1", (isin, day)).fetchone()
    return (r["price"], r["currency"]) if r else None


def account_section(acct: dict, base: str, today: str, since: str) -> dict | None:
    """One account's block, in the account's own currency. None when
    the account holds nothing the pages can value."""
    ccy = acct["currency"].upper()
    s = overview.summary(base, account_ids=[acct["id"]])
    holdings = []
    value = 0.0
    with get_conn() as conn:
        for h in s["holdings"]:
            own = (h["currency"] or base).upper()
            if h.get("value") is None:
                continue
            v = _conv(h["value"], own, ccy, today)
            if v is None:
                continue
            value += v
            change = pct = None
            if h.get("price_kind") == "market" and h.get("price") is not None:
                then = _price_on(conn, h["isin"], since)
                if then:
                    p_then = _conv(then[0], then[1], own, since)
                    if p_then:
                        delta = h["quantity"] * (h["price"] - p_then)
                        change = _conv(delta, own, ccy, today)
                        pct = h["price"] / p_then - 1.0
            cost = h.get("net_invested")
            gain = None
            if cost and cost > 0:
                gain = _conv(h["value"] - cost, own, ccy, today)
            holdings.append({
                "name": h["name"] or h["isin"], "isin": h["isin"],
                "price": h.get("price"), "price_currency": own,
                "value": v, "change_7d": change, "pct_7d": pct,
                "gain": gain, "cost": _conv(cost, own, ccy, today) if cost and cost > 0 else None,
            })
        # Dividends of the trailing year, in the account's currency at
        # the day they were paid; the ones with no rate on file listed
        # beside the total rather than counted as nothing.
        since_12m = (date.fromisoformat(today) - timedelta(days=365)).isoformat()
        since_recent = (date.fromisoformat(today) - timedelta(days=RECENT_DAYS)).isoformat()
        div_12m = 0.0
        recent = []
        unconverted: dict[str, float] = {}
        for r in conn.execute(
                "SELECT txn_date, amount, currency, security_name, description "
                "FROM transactions WHERE account_id = ? AND kind = 'dividend' "
                "AND txn_date > ? AND txn_date <= ? ORDER BY txn_date DESC",
                (acct["id"], since_12m, today)):
            amt = _conv(r["amount"], r["currency"] or ccy, ccy, r["txn_date"])
            if amt is None:
                unconverted[r["currency"]] = unconverted.get(r["currency"], 0.0) + r["amount"]
                continue
            div_12m += amt
            if r["txn_date"] > since_recent:
                recent.append({"date": r["txn_date"],
                               "name": r["security_name"] or r["description"] or _t("Dividend"),
                               "amount": amt})
    cash = _conv(s["cash"], base, ccy, today) if s["cash"] else 0.0
    if not holdings and not cash:
        return None
    holdings.sort(key=lambda h: -h["value"])
    moved = [h for h in holdings if h["change_7d"] is not None]
    change_7d = sum(h["change_7d"] for h in moved) if moved else None
    before = sum(h["value"] - h["change_7d"] for h in moved)
    costed = [h for h in holdings if h["gain"] is not None]
    cost = sum(h["cost"] for h in costed)
    total = value + (cash or 0.0)
    return {
        "id": acct["id"], "name": acct["name"], "currency": ccy,
        "value": total, "cash": cash or 0.0,
        "value_base": _conv(total, ccy, base, today),
        "change_7d": change_7d, "pct_7d": (change_7d / before) if moved and before else None,
        "gain": sum(h["gain"] for h in costed) if costed else None,
        "gain_pct": (sum(h["gain"] for h in costed) / cost) if costed and cost else None,
        "holdings": holdings,
        "dividends_recent": recent, "dividends_12m": div_12m,
        "dividend_yield": (div_12m / total) if total else None,
        "dividends_unconverted": unconverted,
    }


def benchmarks(today: str, since: str) -> list[dict]:
    """The indices whose closes the app already keeps — the ones the
    Performance page has been asked about."""
    labels = {sym: name for name, sym, _ccy in benchmark.BENCHMARKS.values()}
    out = []
    with get_conn() as conn:
        symbols = [r["isin"][len(benchmark.PREFIX):] for r in conn.execute(
            "SELECT DISTINCT isin FROM prices WHERE isin LIKE ? ORDER BY isin",
            (benchmark.PREFIX + "%",))]
        for sym in symbols:
            now = _price_on(conn, benchmark.PREFIX + sym, today)
            then = _price_on(conn, benchmark.PREFIX + sym, since)
            if not now:
                continue
            out.append({"label": labels.get(sym, sym), "price": now[0], "currency": now[1],
                        "change_7d": (now[0] - then[0]) if then else None,
                        "pct_7d": (now[0] / then[0] - 1) if then and then[0] else None})
    return out


def build(base: str = "EUR", today: date | None = None,
          account_types=DEFAULT_TYPES) -> dict:
    today = today or date.today()
    since = today - timedelta(days=7)
    t, s = today.isoformat(), since.isoformat()
    now = overview.summary(base)
    then = history.net_worth_on(since, base)
    with get_conn() as conn:
        marks = ",".join("?" * len(account_types))
        accounts = [dict(r) for r in conn.execute(
            f"SELECT id, name, type, currency FROM accounts WHERE type IN ({marks}) "
            f"ORDER BY name", tuple(account_types))]
    sections = [sec for sec in (account_section(a, base, t, s) for a in accounts) if sec]
    sections.sort(key=lambda x: -(x["value_base"] or 0))
    nw = now["net_worth"]
    return {
        "as_of": t, "since": s, "base": base.upper(),
        "net_worth": nw, "net_worth_then": then,
        "net_worth_change": (nw - then) if then is not None else None,
        "net_worth_pct": (nw / then - 1) if then else None,
        "accounts_total": sum(x["value_base"] or 0 for x in sections),
        "accounts": sections,
        "benchmarks": benchmarks(t, s),
    }


# ─── Rendering ───────────────────────────────────────────────────────

def money(v: float | None, ccy: str, signed: bool = False) -> str:
    if v is None:
        return "—"
    s = i18n.money(v, ccy, lang())
    return f"+{s}" if signed and v > 0 else s


def pct(v: float | None, signed: bool = True) -> str:
    if v is None:
        return "—"
    s = f"{v * 100:.2f}".replace(".", "," if lang() in ("de", "fr", "es") else ".")
    return f"{'+' if signed and v > 0 else ''}{s} %"


def _tone(v: float | None) -> str:
    if v is None or abs(v) < 1e-9:
        return "#6b7280"
    return "#15803d" if v > 0 else "#b91c1c"


def subject(rep: dict) -> str:
    tail = "" if rep["net_worth_change"] is None else \
        f" · {money(rep['net_worth_change'], rep['base'], signed=True)} ({pct(rep['net_worth_pct'])})"
    return _f("Weekly report {date}", date=i18n.fmt_date(rep["as_of"], lang())) + tail


def render_text(rep: dict) -> str:
    b = rep["base"]
    L = [_f("Weekly report — {since} to {date}", since=i18n.fmt_date(rep["since"], lang()),
            date=i18n.fmt_date(rep["as_of"], lang())), ""]
    L.append(f"{_t('Net worth')}: {money(rep['net_worth'], b)}   "
             f"7d {money(rep['net_worth_change'], b, signed=True)} ({pct(rep['net_worth_pct'])})")
    L.append("")
    for s in rep["accounts"]:
        c = s["currency"]
        L.append(f"== {s['name']}  {money(s['value'], c)}   7d {money(s['change_7d'], c, signed=True)} "
                 f"({pct(s['pct_7d'])})   {_t('since purchase')} {money(s['gain'], c, signed=True)} "
                 f"({pct(s['gain_pct'])})")
        for h in s["holdings"]:
            L.append(f"   {h['name'][:44]:44} {money(h['value'], c):>18}   "
                     f"7d {money(h['change_7d'], c, signed=True)} ({pct(h['pct_7d'])})")
        if s["cash"]:
            L.append(f"   {_t('Cash'):44} {money(s['cash'], c):>18}")
        L.append(f"   {_t('Dividends, 12 months')}: {money(s['dividends_12m'], c)}"
                 f"  {_t('yield')} {pct(s['dividend_yield'], signed=False)}")
        for d in s["dividends_recent"]:
            L.append(f"     {d['date']}  {d['name'][:40]:40} {money(d['amount'], c)}")
        L.append("")
    if rep["benchmarks"]:
        L.append(_t("Indices"))
        for x in rep["benchmarks"]:
            L.append(f"   {x['label']:40} {x['price']:,.2f} {x['currency']}   "
                     f"7d {pct(x['pct_7d'])}")
    return "\n".join(L)


def render_html(rep: dict) -> str:
    b = rep["base"]
    td = 'style="padding:6px 8px;border-bottom:1px solid #e5e7eb;font-size:13px"'
    tdr = td[:-1] + ';text-align:right;white-space:nowrap"'
    th = 'style="padding:6px 8px;border-bottom:2px solid #d1d5db;font-size:12px;text-align:left;color:#6b7280"'
    thr = th.replace("text-align:left", "text-align:right")
    muted = 'style="font-size:12px;color:#6b7280"'

    def move(v, p, ccy):
        return (f'<span style="color:{_tone(v)}">{escape(money(v, ccy, signed=True))}'
                f'<br><small>{escape(pct(p))}</small></span>')

    parts = [f'''<div style="font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;max-width:680px;margin:0 auto;color:#111827">
  <h1 style="font-size:20px;margin:16px 0 4px">{escape(_t("Weekly report"))}</h1>
  <div {muted}>{escape(_f("{since} to {date}", since=i18n.fmt_date(rep["since"], lang()), date=i18n.fmt_date(rep["as_of"], lang())))} · Wealth Dashboard</div>
  <table style="width:100%;border-collapse:collapse;margin:16px 0 20px">
    <tr><th {th}>{escape(_t("Overview"))}</th><th {thr}>{escape(_t("Value"))}</th><th {thr}>7d</th></tr>
    <tr><td {td}><b>{escape(_t("Net worth"))}</b></td><td {tdr}><b>{escape(money(rep["net_worth"], b))}</b></td>
        <td {tdr}>{move(rep["net_worth_change"], rep["net_worth_pct"], b)}</td></tr>
''']
    for s in rep["accounts"]:
        parts.append(f'    <tr><td {td}>{escape(s["name"])}</td><td {tdr}>{escape(money(s["value"], s["currency"]))}</td>'
                     f'<td {tdr}>{move(s["change_7d"], s["pct_7d"], s["currency"])}</td></tr>\n')
    parts.append("  </table>\n")
    if rep["benchmarks"]:
        parts.append(f'  <table style="width:100%;border-collapse:collapse;margin-bottom:24px">\n'
                     f'    <tr><th {th}>{escape(_t("Indices"))}</th><th {thr}>{escape(_t("Level"))}</th><th {thr}>7d</th></tr>\n')
        for x in rep["benchmarks"]:
            parts.append(f'    <tr><td {td}>{escape(x["label"])}</td><td {tdr}>{x["price"]:,.2f} {escape(x["currency"])}</td>'
                         f'<td {tdr}><span style="color:{_tone(x["pct_7d"])}">{escape(pct(x["pct_7d"]))}</span></td></tr>\n')
        parts.append("  </table>\n")
    for s in rep["accounts"]:
        c = s["currency"]
        parts.append(f'''
  <h2 style="font-size:17px;margin:24px 0 2px">{escape(s["name"])}</h2>
  <div style="font-size:22px;font-weight:700;margin-bottom:6px">{escape(money(s["value"], c))}</div>
  <table style="border-collapse:collapse;margin-bottom:10px">
    <tr><td style="padding:2px 24px 2px 0;font-size:12px;color:#6b7280">{escape(_t("Gain since purchase"))}</td>
        <td style="padding:2px 24px 2px 0;font-size:12px;color:#6b7280">{escape(_t("Price move, 7 days"))}</td>
        <td style="padding:2px 0;font-size:12px;color:#6b7280">{escape(_t("Dividends, 12 months"))}</td></tr>
    <tr><td style="padding:2px 24px 2px 0;font-size:14px;color:{_tone(s["gain"])}"><b>{escape(money(s["gain"], c, signed=True))}</b> {escape(pct(s["gain_pct"]))}</td>
        <td style="padding:2px 24px 2px 0;font-size:14px;color:{_tone(s["change_7d"])}"><b>{escape(money(s["change_7d"], c, signed=True))}</b> {escape(pct(s["pct_7d"]))}</td>
        <td style="padding:2px 0;font-size:14px"><b>{escape(money(s["dividends_12m"], c))}</b> <span style="color:#6b7280">{escape(_t("yield"))} {escape(pct(s["dividend_yield"], signed=False))}</span></td></tr>
  </table>
  <table style="width:100%;border-collapse:collapse">
    <tr><th {th}>{escape(_t("Holding"))}</th><th {thr}>{escape(_t("Price"))}</th><th {thr}>{escape(_t("Value"))}</th><th {thr}>7d</th></tr>
''')
        for h in s["holdings"]:
            price = "" if h["price"] is None else f"{h['price']:,.2f} {h['price_currency']}"
            parts.append(f'    <tr><td {td}>{escape(h["name"])}</td><td {tdr}>{escape(price)}</td>'
                         f'<td {tdr}>{escape(money(h["value"], c))}</td><td {tdr}>{move(h["change_7d"], h["pct_7d"], c)}</td></tr>\n')
        if s["cash"]:
            parts.append(f'    <tr><td {td}>{escape(_t("Cash"))}</td><td {tdr}></td>'
                         f'<td {tdr}>{escape(money(s["cash"], c))}</td><td {tdr}></td></tr>\n')
        parts.append("  </table>\n")
        if s["dividends_recent"]:
            parts.append(f'  <div {muted[:-1]};margin:10px 0 2px">{escape(_f("Dividends, last {n} days", n=RECENT_DAYS))}</div>\n'
                         '  <table style="width:100%;border-collapse:collapse">\n')
            for d in s["dividends_recent"]:
                parts.append(f'    <tr><td {td}>{escape(i18n.fmt_date(d["date"], lang()))}</td><td {td}>{escape(d["name"])}</td>'
                             f'<td {tdr}>{escape(money(d["amount"], c))}</td></tr>\n')
            parts.append("  </table>\n")
        else:
            parts.append(f'  <div {muted[:-1]};margin-top:8px">{escape(_f("No dividends in the last {n} days.", n=RECENT_DAYS))}</div>\n')
        if s["dividends_unconverted"]:
            parts.append(f'  <div {muted[:-1]};margin-top:4px">' + escape(_f(
                "Not in the dividend total, no rate on file: {amounts}",
                amounts=", ".join(f"{v:,.2f} {k}" for k, v in s["dividends_unconverted"].items()))) + "</div>\n")
    parts.append(f'''
  <div style="color:#9ca3af;font-size:11px;margin:28px 0 12px">
    {escape(_t("7d is the price move of what you hold now, in the account's currency — a deposit or a purchase during the week is not a gain. Gain since purchase compares today's value with what you put in. The net worth line at the top is the balance, and moves when money arrives too."))}
  </div>
</div>
''')
    return "".join(parts)


# ─── Sending ─────────────────────────────────────────────────────────

class NotConfigured(Exception):
    pass


def configured() -> bool:
    cfg = settings.load()
    return bool(cfg.get("smtp_host") and cfg.get("report_to")
                and (settings.SECRETS_DIR / PASSWORD_FILE).exists())


def save(form: dict) -> None:
    """The SMTP details in settings.json, the password beside the keys.
    A blank password keeps the saved one."""
    cfg = settings.load()
    host = (form.get("smtp_host") or "").strip()
    to = ", ".join(a.strip() for a in (form.get("report_to") or "").replace(";", ",").split(",") if a.strip())
    if form.get("report_enabled") and (not host or not to):
        raise ValueError("A server and at least one recipient are needed before the mail can go out.")
    try:
        port = int(form.get("smtp_port") or 587)
    except ValueError:
        raise ValueError("The port needs to be a number — 587 for STARTTLS, 465 for TLS.")
    cfg["smtp_host"], cfg["smtp_port"] = host, port
    cfg["smtp_user"] = (form.get("smtp_user") or "").strip()
    cfg["smtp_from"] = (form.get("smtp_from") or "").strip()
    cfg["report_to"] = to
    try:
        cfg["report_weekday"] = min(6, max(0, int(form.get("report_weekday") or 0)))
    except ValueError:
        cfg["report_weekday"] = 0
    cfg["report_enabled"] = bool(form.get("report_enabled"))
    settings.save(cfg)
    password = (form.get("smtp_password") or "").strip()
    if password:
        settings.ensure_dirs()
        path = settings.SECRETS_DIR / PASSWORD_FILE
        path.write_text(password)
        try:
            path.chmod(0o600)
        except OSError:
            pass


def forget() -> None:
    cfg = settings.load()
    for k in ("smtp_host", "smtp_port", "smtp_user", "smtp_from", "report_to",
              "report_weekday", "report_enabled"):
        cfg.pop(k, None)
    settings.save(cfg)
    try:
        (settings.SECRETS_DIR / PASSWORD_FILE).unlink()
    except FileNotFoundError:
        pass


def send(subject_line: str, html: str, text: str, smtp=None) -> list[str]:
    """One mail, both versions. `smtp` is the transport, for the tests;
    the real one is smtplib with STARTTLS, or implicit TLS on 465."""
    cfg = settings.load()
    host = cfg.get("smtp_host")
    to = [a.strip() for a in (cfg.get("report_to") or "").split(",") if a.strip()]
    try:
        password = (settings.SECRETS_DIR / PASSWORD_FILE).read_text().strip()
    except OSError:
        password = ""
    if not host or not to or not password:
        raise NotConfigured("The weekly e-mail is not set up — server, password and "
                            "recipient are needed under Settings.")
    port = int(cfg.get("smtp_port") or 587)
    user = cfg.get("smtp_user") or ""
    sender = cfg.get("smtp_from") or user or f"wealth-dashboard@{host}"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject_line
    msg["From"] = sender
    msg["To"] = ", ".join(to)
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    (smtp or _smtp_send)(host, port, user, password, sender, to, msg.as_string())
    return to


def _smtp_send(host, port, user, password, sender, to, body) -> None:
    ctx = ssl.create_default_context()
    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=ctx, timeout=30) as s:
            if user:
                s.login(user, password)
            s.sendmail(sender, to, body)
    else:
        with smtplib.SMTP(host, port, timeout=30) as s:
            s.ehlo()
            s.starttls(context=ctx)
            s.ehlo()
            if user:
                s.login(user, password)
            s.sendmail(sender, to, body)


def week_key(day: date) -> str:
    return day.strftime("%G-W%V")


def due(today: date, cfg: dict, last_week: str | None) -> bool:
    """Once a week: on the chosen weekday, and not twice in one ISO
    week — a day the machine slept through is caught up on the next,
    which is what once a week means."""
    if not cfg.get("report_enabled"):
        return False
    weekday = int(cfg.get("report_weekday") or 0)
    if last_week == week_key(today):
        return False
    # Due from the weekday on, for the rest of that week.
    return today.weekday() >= weekday


def send_report(base: str = "EUR", today: date | None = None, smtp=None) -> dict:
    today = today or date.today()
    rep = build(base, today)
    to = send(subject(rep), render_html(rep), render_text(rep), smtp)
    set_state(STATE_KEY, week_key(today))
    set_state(STATE_LOG, datetime.now().isoformat(timespec="seconds"))
    return {"to": to, "subject": subject(rep), "accounts": len(rep["accounts"])}


def send_if_due(base: str = "EUR", today: date | None = None, smtp=None) -> dict | None:
    today = today or date.today()
    if not due(today, settings.load(), get_state(STATE_KEY)):
        return None
    return send_report(base, today, smtp)


def describe() -> dict:
    cfg = settings.load()
    return {"configured": configured(), "enabled": bool(cfg.get("report_enabled")),
            "host": cfg.get("smtp_host") or "", "port": cfg.get("smtp_port") or 587,
            "user": cfg.get("smtp_user") or "", "sender": cfg.get("smtp_from") or "",
            "to": cfg.get("report_to") or "", "weekday": int(cfg.get("report_weekday") or 0),
            "last_sent": get_state(STATE_LOG), "last_week": get_state(STATE_KEY)}
