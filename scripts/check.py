# -*- coding: utf-8 -*-
"""校验生成的订阅 JSON。任一文件失败则以非零状态退出，供 CI 调用。"""
import json, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
failed = False
for name in ["config.json", "movie-only.json", "pan-only.json"]:
    p = ROOT / name
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        sites = d.get("sites", [])
        if not sites:
            raise ValueError("sites 为空")
        types = {}
        for s in sites:
            types[s.get("type")] = types.get(s.get("type"), 0) + 1
        print(f"OK {name}: {len(sites)} sites, {len(d.get('parses', []))} parses, {len(d.get('lives', []))} lives, types={types}, spider={'有' if d.get('spider') else '无'}")
    except Exception as e:
        failed = True
        print(f"FAIL {name}: {e}")
sys.exit(1 if failed else 0)
