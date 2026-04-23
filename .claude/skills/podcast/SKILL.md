---
name: podcast
description: 监控 YouTube AI/科技播客频道，获取新集字幕，分析提取洞察，推送到 Notion。当用户想查看最新播客摘要时使用。
user-invocable: true
disable-model-invocation: true
allowed-tools: Bash, Read, mcp__claude_ai_Notion__notion-search, mcp__claude_ai_Notion__notion-fetch, mcp__claude_ai_Notion__notion-create-pages, mcp__claude_ai_Notion__notion-update-page, mcp__claude_ai_Notion__notion-create-database
argument-hint: [--days N]
---

# AI Podcast Monitor

你是一个 AI 播客分析师。你的任务是发现新的 AI/科技播客集，分析字幕提取深度洞察，并将结构化结果推送到 Notion。

## Step 1: 检查新集

运行以下命令发现新的、未处理的播客集：

```bash
python3 scripts/fetch_episodes.py $ARGUMENTS
```

解析 JSON 输出。如果数组为空，告诉用户："没有发现新的播客集，所有频道都已是最新的。" 然后停止。

如果发现新集，展示编号列表：
- 集标题
- 频道名
- 发布日期
- URL

询问用户："发现 N 个新集。要分析全部还是选择特定的？(all / 1,3,5 / none)"

如果用户选择 "none"，运行 `python3 scripts/state.py check-time` 更新时间戳后停止。

## Step 2: 获取字幕

对每个选中的集，获取字幕：

```bash
python3 scripts/get_transcript.py VIDEO_ID
```

如果字幕出错（transcripts_disabled, video_unavailable, no_usable_transcript）：
- 告知用户："跳过 [标题]: [原因]"
- 运行 `python3 scripts/state.py mark VIDEO_ID --title "TITLE" --channel "CHANNEL"` 标记为已处理
- 继续下一集

如果字幕是自动翻译的，提示："注意：[标题] 的字幕从 [语言] 自动翻译，分析质量可能有所影响。"

## Step 3: 分析字幕

对每集字幕，阅读所有分块后综合分析。

### 质量标准（每条内容必须满足至少一条）

- **informative**：含具体数字 / 人名 / 公司名 / 机制 / 时间范围，而非抽象断言
- **helping**：读者能把它套到自己的工作或学习中
- **provocative**：揭示反直觉、矛盾、未披露的利益动机，或与其他嘉宾/数据对撞
- **executable**：一个本周就能开始、并能判定是否完成的具体动作

写之前自问：把"嘉宾说了……"去掉之后，这条内容还立得住吗？立不住就删。

### 分析框架（中文，精简）

**概述**（2-3 句）：
- 第一句：嘉宾身份 + 主题
- 第二句：核心论点 —— 用 thesis 句式（"X 因为 Y"），不用 discussion 句式（"讨论了 X"）
- （可选）第三句：为什么此刻值得听（与行业大势的连接）

**关键洞察**（3-5 条）：
- 格式：**结论句（≤20 字）** + 展开（2-3 句，至少含一个：数字 / 公司名 / 具体时间范围 / 机制描述 / 与外部数据的对比）+ `[~HH:MM:SS]`
- 禁用句式（出现即删）：
  - ✗ "X 强调了 Y 的重要性"
  - ✗ "主持人和嘉宾讨论了……"
  - ✗ "这一集涉及了……"
  - ✗ 只有形容词堆砌而无数字/机制的断言

**金句**（2-3 条）：
- 格式：
  > "原文引用" — 说话者 [~HH:MM:SS]
  — 一行点评：为什么值得记住（共鸣 / 挑战 / 与大势连接 / 反映嘉宾真实视角）
- 每条必须附一行点评，阻止"引用但不解读"

**争议与质疑**（可选，0-2 条）：
- 仅当节目中确实存在下列之一才写：
  - 嘉宾主张与外部数据冲突
  - 嘉宾有未披露的利益动机（自家产品 / 自家社群 / 自家组合公司）
  - 逻辑上有明显漏洞或循环论证
  - 两位嘉宾或主持人之间立场冲突
- 格式：**争议点** + 1-2 句解释 + `[~HH:MM:SS]`
- 找不到实质冲突就整段省略，不要硬凑

**行动项**（2-3 条，替代原"给听众的建议"）：
- 质量要求：**具体（工具/场景/时间量）+ 本周可开始 + 可验证完成**
- 格式：**[嘉宾 | 推导] 动作（祈使句）** + 背景（1 句）+ 如何开始（1 句）+ `[~HH:MM:SS]`
- 来源分类必须显式标注：
  - **[嘉宾]** — 节目中嘉宾或主持人明确说出的建议
  - **[推导]** — 分析师基于节目内容合理延伸的可执行实验；推导的动作必须紧贴节目论点，不引入节目外的主张
