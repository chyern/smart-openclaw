# Memory Skill - 对话记忆与归纳

## 核心定义

### 存储结构

| 层级 | 路径 | 用途 |
|------|------|------|
| **碎片** | `memory/fragmentization/YYYY-MM-DD-HH.md` | 原始对话日志（追加式，按小时分割） |
| **宫殿** | `memory/palace/{category}.md` | 提炼后的高频记忆（5 个类别文件） |
| **索引** | `memory/chroma/` | ChromaDB 向量索引（语义检索） |
| **计数** | `memory/.frequent.json` | 检索计数（30 天滑动窗口） |
| **状态** | `memory/.state.json` | 整理状态追踪 |

### 写入策略（混合模式）

| 触发条件 | 写入目标 | 说明 |
|----------|----------|------|
| 心跳整理 | **碎片** | 完整对话归档 |
| 检索≥10 分 | **宫殿** | LLM 提炼后写入 |

---

## AI 使用指南

### 1. 初始化检查

**每次会话启动时执行：**
```bash
# 检查索引是否存在
if [ ! -d "$WORKSPACE_ROOT/memory/chroma" ]; then
    python skills/memory/scripts/rag_search.py init
fi
```

---

### 2. 记忆检索

**触发条件（满足任一即检索）：**
- 用户提到具体人名、项目名、地点
- 用户提问涉及偏好/历史/决策（"我之前说过..."）
- 对话超过 10 轮，需要上下文
- 心跳检查时（定期回顾）

**不检索的情况：**
- 简单事实问答（"今天几号"）
- 紧急操作（"快停止进程"）
- 用户明确说"不用查"

**检索命令（AI 调用）：**
```bash
python skills/memory/scripts/rag_search.py search "<查询内容>"
```

**Query 提取策略：**
| 用户输入 | 提取的 Query |
|----------|-------------|
| "我上次说的那个项目" | "项目" |
| "用户喜欢吃什么" | "用户 偏好 食物" |
| "公司的加班文化" | "公司 加班 文化" |
| "记得帮我记下来" | （不检索，触发添加） |

**返回格式：**
```json
[{"content": "...", "filename": "...", "filepath": "...", "distance": 0.xx}]
```

**处理逻辑：**
- `distance < 0.3` → 高相关，直接使用
- `distance 0.3-0.6` → 中等相关，谨慎引用
- `distance > 0.6` 或空列表 → 无结果，告知用户"没找到相关记忆"

---

### 3. 记忆添加

**触发时机：**
- 心跳整理 → 碎片（自动）
- 检索≥10 分 → 宫殿（LLM 提炼）
- 用户说"记住这个" → 直接调用 `rag_search.py add`

**添加命令：**
```bash
python skills/memory/scripts/rag_search.py add "<文件名>" "<内容>"
```

**文件名参数：** 相对于 `memory/palace/` 的路径（支持子目录）

**目录结构：** 按需创建，无预定义限制

**常见分类参考：**
```
memory/palace/
├── preferences/     # 偏好/习惯
├── projects/        # 项目信息
├── people/          # 人物相关
├── todos/           # 待办事项
├── context/         # 背景知识
├── decisions/       # 重要决策
├── skills/          # 技能/能力
└── events/          # 事件记录
```

**命名原则：**
- 语义清晰（文件名能反映内容）
- 同类聚合（相关内容放同一目录）
- 避免过深（建议不超过 2 层子目录）

---

### 4. 心跳整理流程

**系统后台自动执行**（AI 不主动调用，只负责读取）：

**状态追踪：** `memory/.state.json`

**流程：**
```
1. 读取未处理会话 → 写碎片
2. 更新索引（碎片消息向量）
3. 检查 .frequent.json → 发现≥10 分的记忆
4. LLM 提炼 → 追加到宫殿
5. 更新索引（宫殿内容向量）
6. 清理 30 天前计数
7. 更新状态
```

**AI 角色：**
- 对话中：无需额外操作
- 心跳时：直接读取已更新的记忆宫殿和索引
- 用户说"记住这个"时：调用 `rag_search.py add` 立即添加

---

## 依赖与环境

**安装依赖：**
```bash
pip install -r skills/memory/requirements.txt
```

**依赖包：**
- `chromadb` - 向量数据库
- `sentence-transformers` - Embedding 模型（支持中文）

**环境变量：**
- `WORKSPACE_ROOT` - 工作区根目录（由 OpenClaw 自动设置）

---

## 故障处理

| 问题 | 处理方案 |
|------|----------|
| 索引目录不存在 | 运行 `init` 初始化 |
| 检索返回空列表 | 告知用户"没找到相关记忆"，不报错 |
| 依赖未安装 | 提示运行 `pip install -r requirements.txt` |
| 脚本执行失败 | 降级到不检索，继续对话 |

---

## 脚本位置

- **rag_search.py** — RAG 检索/添加/初始化
- **consolidate.py** — 心跳整理（主脚本）
- **fragmentize.py** — 碎片追加

---
