# Memory Skill - 记忆技能

## 📖 这是什么

为 OpenClaw 提供**长期记忆能力**的技能包，让 AI 助理能够：
- 📝 **记录** - 自动保存对话到记忆碎片
- 🧠 **整理** - 将碎片归纳为结构化知识（记忆宫殿）
- 🔍 **检索** - 通过 RAG 语义检索快速找到相关记忆

---

## 💡 设计思想

### 核心理念

**像人类一样记忆** — 短期记忆（碎片）→ 长期记忆（宫殿），越常用越牢固：

```
┌─────────────────────────────────────────────────────────┐
│  对话进行中                                              │
│    ↓                                                    │
│  碎片 (fragmentization/) ← 完整对话，按小时归档           │
│    ↓ (检索计数)                                          │
│  索引 (chroma/) ← 向量检索，追踪热度                     │
│    ↓ (≥10 分)                                           │
│  LLM 提炼 → 宫殿 (palace/) ← 结构化精华，类别聚合         │
└─────────────────────────────────────────────────────────┘
```

### 为什么这样设计

| 问题 | 传统方案 | Memory Skill 方案 |
|------|----------|------------------|
| 记忆太多读不完 | 全部加载 → 浪费 token | RAG 检索 → 只读相关的 |
| 检索不准确 | 关键词匹配 | 语义匹配（理解意思） |
| 维护成本高 | 手动整理 | 自动整理 + 增量更新 |
| 重要信息滞后 | 批量处理 | 混合写入（高频即时提炼） |
| Token 消耗 | 可能调用 LLM 整理 | 零 LLM（仅高频触发） |

### 关键决策

1. **混合写入** — 日常对话归档碎片，高频记忆提炼宫殿
2. **碎片按小时分割** — 避免单文件过大，便于定位
3. **检索计数加权** — 前 3 条 (1.0/0.7/0.4)，≥10 分触发提炼
4. **30 天滑动窗口** — 像人类一样，太久不用的会"遗忘"
5. **类别聚合** — 宫殿按 5 个类别聚合（偏好/待办/决策/人物/项目）
6. **OpenClaw LLM** — 直接使用 `openclaw agent`，无需额外 API

---

## 📁 文件结构

```
skills/memory/
├── SKILL.md                 # 技能定义（OpenClaw 加载）
├── README.md                # 本文档（人类可读）
├── requirements.txt         # Python 依赖
├── scripts/
│   ├── rag_search.py        # RAG 检索主脚本
│   ├── fragmentize.py       # 碎片记录脚本
│   └── consolidate.py       # 整理脚本
└── venv/                    # 虚拟环境（自动生成）
```

**运行时生成：**
```
memory/
├── fragmentization/         # 记忆碎片（按小时分割）
│   ├── 2026-03-11-19.md
│   └── ...
├── palace/                  # 记忆宫殿（5 个类别文件）
│   ├── preferences.md       # 偏好/习惯
│   ├── todos.md             # 待办事项
│   ├── decisions.md         # 重要决策
│   ├── people.md            # 人物关系
│   └── projects.md          # 项目工作
├── chroma/                  # 向量数据库索引
├── .state.json              # 整理状态
└── .frequent.json           # 检索计数（30 天窗口）
```

---

## 🧠 记忆读取时机

| 时机 | 说明 |
|------|------|
| 会话启动 | 新会话开始时读取热点记忆 |
| 提及相关话题 | 检测到关键词/项目名时 |
| 做决策前 | 涉及用户偏好/历史决策时 |
| 心跳检查 | 定期读取记忆 |
| 长对话中 | 对话超过 10 轮后 |
| 简单问答 | "今天天气如何" — 不读取 |
| 用户明确说不用查 | 跳过检索 |
| 紧急操作 | "快停止那个进程" — 不读取 |

---

## 🔄 记忆整理流程

### 自动整理（心跳触发）

**完整流程：**

```
心跳触发
    ↓
1. 读取未处理会话 → 写碎片（按小时）
2. 更新索引（碎片消息向量）
3. 检查 .frequent.json → 发现≥10 分的记忆
4. LLM 提炼（openclaw agent）→ 追加到宫殿
5. 更新索引（宫殿内容向量）
6. 清理 30 天前计数
7. 更新状态
```

**检索计数规则：**
- 每次检索前 3 条加权：第 1 条 +1.0，第 2 条 +0.7，第 3 条 +0.4
- 距离过滤：distance < 0.3 才计数
- 滑动窗口：30 天，过期自动清理
- 提炼阈值：累积≥10 分触发 LLM 提炼

