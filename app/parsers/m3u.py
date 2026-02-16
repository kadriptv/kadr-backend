import re
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

_attr_re = re.compile(r'(\w+(?:-\w+)*)="([^"]*)"')

@dataclass
class Channel:
    tvg_id: str
    name: str
    tvg_name: Optional[str]
    logo: Optional[str]
    grp: Optional[str]
    stream_url: str
    raw_extinf: str

def extract_epg_url(m3u_text: str) -> Optional[str]:
    for line in m3u_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#EXTM3U"):
            attrs = dict(_attr_re.findall(line))
            return attrs.get("url-tvg") or attrs.get("x-tvg-url")
        break
    return None

def _parse_extinf_attrs(extinf_line: str) -> Tuple[Dict[str, str], str]:
    attrs = dict(_attr_re.findall(extinf_line))
    display_name = ""
    if "," in extinf_line:
        display_name = extinf_line.split(",", 1)[1].strip()
    return attrs, display_name

def parse_m3u(m3u_text: str) -> List[Channel]:
    lines = [ln.rstrip("\r") for ln in m3u_text.splitlines()]
    channels: List[Channel] = []
    pending_extinf = None
    pending_attrs = None
    pending_name = None
    pending_grp = None

    def clean(s):
        if s is None: return None
        s = s.strip()
        return s if s else None

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        if line.startswith("#EXTINF"):
            pending_extinf = line
            attrs, disp = _parse_extinf_attrs(line)
            pending_attrs = attrs
            pending_name = disp or attrs.get("tvg-name") or attrs.get("tvg-id") or "Channel"
            if "group-title" in attrs:
                pending_grp = attrs.get("group-title")
            continue

        if line.startswith("#EXTGRP:"):
            pending_grp = line.split(":", 1)[1].strip() or pending_grp
            continue

        if line.startswith("#"):
            continue

        if pending_extinf and pending_attrs:
            tvg_id = pending_attrs.get("tvg-id") or pending_attrs.get("tvgid") or pending_attrs.get("tvg_id")
            tvg_id = (tvg_id or (pending_attrs.get("tvg-name") or pending_name or "unknown")).strip()
            channels.append(Channel(
                tvg_id=tvg_id,
                name=(pending_name or tvg_id).strip(),
                tvg_name=clean(pending_attrs.get("tvg-name")),
                logo=clean(pending_attrs.get("tvg-logo")),
                grp=clean(pending_grp),
                stream_url=line,
                raw_extinf=pending_extinf
            ))

        pending_extinf = None
        pending_attrs = None
        pending_name = None
        pending_grp = None

    return channels
