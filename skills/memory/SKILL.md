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

### 1. 记忆碎片记录（手动触发）

**触发时机：**
- 用户说 `追加记忆碎片`
- 或手动调用

**执行动作：**
- 获取当前时间 `YYYY-MM-DD HH:mm:ss`
- 读取或创建 `memory/fragmentization/YYYY-MM-DD HH.md`
- 从会话历史中直接提取对话记录（无需模型交互）
- **追加**对话内容（时间戳 + 用户消息 + AI 回复 + 关键事件）
- 不修改已有内容

**数据来源：** `sessions_history` API（直接获取，不经过模型）

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
