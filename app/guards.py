"""Deterministic guards that must not depend on an LLM: stated-age (minor) detection, limitation
arithmetic, case-law request detection, reply-script check and source-caution notes."""
import os
import re
import unicodedata
from datetime import date, timedelta

_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def norm(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def today() -> date:
    v = os.environ.get("AI_LAWYER_TODAY", "").strip()
    return date.fromisoformat(v) if v else date.today()


# ------------------------------------------------------------------ 1. minors
_UNITS_AFTER = (r"(?!\s*(?:days?|months?|weeks?|years?|yrs?|hours?|rupees?|rs\b|%|lakh|k\b|times|km|kg|per\b|"
                r"percent|thousand|crore|din|mahine|saal|hafte))")
MINOR_PATTERNS = [
    re.compile(r"\b(\d{1,2})\s*[- ]?\s*(?:years?|yrs?)[- ]?\s*old\b"),
    re.compile(r"\b(\d{1,2})\s*(?:yo|y/o)\b"),
    re.compile(r"\b(?:i\s*am|i['’]m|im|my\s+age\s+is|age\s+is|aged|age)\s*:?\s*(\d{1,2})\b" + _UNITS_AFTER),
    re.compile(r"\b(?:meri\s+)?(?:umar|umr)\s*(?:hai\s*)?:?\s*(\d{1,2})\b"),
    re.compile(r"\b(\d{1,2})\s*(?:saal|sal|varsh|year)\s*(?:ka|ki)\s*(?:hu+n?|hoon|hun|hu|hai|tha|thi)\b"),
    # Hindi: "16 साल का/की" only when it ends the phrase ("5 साल का किराया" = rent of 5 years: no flag)
    re.compile(r"(?<!\d)(\d{1,2})\s*(?:साल|वर्ष|बरस)\s*(?:का|की)(?=\s*(?:हूँ|हूं|हु|है|था|थी|[.,!?।]|$))"),
    re.compile(r"उम्र\s*(?:है\s*)?:?\s*(\d{1,2})(?!\d)"),
]


def minor_flags(text: str) -> list[str]:
    """['minor_age'] if the user states an age under 18, else []."""
    t = norm(text).translate(_DEV_DIGITS).lower()
    for rx in MINOR_PATTERNS:
        for m in rx.finditer(t):
            if 1 <= int(m.group(1)) <= 17:
                return ["minor_age"]
    return []


# ------------------------------------------------------------------ 3. limitation arithmetic
_MONTHS = {m: i for i, m in enumerate(
    "january february march april may june july august september october november december".split(), 1)}
_MONTHS.update({k[:3]: v for k, v in list(_MONTHS.items())})
_MONTHS["sept"] = 9
_NUMW = {"one": 1, "a": 1, "an": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
         "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}


def parse_event_date(s) -> str | None:
    """Normalise an LLM- or user-given date to 'YYYY-MM-DD' or 'YYYY-MM' (or 'YYYY' -> 'YYYY-01'). None if unparsable."""
    if not isinstance(s, str):
        return None
    t = s.strip().lower()
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", t)
    if m:
        try:
            return date(int(m[1]), int(m[2]), int(m[3])).isoformat()
        except ValueError:
            return None
    m = re.match(r"^(\d{4})-(\d{1,2})$", t)
    if m and 1 <= int(m[2]) <= 12:
        return f"{m[1]}-{int(m[2]):02d}"
    m = re.match(r"^([a-z]{3,9})\.?,?\s+(\d{4})$", t) or re.match(r"^(\d{4})\s+([a-z]{3,9})$", t)
    if m:
        a, b = m.groups()
        mon, yr = (a, b) if a.isalpha() else (b, a)
        if mon in _MONTHS:
            return f"{yr}-{_MONTHS[mon]:02d}"
    if re.match(r"^\d{4}$", t):
        return f"{t}-01"
    return None


def months_since(event_date, today_: date | None = None) -> float | None:
    """Months between event_date and today, computed in code. None if the date cannot be parsed."""
    p = parse_event_date(event_date)
    if not p:
        return None
    td = today_ or today()
    parts = [int(x) for x in p.split("-")]
    y, mo = parts[0], parts[1]
    d = parts[2] if len(parts) == 3 else 1
    months = (td.year - y) * 12 + (td.month - mo) + (td.day - d) / 30.0
    return round(max(months, 0.0), 1)


def _sub_months(d: date, n: int) -> date:
    y, m = divmod(d.year * 12 + d.month - 1 - n, 12)
    m += 1
    day = min(d.day, [31, 29 if y % 4 == 0 and (y % 100 or y % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    return date(y, m, day)


_REL = re.compile(r"\b(\d{1,3}|one|a|an|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
                  r"(day|week|month|year)s?\s+(?:ago|back)\b")
_REL_HI = re.compile(r"(\d{1,3})\s*(दिन|हफ्ते|हफ़्ते|सप्ताह|महीने|महीना|माह|साल|वर्ष)\s*(?:पहले|पहले से)")
_REL_RO = re.compile(r"\b(\d{1,3})\s*(din|hafte|mahine|mahina|saal|sal)\s*(?:pehle|pahle)\b")


def relative_event_date(text: str, today_: date | None = None) -> str | None:
    """'2 months ago' / '3 साल पहले' / '3 saal pehle' -> ISO date, computed in code."""
    td = today_ or today()
    t = norm(text).translate(_DEV_DIGITS).lower()
    n = unit = None
    m = _REL.search(t)
    if m:
        n = int(m[1]) if m[1].isdigit() else _NUMW[m[1]]
        unit = m[2]
    else:
        m = _REL_HI.search(t) or _REL_RO.search(t)
        if m:
            n = int(m[1])
            u = m[2]
            unit = ("day" if u in ("दिन", "din") else "week" if u in ("हफ्ते", "हफ़्ते", "सप्ताह", "hafte")
                    else "year" if u in ("साल", "वर्ष", "saal", "sal") else "month")
    if n is None:
        return None
    if unit == "day":
        return (td - timedelta(days=n)).isoformat()
    if unit == "week":
        return (td - timedelta(weeks=n)).isoformat()
    return _sub_months(td, n * (12 if unit == "year" else 1)).isoformat()


# ------------------------------------------------------------------ 4. case-law requests
_CASE_EN = re.compile(
    r"\b(case\s*law|judge?ments?|precedents?|supreme\s+court|landmark\s+(?:case|judge?ment)|"
    r"(?:similar|previous|past|any|famous)\s+cases?|court\s+(?:ruling|decision|held)|rulings?|verdicts?|"
    r"faisla|faisle|nazir|misal)\b", re.I)
_CASE_HI = ["फैसला", "फैसले", "फ़ैसला", "फ़ैसले", "मिसाल", "नज़ीर", "नजीर", "सुप्रीम कोर्ट", "केस लॉ", "पुराने केस",
            "पुराना केस", "पहले के केस", "ऐसा कोई केस", "कोई केस"]


def case_law_request(text: str) -> bool:
    t = norm(text)
    return bool(_CASE_EN.search(t)) or any(norm(k) in t for k in _CASE_HI)


# ------------------------------------------------------------------ 5. reply script
def script_ok(text: str, lang: str, min_share: float = 0.5) -> bool:
    """Hindi replies must be mostly Devanagari (not English / Roman Hindi); English replies mostly Latin."""
    dev = sum(1 for c in text if "ऀ" <= c <= "ॿ")
    lat = sum(1 for c in text if c.isascii() and c.isalpha())
    if dev + lat < 20:
        return True
    if lang.lower().startswith("hi"):
        return dev / (dev + lat) >= min_share
    if lang.lower().startswith("en"):
        return lat / (dev + lat) >= min_share
    return True


# ------------------------------------------------------------------ 6. source caution (UI panel)
CAUTION = "(unverified source – check before relying on it)"


def source_notes(chunk: dict) -> list[str]:
    """Lines for the 'How I got this answer' panel: source_type, REVIEW note, secondary caution."""
    notes = [f"source type: {chunk.get('source_type', 'unknown')}"]
    sn = chunk.get("status_note") or ""
    if "REVIEW" in sn:
        notes.append(sn)
    if chunk.get("source_type") == "secondary":
        notes.append(CAUTION)
    return notes
