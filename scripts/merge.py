#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并上游公开 TVBox 源 + 本地网盘配置，生成 config.json / movie-only.json / pan-only.json。

用法：
  python scripts/merge.py            # 拉取上游在线源
  python scripts/merge.py --offline  # 仅用 data/sources_snapshot.json（离线）

三份输出的含义：
  config.json      全量：影视采集站 + 网盘配置中心 + 解析
  movie-only.json  只有影视采集站（不含网盘配置中心）
  pan-only.json    只有网盘配置中心（扫码登录）
"""
import argparse, json, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SNAPSHOT = DATA / "sources_snapshot.json"
# 本地网盘配置（可选）：优先读仓库内 data/winbox_pan_config.json，
# 兼容旧位置（仓库父目录）。该文件只在本地生效，不提交进仓库。
PAN_LOCAL = DATA / "winbox_pan_config.json"
PAN_LOCAL_LEGACY = ROOT.parent / "winbox_pan_config.json"

# 上游公开源（按优先级）。official 为 TVboxorg 每日探测的可用聚合。
# raw 与 jsdelivr 是同一份 official.json 的两个入口，都会拉取，
# 去重逻辑保证结果一致。
UPSTREAM = [
    "https://raw.githubusercontent.com/TVboxorg/TVbox/main/dist/official.json",
    "https://cdn.jsdelivr.net/gh/TVboxorg/TVbox@main/dist/official.json",
    "https://raw.githubusercontent.com/25175/tvyuan/master/tvbox.json",
    "https://d.kstore.dev/download/9280/wex.json",
]

# 网盘配置中心类站点的 api 标识
CONFIG_APIS = ("csp_Config", "csp_PanConfig", "csp_PanConfigGuard")

HEAD = {"User-Agent": "Mozilla/5.0"}


def fetch_json(url, timeout=20):
    req = urllib.request.Request(url, headers=HEAD)
    with urllib.request.urlopen(req, timeout=timeout) as r:
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


def dedup_values(items):
    """对 doh / rules 这类字符串或字典混合列表去重（保持首次出现顺序）。"""
    seen, out = set(), []
    for it in items:
        k = json.dumps(it, sort_keys=True, ensure_ascii=False) if isinstance(it, (dict, list)) else str(it)
        if k in seen:
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
    if isinstance(blobs, dict):
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
    doh = dedup_values(doh)
    rules = dedup_values(rules)

    # 网盘处理（XiugouTV / FongMi / CatVod 内核）
    # XiugouTV 用内置 Pan spider + PanConfig 配置中心；不认 csp_PanAli/csp_PanQuark
    # 等独立网盘类，加进去只会 Fallback to SpiderNull。网盘授权在软件内
    # “配置中心”扫码，需要开启 GO 代理才能播放网盘线路。
    CENTER = {"key": "配置中心", "name": "网盘配置中心 | 扫码登录", "type": 3, "api": "csp_Config",
              "searchable": 0, "filterable": 0, "changeable": 0}

    # 上游自带的配置中心站点从影视列表里拆出来归入网盘侧：
    # movie-only 不含网盘入口，pan-only 也不再为空；上游没有时补一个默认配置中心。
    center_sites = [s for s in movie_sites if s.get("api") in CONFIG_APIS]
    movie_only_sites = [s for s in movie_sites if s.get("api") not in CONFIG_APIS]
    pan_sites = center_sites if center_sites else [dict(CENTER)]

    pan_local = PAN_LOCAL if PAN_LOCAL.exists() else PAN_LOCAL_LEGACY
    if pan_local.exists():
        pan = json.loads(pan_local.read_text(encoding="utf-8"))
        parses = dedup(parses + pan.get("parses", []), "name")

    common = {
        "spider": spider or "",
        "parses": parses,
        "doh": doh,
        "flags": dedup(flags, "name") if flags and isinstance(flags[0], dict) else list(dict.fromkeys(flags)),
        "rules": rules,
        "hosts": list(dict.fromkeys(hosts)),
    }

    note = "网盘由客户端内置 Pan spider 提供；在软件『配置中心』扫码登录，并开启 GO 代理后即可播放网盘线路"

    (ROOT / "movie-only.json").write_text(
        json.dumps({**common, "sites": movie_only_sites, "lives": lives}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"生成 movie-only.json: sites={len(movie_only_sites)}")

    all_sites = dedup(movie_only_sites + pan_sites)
    (ROOT / "config.json").write_text(
        json.dumps({**common, "sites": all_sites, "lives": lives, "_pan_note": note}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"生成 config.json: sites={len(all_sites)}")

    (ROOT / "pan-only.json").write_text(
        json.dumps({**common, "sites": pan_sites, "_pan_note": note}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"生成 pan-only.json: sites={len(pan_sites)} (仅配置中心)")


if __name__ == "__main__":
    main()
