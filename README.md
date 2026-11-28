# Zyfun / WIN-Box 订阅配置

自动聚合的 TVBox/影视仓配置，供 **Zyfun / WIN-Box**（Windows 版）及 TVBox 系播放器使用。

## 订阅地址（仓库建好并推送后可用）

```
https://raw.githubusercontent.com/Reaserdu/DSHTV/main/config.json
```

国内加速：

```
https://cdn.jsdelivr.net/gh/Reaserdu/DSHTV@main/config.json
```

## 配置文件

| 文件 | 用途 | 复制到一个播放器用哪个 |
|---|---|---|
| `config.json` | 影视采集站 + 网盘配置中心 + 解析，全量合一 | ✅ 日常用这个 |
| `pan-only.json` | 只有网盘配置中心（扫码登录，无影视资源） | 只想挂载自己网盘时用 |
| `movie-only.json` | 只有影视采集站（不含网盘配置中心） | 只要免费影视时用 |

> 网盘源本身不含影视内容，只能列出你自己网盘里已存的文件；要看影视请导入 `config.json` 或 `movie-only.json`。

## 自动更新

`.github/workflows/update.yml` 每天定时拉取上游公开源，按可用性合并 `sites`/`parses`，提交回仓库。也可在 Actions 页手动触发。每次合并后会运行 `scripts/check.py` 校验，校验失败则不提交。

## 本地重新生成

```bash
python scripts/merge.py
```

依赖：Python 3（仅标准库，无第三方依赖）。

本地网盘配置（可选）：把 `winbox_pan_config.json` 放到 `data/` 目录下再运行，里面的 `parses` 会合并进去；该文件不提交进仓库。

## 导入方法（Zyfun / WIN-Box）

设置 → 数据配置 → 数据导入 → 类型选 **Tvbox** → 接口填上方订阅地址 → **覆盖** → 确定。

## 免责声明

配置聚合自互联网公开源，仅供学习交流。源站稳定性由原作者负责，本仓库不提供可用性承诺。
