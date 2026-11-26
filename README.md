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
| `config.json` | 影视采集站 + 网盘 + 解析，全量合一 | ✅ 日常用这个 |
| `pan-only.json` | 只有 10 种网盘（无影视资源） | 只想挂载自己网盘时用 |
| `movie-only.json` | 只有影视采集站 | 只要免费影视时用 |

> 网盘源本身不含影视内容，只能列出你自己网盘里已存的文件；要看影视请导入 `config.json` 或 `movie-only.json`。

## 自动更新

`.github/workflows/update.yml` 每天定时拉取上游公开源，按可用性合并 `sites`/`parses`，提交回仓库。也可在 Actions 页手动触发。

## 本地重新生成

```bash
python scripts/merge.py
```

依赖：Python 3 + requests（可选，标准库 urllib 亦可）。

## 导入方法（Zyfun / WIN-Box）

设置 → 数据配置 → 数据导入 → 类型选 **Tvbox** → 接口填上方订阅地址 → **覆盖** → 确定。

## 免责声明

配置聚合自互联网公开源，仅供学习交流。源站稳定性由原作者负责，本仓库不提供可用性承诺。
