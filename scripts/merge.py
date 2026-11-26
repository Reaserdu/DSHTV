#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并上游公开 TVBox 源 + 本地网盘配置，生成 config.json / movie-only.json / pan-only.json。

用法：
  python scripts/merge.py            # 拉取上游在线源
  python scripts/merge.py --offline  # 仅用 data/sources_snapshot.json（离线）
"""
import argparse, json, os, ssl, urllib.request, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SNAPSHOT = DATA / "sources_snapshot.json"
PAN_LOCAL = ROOT.parent / "winbox_pan_config.json"   # 之前生成的网盘配置
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# 上游公开源（按优先级）。official 为 TVboxorg 每日探测的可用聚合。
UPSTREAM = [
    "https://raw.githubusercontent.com/TVboxorg/TVbox/main/dist/official.json",
    "https://cdn.jsdelivr.net/gh/TVboxorg/TVbox@main/dist/official.json",
    "https://raw.githubusercontent.com/25175/tvyuan/master/tvbox.json",
    "https://d.kstore.dev/download/9280/wex.json",
]

HEAD = {"User-Agent": "Mozilla/5.0"}


def fetch_json(url, timeout=20):
    req = urllib.request.Request(url, headers=HEAD)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        raw = r.read()
    for enc in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return json.loads(raw.decode(enc))
        except Exception:
            pass
    return json.loads(raw.decode("utf-8", "ignore"))


def dedup(items, key="key"):
    seen, out = set(), []
    for it in items:
        k = str(it.get(key, "")).strip()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out


def load_upstream(offline=False):
    blobs = []
    if offline and SNAPSHOT.exists():
        return json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    for u in UPSTREAM:
        try:
            d = fetch_json(u)
            blobs.append(d)
            print("拉取成功:", u)
        except Exception as e:
            print("跳过:", u, str(e)[:80])
    if not blobs and SNAPSHOT.exists():
        print("在线源全部失败，使用快照")
        return json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    # 缓存快照
    DATA.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(blobs, ensure_ascii=False), encoding="utf-8")
    return blobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()

    blobs = load_upstream(args.offline)
    if blobs and isinstance(blobs, list) and len(blobs) == 1 and "sites" in blobs[0]:
        blobs = blobs  # snapshot of one config
    elif isinstance(blobs, dict):
        blobs = [blobs]

    movie_sites, parses, lives = [], [], []
    spider, doh, flags, rules, hosts = None, [], [], [], []
    for d in blobs:
        if not isinstance(d, dict):
            continue
        spider = spider or d.get("spider")
        movie_sites += d.get("sites", [])
        parses += d.get("parses", [])
        lives += d.get("lives", [])
        doh += d.get("doh", [])
        flags += d.get("flags", [])
        rules += d.get("rules", [])
        hosts += d.get("hosts", [])

    movie_sites = dedup(movie_sites)
    parses = dedup(parses, "name")
    lives = dedup(lives, "name")

    # 网盘站点
    pan_sites = []
    if PAN_LOCAL.exists():
        pan = json.loads(PAN_LOCAL.read_text(encoding="utf-8"))
        pan_sites = [s for s in pan.get("sites", [])]
        parses = dedup(parses + pan.get("parses", []), "name")

    common = {
        "spider": spider or "",
        "parses": parses,
        "doh": doh,
        "flags": dedup(flags, "name") if flags and isinstance(flags[0], dict) else list(dict.fromkeys(flags)),
        "rules": rules,
        "hosts": list(dict.fromkeys(hosts)),
    }

    def dump(name, sites, extra=None):
        obj = dict(common)
        obj["sites"] = sites
        if extra:
            obj.update(extra)
        (ROOT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"生成 {name}: sites={len(sites)}")

    dump("movie-only.json", movie_sites, {"lives": lives})
    dump("pan-only.json", pan_sites)
    dump("config.json", dedup(movie_sites + pan_sites), {"lives": lives})


if __name__ == "__main__":
    main()