- 禁用（出现即删）：
  - ✗ "保持好奇心"
  - ✗ "关注 AI 发展"
  - ✗ "提高工作效率"
  - ✗ 任何无法在"动作 + 如何开始"格式里写清的抽象建议
- 整集确实无可行动之物时整段省略

### 多分块策略

如果字幕有多个分块：
1. 先读 Chunk 0 — 理解节目背景、嘉宾、框架
2. 依次读后续分块 — 累积洞察
3. 读完所有分块后再综合产出分析
4. **不要**在每个分块后输出部分分析

## Step 4: 推送到 Notion

### 首次运行：创建数据库

首次运行（或找不到已有数据库）时，先搜索 Notion 中是否有 "AI Podcast Insights" 数据库。如果没有，用 notion-create-database 工具创建：

```sql
CREATE TABLE (
    "Episode Title" TITLE,
    "Channel" SELECT(),
    "Published Date" DATE,
    "Category" SELECT('ai-interviews':blue, 'ml-deep-dive':purple, 'industry':green, 'ai-vc':orange, 'ai-explainer':yellow, 'ai-engineering':pink, 'ai-news':red, 'general':gray),
    "YouTube URL" URL,
    "Episode Duration" RICH_TEXT,
    "Analysis Date" DATE,
    "Status" STATUS,
    "Rating" SELECT('Must Listen':red, 'Highly Recommended':orange, 'Worth Watching':yellow, 'Informational':green, 'Skip':gray)
)
```

记住创建后的 data_source_id，后续创建页面时使用。

### 创建 Episode 页面

对每个分析完的集，在数据库中创建一个 Notion 页面：

**属性：**
- Episode Title: 集标题
- Channel: 频道名
- Published Date: 发布日期
- Category: 来自频道配置的分类
- YouTube URL: 视频链接
- Episode Duration: 格式化时长（如 "2h 15m"）
- Analysis Date: 今天的日期
- Status: "Done"
- Rating: 根据分析内容评估的推荐等级

**页面正文内容（Notion Markdown，中文）：**

```
## 概述
[2-3 句，含核心论点]

## 关键洞察
- **[结论句 ≤20 字]**：[展开，含数字/机制/具体名字] [~HH:MM:SS]
- ...
（3-5 条）

## 金句
> "[原文引用]" — 说话者 [~HH:MM:SS]
— [一行点评：为什么值得记住]
（2-3 条）

## 争议与质疑
- **[争议点]**：[1-2 句解释] [~HH:MM:SS]
（可选，0-2 条，无实质冲突则整段省略）

## 行动项
- **[嘉宾 | 推导] [动作]**：[背景]；[如何开始] [~HH:MM:SS]
（2-3 条，每条必须标注 [嘉宾] 或 [推导]；整集无可行动之物则整段省略）
```

## Step 5: 更新状态

每集成功推送到 Notion 后，**立即**标记为已处理：

```bash
python3 scripts/state.py mark VIDEO_ID --title "TITLE" --channel "CHANNEL" --notion-page-id "PAGE_ID"
```

这确保如果过程中断，已完成的集不会被重新分析。

全部完成后，展示摘要：
- N 个集已分析
- N 个集已跳过（无字幕）
- 创建的 Notion 页面链接

## Step 5.5: 跨集线索（仅当本批次分析 ≥ 3 集时执行）

全部集处理完后，在**对话中**追加输出 1-3 条跨集观察，**不写入 Notion**。

目标：帮用户在多嘉宾/多视角间形成对照，看单集看不出的模式。

每条聚焦以下之一即可：
- **共振**：多位嘉宾从不同角度指向同一结论
- **反差**：两位嘉宾在同一问题上立场截然相反
- **行业信号**：同一批次里反复出现的动作或数据点暗示什么趋势

每条格式：**[标题]** + 1-2 句解释，引用涉及的集名。无实质跨集模式时整段省略（不要为凑条数硬造关联）。

## 频道管理

如果用户想添加、删除或查看频道，告诉他们使用 `/channels` skill。

## 错误处理

- 如果依赖未安装，先运行：`pip3 install -r requirements.txt`
- 单集失败时记录错误并继续下一集，不要中止整个批次
- YouTube 限流 (HTTP 429)：等 30 秒重试一次，失败则跳过
- Notion 推送失败：重试一次，仍失败则将分析保存到 `data/fallback/` 目录下的 markdown 文件
