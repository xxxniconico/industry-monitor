# Phase 1 实施计划：数据管道

> Hermes 规划 | Cursor 执行 | 2026-05-17

## 总目标

建立四个行业的数据采集管道。每个 collector 独立运行，输出统一 JSON 格式。

## 任务列表

| ID | 任务 | 优先级 | 预计工作量 |
|----|------|:------:|----------|
| 1.1 | 创建 `.gitignore` + `requirements.txt` | P0 | 10min |
| 1.2 | RSS 监控脚本 (`rss_monitor.py`) | P0 | 30min |
| 1.3 | arXiv 论文追踪 (`paper_tracker.py`) | P0 | 20min |
| 1.4 | ClinicalTrials.gov 追踪 (`clinical_trials.py`) | P1 | 25min |
| 1.5 | 航天发射追踪 (`launch_tracker.py`) | P1 | 20min |
| 1.6 | VC 融资新闻追踪 (`vc_tracker.py`) | P2 | 25min |

---

## 1.1 `.gitignore` + `requirements.txt`

**规格：**
- `.gitignore`：忽略 `data/raw/`、`__pycache__/`、`.env`、`*.pyc`
- `requirements.txt`：列出所有 Python 依赖
- 初始依赖：`requests`, `feedparser`

**验收：** `git status` 不显示 `data/raw/` 下的文件

---

## 1.2 RSS 监控脚本

**文件：** `collectors/rss_monitor.py`

**数据源（10 个 RSS）：**

| # | 名称 | RSS URL | 覆盖行业 |
|---|------|---------|:-------:|
| 1 | ArXiv CS.AI | `http://export.arxiv.org/rss/cs.AI` | AI |
| 2 | Stanford HAI | `https://hai.stanford.edu/rss.xml` | AI |
| 3 | MIT Technology Review | `https://www.technologyreview.com/feed/` | AI/Tech |
| 4 | OpenAI Blog | `https://openai.com/blog/rss.xml` | AI |
| 5 | STAT News | `https://www.statnews.com/feed/` | 医疗 |
| 6 | FDA News | `https://www.fda.gov/about-fda/contact-fda/rss-feeds/fda-news-releases/rss.xml` | 医疗 |
| 7 | FierceBiotech | `https://www.fiercebiotech.com/rss.xml` | 医疗 |
| 8 | SpaceNews | `https://spacenews.com/feed/` | 航天 |
| 9 | NASA Breaking News | `https://www.nasa.gov/news-release/feed/` | 航天 |
| 10 | DroneDJ | `https://dronedj.com/feed/` | 低空经济 |

**输出格式：**

```json
{
  "source": "rss_monitor",
  "fetched_at": "2026-05-17T10:00:00Z",
  "items": [
    {
      "title": "...",
      "url": "...",
      "published": "2026-05-17T08:00:00Z",
      "source_feed": "ArXiv CS.AI",
      "industry": "AI",
      "summary": "..."
    }
  ]
}
```

**输出路径：** `data/raw/rss/YYYY-MM-DD.json`

**依赖：** `feedparser`（`uv pip install feedparser`）

**运行方式：** `python collectors/rss_monitor.py`

**验收标准：** 运行一次能抓到 10 个源的至少 7 个，输出正确 JSON 格式。

**注意事项：**
- 部分 RSS 源可能被墙，加 timeout=15 和 try/except
- 用 `requests` 发 HTTP，不用 `feedparser` 直接 parse URL（方便加 headers）
- industry 字段用简单关键词匹配映射：AI/medical/space/drone

---

## 1.3 arXiv 论文追踪

**文件：** `collectors/paper_tracker.py`

**数据源：** arXiv API (`http://export.arxiv.org/api/query`)

**查询分类：**
| 分类 | 覆盖行业 |
|------|:-------:|
| `cs.AI` | AI |
| `cs.CL` (计算语言学) | AI |
| `cs.LG` (机器学习) | AI |
| `q-bio` (定量生物) | 医疗 |
| `stat.ML` | AI |

**参数：** 每次取最近 50 篇，`sortBy=submittedDate&sortOrder=descending`

**输出格式：**

