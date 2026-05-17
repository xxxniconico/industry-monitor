# AGENTS.md — Industry Monitor

> Cursor/OpenCode 工作指令。任何 AI 编码代理打开此仓库必须先读此文件。

## 项目概述

跨行业趋势监控系统。追踪 AI、医疗、航天、低空经济四个行业的趋势变化，基于七类信号（技术链/资本/技术/监管/市场/人才/基建）自动采集、分类、预警。

**完整框架文档：** `~/Documents/Obsidian Vault/行业趋势监控体系.md`

## 技术栈约束

- **语言：** Python 3.11+（WSL venv: `~/.hermes/hermes-agent/venv/`）
- **包管理：** `uv pip install`（Hermes venv 没有 pip）
- **数据存储：** JSON 文件（`data/processed/` 和 `data/models/`），不用数据库
- **看板：** Streamlit（后期 Phase 3），纯 HTML + fetch JSON 也可
- **禁止：** Node.js / React / npm / 数据库（SQLite 除外如需）
- **运行环境：** WSL Ubuntu，工作目录 `~/industry-monitor/`

## 目录结构

```
industry-monitor/
├── AGENTS.md              # 本文件
├── data/
│   ├── raw/               # 原始抓取数据（不提交 git）
│   │   ├── rss/           # blogwatcher 输出的 RSS 结果
│   │   ├── reports/       # 下载的 PDF/报告
│   │   └── feeds/         # API 拉取的结构化 JSON
│   ├── processed/         # 处理后的信号数据
│   │   ├── signals.json   # 七类信号分类结果
│   │   ├── trl_tracker.json
│   │   └── events.json    # 关键事件时间线
│   └── models/            # 人工判断 + 模型输出
│       ├── s_curve.json   # 各行业 S 曲线位置
│       └── porter.json    # 五力评估
├── collectors/            # 数据采集脚本（每个文件一个数据源）
├── processors/            # 信号处理和分类
├── dashboard/             # Streamlit 看板 (port 8505)
├── cron/                  # Hermes cron 任务模板
├── plans/                 # 实施计划和任务规格
└── skills/                # Hermes 技能文件
```

## 编码规范

1. 每个 collector 一个 Python 文件，独立运行，输出到 `data/raw/feeds/<name>.json`
2. 所有脚本必须能在 Hermes venv 下运行
3. 使用 `#!/usr/bin/env python3` shebang
4. 依赖用 `uv pip install <pkg>` 安装，记录在文件顶部注释中
5. HTTP 请求用 `requests` 或 `urllib`（标准库优先）
6. 输出格式统一为 JSON：`{"source": "...", "fetched_at": "ISO8601", "items": [...]}`
7. 错误处理：API 不可达时写 error 字段到 JSON，不抛异常退出
8. 不要硬编码 API key，从环境变量读取
9. 文件编码 UTF-8

## 关键约束

- **不操作数据库。** 所有数据存 JSON 文件。
- **不删除已有数据文件。** 只追加或覆盖写入。
- **不做个股分析。** 这是行业层面的监控系统。
- **不引入 Node.js/npm 依赖。**
- **每个脚本可独立运行，不依赖其他 collector。**
- **WSL 下网络：** TCP 直连可用，IPv6 不可用。curl 优先，避免 akshare。

## 任务分工

```
Hermes  → 规划、架构设计、写 AGENTS.md、任务拆解
Cursor  → 写代码、测试、验证（当前工作者）
OpenCode → 备胎，仅纯新代码生成
```

## 当前阶段：Phase 1 — 数据管道
