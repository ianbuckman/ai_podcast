# AI Podcast Monitor

监控 YouTube AI/科技播客频道，自动提取字幕，用 Claude 分析提取洞察，推送结构化结果到 Notion。

## 功能

- 通过 RSS 订阅自动发现 YouTube 播客新集
- 提取视频字幕（支持多语言，自动翻译为英文）
- 用 Claude 深度分析字幕内容，提炼关键洞察和金句
- 将分析结果结构化推送到 Notion 数据库
- 自动跟踪已处理集数，避免重复分析

## 前置要求

- Python 3.9+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- Notion MCP 集成（用于推送分析结果）

## 安装

```bash
git clone <repo-url>
cd ai_podcast
pip install -r requirements.txt
```

依赖包：
- `pyyaml` — 解析频道配置
- `youtube-transcript-api` — 获取 YouTube 字幕

> 无需 YouTube API Key，RSS 订阅和字幕获取均为免费接口。

## 快速开始

在 Claude Code 中运行 `/podcast` 即可触发完整工作流：

```
/podcast           # 分析最近 7 天的新集
/podcast --days 14 # 分析最近 14 天的新集
```

工作流程：
1. 检查所有订阅频道的新集
2. 展示新集列表，等待用户选择
3. 获取字幕并用 Claude 分析
4. 推送结果到 Notion 数据库 "AI Podcast Insights"
5. 标记已处理，更新状态

## 频道管理

### 查看已订阅频道

```bash
python scripts/manage_channels.py list
```

### 添加频道

支持频道名、@handle 或 YouTube URL，channel_id 会自动解析：

```bash
python scripts/manage_channels.py add "@lexfridman" --category ai-interviews
python scripts/manage_channels.py add "No Priors" --category ai-vc
python scripts/manage_channels.py add "https://www.youtube.com/@ycombinator" --category general
```

可用分类：`ai-interviews`、`ml-deep-dive`、`ai-vc`、`ai-explainer`、`ai-engineering`、`ai-news`、`general`

### 删除频道

```bash
python scripts/manage_channels.py remove "频道名"  # 支持模糊匹配
```

## 单独使用脚本

每个脚本可独立运行，便于调试：

```bash
# 获取新集（输出 JSON 到 stdout）
python scripts/fetch_episodes.py --days 7

# 获取指定视频的字幕
python scripts/get_transcript.py VIDEO_ID

# 解析频道名/@handle 为 channel_id
python scripts/resolve_channel.py "@lexfridman"

# 管理处理状态
python scripts/state.py show            # 查看状态摘要
python scripts/state.py mark VIDEO_ID   # 标记为已处理
```

## 项目结构

```
ai_podcast/
├── config/
│   └── channels.yaml        # 订阅频道配置
├── scripts/
│   ├── fetch_episodes.py    # 通过 RSS 获取新集
│   ├── get_transcript.py    # 获取并分块字幕
│   ├── manage_channels.py   # 频道增删查
│   ├── resolve_channel.py   # 解析频道名为 channel_id
│   └── state.py             # 管理已处理状态
├── data/                    # 运行时数据（gitignored）
│   └── processed.json       # 已处理集跟踪
├── .claude/
│   └── skills/podcast/
│       └── SKILL.md         # Claude Code /podcast 技能定义
├── requirements.txt
└── CLAUDE.md
```

## 默认订阅频道

| 频道 | 分类 |
|------|------|
| Lex Fridman Podcast | ai-interviews |
| No Priors | ai-vc |
| Y Combinator | general |
| Lenny's Podcast | general |
| Last Week in AI | ai-news |

## 约定

- 所有脚本输出 JSON 到 stdout，日志/错误输出到 stderr
- 使用相对于项目根目录的绝对路径
- 状态文件 `data/processed.json` 不纳入版本控制
