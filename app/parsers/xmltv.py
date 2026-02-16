import gzip, io
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional, Iterator
from lxml import etree

@dataclass
class Programme:
    tvg_id: str
    start_utc: str
    stop_utc: str
    title: Optional[str]
    desc: Optional[str]

def _xmltv_to_utc_iso(dt_str: str) -> str:
    s = dt_str.strip()
    if " " in s:
        main, tz = s.split(" ", 1)
        s = main + tz
    main = s[:14]
    tz = s[14:19] if len(s) >= 19 and s[14] in "+-" else None
    dt_naive = datetime.strptime(main, "%Y%m%d%H%M%S")
    if tz:
        sign = 1 if tz[0] == "+" else -1
        offset_minutes = sign * (int(tz[1:3]) * 60 + int(tz[3:5]))
        dt_utc = dt_naive.replace(tzinfo=timezone.utc) - timedelta(minutes=offset_minutes)
    else:
        dt_utc = dt_naive.replace(tzinfo=timezone.utc)
    return dt_utc.isoformat().replace("+00:00", "Z")

def load_xmltv_from_path(path: str) -> bytes:
    with open(path, "rb") as f:
        data = f.read()
    if data[:2] == b"\x1f\x8b":
        return gzip.decompress(data)
    return data

def iter_programmes_from_bytes(xml_bytes: bytes) -> Iterator[Programme]:
    context = etree.iterparse(io.BytesIO(xml_bytes), events=("end",), tag="programme", recover=True, huge_tree=True)
    for _event, elem in context:
        try:
            tvg_id = elem.get("channel") or ""
            start = elem.get("start") or ""
            stop = elem.get("stop") or ""
            title_el = elem.find("title")
            desc_el = elem.find("desc")
            title = title_el.text.strip() if (title_el is not None and title_el.text) else None
            desc = desc_el.text.strip() if (desc_el is not None and desc_el.text) else None
            if tvg_id and start and stop:
                yield Programme(tvg_id=tvg_id, start_utc=_xmltv_to_utc_iso(start), stop_utc=_xmltv_to_utc_iso(stop), title=title, desc=desc)
        finally:
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