```json
{
  "source": "arxiv",
  "fetched_at": "...",
  "items": [
    {
      "title": "...",
      "arxiv_id": "2605.12345",
      "url": "https://arxiv.org/abs/2605.12345",
      "published": "2026-05-17T00:00:00Z",
      "categories": ["cs.AI", "cs.CL"],
      "industry": "AI",
      "summary": "..." 
    }
  ]
}
```

**输出路径：** `data/raw/feeds/arxiv_YYYY-MM-DD.json`

**依赖：** `feedparser` 或直接用 `xml.etree.ElementTree`（标准库）

**注意事项：**
- arXiv API 要求 User-Agent header
- 请求间隔至少 3 秒（rate limit）

---

## 1.4 ClinicalTrials.gov 追踪

**文件：** `collectors/clinical_trials.py`

**数据源：** ClinicalTrials.gov API v2 (`https://clinicaltrials.gov/api/v2/studies`)

**查询参数：**
- `query.term=AREA[OverallStatus]RECRUITING+AND+AREA[StudyType]INTERVENTIONAL`
- `pageSize=50`
- `format=json`

**输出格式：**

```json
{
  "source": "clinicaltrials",
  "fetched_at": "...",
  "items": [
    {
      "nct_id": "NCT...",
      "title": "...",
      "status": "RECRUITING",
      "phase": "Phase 2",
      "conditions": ["..."],
      "interventions": ["..."],
      "start_date": "2026-05-01",
      "url": "https://clinicaltrials.gov/study/NCT..."
    }
  ]
}
```

**输出路径：** `data/raw/feeds/clinical_trials_YYYY-MM-DD.json`

**依赖：** `requests`

**注意事项：**
- API 免费，无需 API key
- 只取最近更新的试验（`query.term=...` 已限制）
- Phase 字段可能为空（Early Phase 1），正常

---

## 1.5 航天发射追踪

**文件：** `collectors/launch_tracker.py`

**数据源：** 
- 方案 A（推荐）：The Space Devs Launch Library API (`https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=20`)
- 方案 B（备选）：Wikipedia 页面抓取

**输出格式：**

```json
{
  "source": "launch_library",
  "fetched_at": "...",
  "items": [
    {
      "name": "Starlink Group 12-1",
      "provider": "SpaceX",
      "rocket": "Falcon 9",
      "launch_date": "2026-05-20T12:00:00Z",
      "status": "upcoming",
      "url": "...",
      "mission_type": "communications"
    }
  ]
}
```

**输出路径：** `data/raw/feeds/launches_YYYY-MM-DD.json`

**依赖：** `requests`

**注意事项：**
- The Space Devs API 免费，无需 key
- 如果 API 不可用，fallback 到写入 error JSON

---

## 1.6 VC 融资新闻追踪

**文件：** `collectors/vc_tracker.py`

**数据源：** 
- 方案 A：Crunchbase News RSS (`https://news.crunchbase.com/feed/`)
- 方案 B：TechCrunch RSS (`https://techcrunch.com/feed/`)
- 方案 C：直接 web_extract CB Insights 公开摘要

**输出格式：**

```json
{
  "source": "vc_news",
  "fetched_at": "...",
  "items": [
    {
      "title": "...",
      "url": "...",
      "published": "...",
      "industry": "AI",
      "summary": "X raised $Y million for Z...",
      "funding_amount": null,
      "company_name": null
    }
  ]
}
```

**输出路径：** `data/raw/feeds/vc_news_YYYY-MM-DD.json`

**依赖：** `feedparser`

**注意事项：**
- 免费源数据有限，这是辅助信号
- 融资额和公司名解析是可选功能，做不好就留 null
- 优先级 P2，可以最后做

---

## 执行顺序

```
1.1 → 1.3 (arxiv, 最快出结果验证管道) 
    → 1.2 (rss, 核心采集)
    → 1.4 (clinical trials)
    → 1.5 (launches)
    → 1.6 (vc, P2 可选)
```

## 验证方式

每个 collector 完成后运行一次，检查：
1. JSON 文件生成在正确的路径
2. `items` 数组不为空
3. 日期格式 ISO8601
4. 错误时输出 error 字段而非崩溃

---

## 下一步（Phase 2 预览）

信号分类器 + TRL 估算器。Phase 1 的所有输出作为 Phase 2 的输入。
