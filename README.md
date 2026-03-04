# AI Podcast Monitor

在 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 中用自然语言管理你的 AI/科技播客订阅。Claude 会自动发现新集、分析字幕内容、提炼关键洞察，并推送到 Notion。

## 快速开始

```bash
git clone <repo-url>
cd ai_podcast
pip install -r requirements.txt
```

然后在 Claude Code 中打开此项目，用自然语言告诉 Claude 你想做什么。

## 使用方式

所有操作通过在 Claude Code 中对话完成，以下是你可以表达的意图：

### 查看最新播客

> "帮我看看最近有什么新的播客"
>
> "最近两周有哪些新集？"

Claude 会检查所有订阅频道的更新，列出新集，你可以选择分析全部或部分。分析完成后结果会自动推送到 Notion 数据库。

### 查看已订阅的频道

> "我现在订阅了哪些频道？"
>
> "列一下当前的频道"

### 添加频道

> "帮我加一下 @lexfridman"
>
> "订阅 No Priors 这个频道，分类是 ai-vc"
>
> "把 https://www.youtube.com/@ycombinator 加到频道列表"

支持频道名、@handle 或 YouTube URL，channel_id 会自动解析。

可用分类：`ai-interviews` · `ml-deep-dive` · `ai-vc` · `ai-explainer` · `ai-engineering` · `ai-news` · `general`

### 删除频道

> "把 Lex Fridman 从订阅列表里删掉"
>
> "取消订阅 No Priors"

### 用 `/podcast` 直接触发分析

除了自然语言，也可以用 skill 快捷命令：

```
/podcast           # 分析最近 7 天的新集
/podcast --days 14 # 分析最近 14 天
```

## 分析产出

每集分析后会在 Notion 数据库 "AI Podcast Insights" 中创建一个页面，包含：

- **概述** — 嘉宾、主题、核心论点（2-3 句）
- **关键洞察** — 最有价值的 5 条洞察，附时间戳
- **金句** — 最有冲击力的直接引用

## 默认订阅频道

| 频道 | 分类 |
|------|------|
| Lex Fridman Podcast | ai-interviews |
| No Priors | ai-vc |
| Y Combinator | general |
| Lenny's Podcast | general |
| Last Week in AI | ai-news |

## 前置要求

- Python 3.9+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- Notion MCP 集成（用于推送分析结果）
- 无需 YouTube API Key
