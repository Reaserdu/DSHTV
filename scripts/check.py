# -*- coding: utf-8 -*-
"""校验生成的订阅 JSON。"""
import json, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
for name in ["config.json", "movie-only.json", "pan-only.json"]:
    p = ROOT / name
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        sites = d.get("sites", [])
        types = {}
        for s in sites:
            types[s.get("type")] = types.get(s.get("type"), 0) + 1
        print(f"OK {name}: {len(sites)} sites, {len(d.get('parses',[]))} parses, {len(d.get('lives',[]))} lives, types={types}, spider={'有' if d.get('spider') else '无'}")
    except Exception as e:
        print(f"FAIL {name}: {e}")
