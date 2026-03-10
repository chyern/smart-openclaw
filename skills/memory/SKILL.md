# Memory Skill - 对话记忆与归纳

## 定义

### 记忆碎片（Memory Fragmentization）
**路径：** `memory/fragmentization/YYYY-MM-DD HH.md`

- 原始、完整、追加式的对话日志
- 每次用户交互时自动记录
- 保留所有细节，不做筛选
- 按小时分割文件（便于管理和定位）
- **时间戳精度：** 秒级（`HH:mm:ss`）

### 记忆宫殿（Memory Palace）
**路径：** `memory/palace/`

- 由记忆碎片整理生成的结构化知识库
- 按照不同的知识体系创建下级目录
- 根据具体内容创建不同的 `.md` 文件
- **文件命名：** 英文（如 `user-preferences.md`、`project-context.md`）
- **内容风格：** 中文
- **热度分类：**
  - 🔥 热点记忆 - 高频读取的内容
  - ❄️ 冷记忆 - 低频读取的内容

### 记忆目录（Memory Directory）
**路径：** `memory/directory.md`

- 维护记忆在记忆宫殿中的路径和说明
- **不记录具体内容**，只记录索引
- 通过路径定位到记忆宫殿中的具体内容
- 记录**上一次整理时间**，用于增量整理

### 记忆整理（Memory Organization）
- 根据记忆目录中的上次整理时间，列出待整理的记忆碎片
- 将记忆碎片中的内容维护到记忆宫殿
- 同步更新记忆目录
- **触发方式：**
  - 手动指令：`记忆整理`
  - 自动任务：每天 23:59

## 核心概念对比

| 概念 | 路径 | 更新方式 | 定位 |
|------|------|----------|------|
| 记忆碎片 | `memory/fragmentization/YYYY-MM-DD HH.md` | 追加式 | 原始对话日志 |
| 记忆宫殿 | `memory/palace/` | 结构化组织 | 知识库 |
| 记忆目录 | `memory/directory.md` | 索引更新 | 路径索引 + 整理时间 |

## 文件结构

```
workspace/
└── memory/
    ├── directory.md                    # 记忆目录（索引）
    ├── palace/                         # 记忆宫殿
    │   ├── user/                       # 用户相关
    │   │   ├── preferences.md          # 用户偏好
    │   │   └── context.md              # 用户上下文
    │   ├── projects/                   # 项目相关
    │   │   ├── company.md              # 公司项目
    │   │   └── personal.md             # 个人项目
    │   ├── environment/                # 环境配置
    │   │   └── system.md               # 系统环境
    │   └── knowledge/                  # 知识体系
    │       └── ...                     # 其他知识
    └── fragmentization/                # 记忆碎片
        ├── 2026-03-10 14.md            # 按小时分割
        ├── 2026-03-10 15.md
        └── ...
```

## 行为规则

### 1. 记忆碎片记录（AI 主动执行）

**触发时机：** AI 在每次回复用户**之后**主动执行（本轮交互结束前）

> ⚠️ **强制要求：** 这是**每次回复必须执行**的流程，不是可选项。
>
> **为什么：**
> - 这不是自动 hook，需要 AI 主动调用
> - 必须在 AI 回复内容已发送后执行，才能获取完整对话
> - **无额外 token 消耗** — `sessions_history` 是工具调用，不经过 LLM
>
> **执行顺序：**
> 1. AI 生成并发送回复给用户
> 2. AI 调用 `sessions_history` 获取完整会话历史
> 3. 从 `lastMessageId` 之后提取新对话
> 4. 追加到碎片文件
> 5. 更新 `fragmentization-state.json`

**执行动作：**
1. **读取状态** — `memory/fragmentization/fragmentization-state.json` 获取 `lastMessageId`
2. **获取 sessionKey** — 调用 `sessions_list(limit=1)` 获取当前会话 key
3. **获取历史** — 调用 `sessions_history(sessionKey, limit=100)` 获取会话历史
4. **提取新对话** — 从 `lastMessageId` 之后提取所有用户消息和 AI 回复
5. **格式化记录** — `HH:mm:ss` 时间戳 + 角色 + 内容 + 元数据（频道、发件人/收件人）
6. **追加到碎片文件** — `memory/fragmentization/YYYY-MM-DD HH.md`（按小时分割）
7. **更新状态** — 写入最新的 `lastMessageId` 和 `lastRunAt`

**数据来源：** `sessions_history` API（直接获取，不经过模型，**无 token 消耗**）

**状态文件：** `memory/fragmentization/fragmentization-state.json`
```json
{
  "lastMessageId": "消息 timestamp 或 ID",
  "lastRunAt": "ISO-8601 时间戳"
}
```

**示例记录格式：**
```markdown
## 14:23:45 - 用户消息

**频道:** telegram
**发件人:** +1234567890

今天天气怎么样？

---

## 14:23:50 - AI 回复

**频道:** telegram
**收件人:** +1234567890

深圳今天晴，气温 25°C。

---
```

**注意事项：**
- 按小时分割文件：`YYYY-MM-DD HH.md`（如 `2026-03-11 02.md`）
- 时间使用 Asia/Shanghai 时区
- 如果碎片文件不存在，创建新文件
- 状态文件必须每次更新，避免重复记录

### 2. 记忆整理（手动/自动）

**触发时机：**
- 用户说 `记忆整理`
- 每日 23:59 定时任务

**执行流程：**
1. 读取 `memory/directory.md` 获取上次整理时间
2. 列出 `memory/fragmentization/` 中上次整理时间之后的所有文件
3. 读取这些记忆碎片，提取有价值的内容
4. 分类整理到 `memory/palace/` 的对应文件中
5. 更新 `memory/directory.md`：
   - 更新记忆宫殿中各文件的路径索引
   - 更新**本次整理时间**

**整理原则：**
- 🔥 热点记忆 - 频繁提及的内容（用户偏好、常用指令、当前项目）
- ❄️ 冷记忆 - 一次性或低频内容（临时任务、历史对话）

### 3. 记忆目录维护

**记录内容：**
```markdown
# 记忆目录

## 上次整理时间
2026-03-10 15:00

## 记忆宫殿索引

| 路径 | 说明 | 热度 |
|------|------|------|
| palace/user/preferences.md | 用户偏好和习惯 | 🔥 |
| palace/user/context.md | 用户身份和上下文 | 🔥 |
| palace/projects/company.md | 公司项目 | 🔥 |
| palace/environment/system.md | 系统环境配置 | ❄️ |
```

## 配置示例

### 定时任务（cron）

```json
{
  "name": "每日记忆整理",
  "schedule": {"kind": "cron", "expr": "59 23 * * *", "tz": "Asia/Shanghai"},
  "payload": {"kind": "agentTurn", "message": "执行记忆整理：读取 memory/directory.md 获取上次整理时间，整理之后的记忆碎片到记忆宫殿，更新记忆目录。"},
  "sessionTarget": "isolated"
}
```

## 指令响应

| 用户指令 | 行为 |
|----------|------|
| `记忆整理` | 立即执行记忆整理流程 |
| `在记忆宫殿中查找:{关键词}` | 根据记忆目录查找记忆宫殿中记录的内容 |

## 版本

- v2.0 - 2026-03-10 - 记忆宫殿架构重构
- v1.0 - 2026-03-10 - 初始版本