### 手动整理

```bash
# 初始化/更新 RAG 索引
python scripts/rag_search.py init

# 搜索记忆
python scripts/rag_search.py search "用户偏好"

# 添加单个记忆
python scripts/rag_search.py add "filename.md" "内容"

# 手动触发整理（测试用）
python scripts/consolidate.py --dry-run
```

---

## 📦 依赖安装

**前提：** Python 3.8+ 和 pip

```bash
cd skills/memory

# 安装依赖
pip install -r requirements.txt

# 初始化索引
python scripts/rag_search.py init
```

**依赖说明：**
- `chromadb` - 本地向量数据库（必需）
- `sentence-transformers` - Embedding 模型，支持中文（必需）
- `faiss-cpu` - 可选，更快的向量检索（可选）

**注意：** 首次安装会下载模型文件（约 500MB）

---

## 🔧 故障处理

| 问题 | 处理方案 |
|------|----------|
| 索引为空 | 运行 `python scripts/rag_search.py init` |
| 检索无结果 | 正常，返回空列表 |
| 依赖未安装 | 运行 `pip install -r requirements.txt` |

---

## 🔍 RAG 检索详解

### 工作流程

```
用户提问
    ↓
检测需要记忆检索
    ↓
RAG 搜索（本地 ChromaDB + 向量匹配）
    ↓
返回最相关的 3-5 个记忆片段
    ↓
拼接上下文 → 发送给 LLM 生成回答
```

**关键点：**
- 检索阶段**不调用 LLM**，纯本地向量计算
- 只有最终生成回答时才消耗 LLM tokens
- Embedding 模型：`sentence-transformers`（本地运行，支持中文）

### 方案对比

| 方案 | Token 消耗 | 检索准确度 | 维护成本 |
|------|-----------|-----------|----------|
| **RAG 语义检索** | ~0 tokens | ⭐⭐⭐⭐⭐ 语义匹配 | 低（自动） |
| 读取所有记忆 | ~5000+ tokens | ⭐⭐⭐⭐ 完整上下文 | 低（但浪费） |
| 关键词匹配 | ~100-300 tokens | ⭐⭐ 字面匹配 | 中 |

### RAG 优势

- ✅ **检索几乎 0 LLM tokens** — 本地向量数据库
- ✅ **语义匹配** — 理解意思，不是关键词
- ✅ **自动维护索引** — 添加/更新记忆时自动同步
- ✅ **本地运行** — 无需外部 API，数据隐私安全
- ✅ **可扩展** — 支持数千个记忆文件

### 技术细节

| 组件 | 说明 |
|------|------|
| **向量数据库** | ChromaDB（本地持久化，DuckDB + Parquet） |
| **Embedding 模型** | `paraphrase-multilingual-MiniLM-L12-v2` |
| **相似度算法** | 余弦相似度（cosine） |
| **索引位置** | `memory/chroma/` |
| **索引文件** | `memory/index.json`（元数据缓存） |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd skills/memory
pip install -r requirements.txt
```

### 2. 初始化索引

```bash
python scripts/rag_search.py init
```

### 3. 使用

```bash
# 搜索记忆
python scripts/rag_search.py search "用户偏好"

# 添加记忆
python scripts/rag_search.py add "filename.md" "内容"
```

---

## 📝 版本历史

### v0.3.0 (2026-03-11) - 类人记忆架构
- ✅ 混合写入策略（碎片归档 + 高频提炼）
- ✅ 检索计数加权（前 3 条 1.0/0.7/0.4）
- ✅ 30 天滑动窗口（自动清理过期）
- ✅ ≥10 分触发 LLM 提炼
- ✅ 宫殿类别聚合（5 个文件）
- ✅ 直接使用 OpenClaw agent 调用 LLM
- ✅ 新增 `consolidate.py` 心跳整理脚本
- ✅ 新增 `fragmentize.py` 碎片追加脚本

### v0.1.1 (2026-03-11) - 简化架构
- ✅ 移除 directory.md，纯 RAG 检索
- ✅ 简化故障处理流程

### v0.1.0 (2026-03-11) - 初始版本
- ✅ 基础碎片记录功能
- ✅ RAG 语义检索（ChromaDB + sentence-transformers）
- ✅ 记忆宫殿结构定义
- ✅ 自动整理任务

---

## 🔗 相关文档

- [SKILL.md](./SKILL.md) - 完整技能定义
- [OpenClaw 文档](https://docs.openclaw.ai) - 平台文档

---

*最后更新：2026-03-11*
