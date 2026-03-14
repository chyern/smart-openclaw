# smart-openclaw · OpenClaw 可插拔扩展系统

为 OpenClaw 提供轻量级、可插拔的设定追加和技能扩展能力，让你可以：
- 🧠 **动态扩展 AI 人格**（SOUL.md）
- ⚙️ **定制化行为流程**（AGENTS.md）
- 🔧 **灵活加载技能**（skills/）
- 🚀 **零修改原文件**，随时启用/禁用

---

## 📁 项目结构

```
smart-openclaw/
├── DESIGN.md                    # 追加规则说明
├── ADDITION_SOUL.md             # AI 人格补充设定
├── ADDITION_AGENTS.md           # 行为流程补充设定
├── skills/
│   ├── list-skills.sh           # 技能安装状态检查
│   └── memory/                  # 记忆管理技能
└── (其他配置文件)
```

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/chyern/smart-openclaw.git
cd smart-openclaw
```

### 2. 配置 OpenClaw
在你的 OpenClaw 工作区 `AGENTS.md` 中添加一行：

```markdown
读 /path/to/smart-openclaw/DESIGN.md，根据其内容执行额外的动作
```

### 3. 自定义设定（可选）
编辑追加文件来扩展 AI 的行为：
- `ADDITION_SOUL.md` – 人格与底线
- `ADDITION_AGENTS.md` – 工作流程与 Git 策略

### 4. 管理技能
- **添加技能**：放入 `skills/` 目录即可自动加载
- **检查状态**：运行 `./skills/list-skills.sh`，查看哪些技能已安装（✅/❌）

### 5. 同步更新
定期 `git pull` 获取最新设定。

---

## 🧩 工作原理

smart-openclaw 采用 **内存拼接** 机制：

1. **运行时拼接** – OpenClaw 在启动时将原文件（`SOUL.md`/`AGENTS.md`）与追加文件在内存中合并
2. **文件独立** – 不修改 OpenClaw 原文件，追加文件保持独立
3. **自动生效** – 文件存在即启用，删除即失效
4. **连接加载** – 技能通过文件连接方式加载，不复制内容

```
原文件 + 追加文件 → 内存拼接 → OpenClaw 实际使用的设定
```

## 📋 追加规则详情

详见 [DESIGN.md](./DESIGN.md)，核心原则：

| 原则 | 说明 |
|------|------|
| **内存拼接** | 设定在运行时拼接，不修改原本文件 |
| **文件独立** | 追加文件保持独立，不修改原始文件 |
| **连接模式** | 追加 skill 使用文件连接，不复制文件内容 |
| **自动启用** | 文件存在即启用，删除即失效 |

## 🔗 参考链接

- [OpenClaw 官方文档](https://docs.openclaw.ai)
- [OpenClaw 技能中心 (ClawHub)](https://clawhub.com)
- [GitHub 仓库](https://github.com/chyern/smart-openclaw)

---

> 提示：所有设定都是 **可插拔** 的——随时添加、修改或移除，无需重启 OpenClaw 服务。