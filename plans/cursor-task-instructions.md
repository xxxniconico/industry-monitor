# Cursor 任务指令 — Phase 1 数据管道

> 复制以下内容到 Cursor Composer (Agent 模式)

---

请按顺序完成以下任务。

## 第一步：了解项目

阅读以下文件：
1. `AGENTS.md` — 项目概述、技术栈约束、编码规范
2. `plans/phase-1-data-pipeline.md` — 每个任务的详细规格（API 地址、参数、输出格式）

## 第二步：安装依赖

```bash
uv pip install --python ~/.hermes/hermes-agent/venv/bin/python feedparser requests
```

## 第三步：按顺序创建 collector 脚本

所有脚本放在 `collectors/` 目录下。每个脚本独立运行，输出到 `data/raw/feeds/` 或 `data/raw/rss/`。

### Task 1: arXiv 论文追踪
- **文件：** `collectors/paper_tracker.py`
- **API：** `http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.LG+OR+cat:q-bio&sortBy=submittedDate&sortOrder=descending&max_results=50`
- **输出：** `data/raw/feeds/arxiv_YYYY-MM-DD.json`
- **依赖：** 用 `xml.etree.ElementTree`（标准库），不用 feedparser
- **注意：** 必须加 User-Agent header

### Task 2: RSS 监控
- **文件：** `collectors/rss_monitor.py`
- **数据源：** 10 个 RSS 源，见 `plans/phase-1-data-pipeline.md` 第 1.2 节
- **输出：** `data/raw/rss/YYYY-MM-DD.json`
- **依赖：** `feedparser`
- **注意：** 每个源加 timeout=15，try/except；自动判断 industry 字段（AI/medical/space/drone）

### Task 3: ClinicalTrials.gov
- **文件：** `collectors/clinical_trials.py`
- **API：** `https://clinicaltrials.gov/api/v2/studies?query.term=AREA[OverallStatus]RECRUITING+AND+AREA[StudyType]INTERVENTIONAL&pageSize=50&format=json`
- **输出：** `data/raw/feeds/clinical_trials_YYYY-MM-DD.json`

### Task 4: 航天发射
- **文件：** `collectors/launch_tracker.py`
- **API：** `https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=20`
- **输出：** `data/raw/feeds/launches_YYYY-MM-DD.json`

### Task 5: VC 融资新闻（可选，P2）
- **文件：** `collectors/vc_tracker.py`
- **RSS：** `https://techcrunch.com/feed/`
- **输出：** `data/raw/feeds/vc_news_YYYY-MM-DD.json`

## 验证

每完成一个脚本，运行一次：
```bash
cd ~/industry-monitor && python collectors/<script>.py
```

确认 JSON 文件生成在正确路径，`items` 不为空。

## 规则

- ✅ 每个脚本独立，不依赖其他文件
- ✅ API 不可达时写 error 字段，不崩溃
- ✅ 不删文件、不改 `data/` 以外的目录
- ❌ 禁止引入 Node.js / npm / 数据库
- ❌ 禁止修改 AGENTS.md 或 plans/ 下的文件

---

**每个任务的完整 Output JSON Schema 见 `plans/phase-1-data-pipeline.md`。**
