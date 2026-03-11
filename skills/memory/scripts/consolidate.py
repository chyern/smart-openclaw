#!/usr/bin/env python3
"""
Memory Skill - 心跳整理脚本

流程：
1. 读取未处理会话 → 写碎片
2. 更新索引（碎片消息）
3. 检查高频记忆（score ≥ 10）
4. 批量 LLM 提炼 → 写宫殿
5. 更新索引（宫殿内容）
6. 清理过期计数（30 天）
7. 更新状态

用法:
    python consolidate.py              # 正常执行
    python consolidate.py --dry-run    # 预览
    python consolidate.py --force      # 强制重新处理
"""

import sys
import os
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# 依赖检查
try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False
    print("警告：chromadb 未安装，索引功能将跳过")

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE = True
except ImportError:
    HAS_SENTENCE = False
    print("警告：sentence-transformers 未安装，索引功能将跳过")

# 配置
CONFIG = {
    "distance_threshold": 0.3,      # 检索距离阈值
    "count_top_n": 3,               # 计数前 N 条
    "weights": [1.0, 0.7, 0.4],     # 加权系数
    "refine_threshold": 10.0,       # 提炼阈值
    "window_days": 30,              # 滑动窗口天数
    "llm_batch_size": 5,            # LLM 批量大小
    "max_sessions": 10,             # 每次最多处理会话数
}


class MemoryConsolidator:
    """心跳整理器"""
    
    CATEGORIES = ["preferences", "todos", "decisions", "people", "projects"]
    
    def __init__(self, workspace_root: str):
        self.workspace = Path(workspace_root)
        self.memory_dir = self.workspace / "memory"
        self.chroma_dir = self.memory_dir / "chroma"
        self.palace_dir = self.memory_dir / "palace"
        self.fragment_dir = self.memory_dir / "fragmentization"
        self.state_file = self.memory_dir / ".state.json"
        self.frequent_file = self.memory_dir / ".frequent.json"
        
        # 确保目录存在
        for d in [self.chroma_dir, self.palace_dir, self.fragment_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # 初始化宫殿文件
        self._init_palace_files()
        
        # 状态
        self.state = self._load_state()
        self.frequent = self._load_frequent()
        
        # ChromaDB
        self.collection = None
        self.embed_model = None
        if HAS_CHROMA:
            self._init_chroma()
    
    def _init_palace_files(self):
        """初始化宫殿文件"""
        for cat in self.CATEGORIES:
            palace_file = self.palace_dir / f"{cat}.md"
            if not palace_file.exists():
                palace_file.write_text(f"# {cat.title()}\n\n_最后更新：{datetime.now().isoformat()}_\n\n---\n\n", encoding="utf-8")
    
    def _load_state(self) -> dict:
        """加载状态"""
        if self.state_file.exists():
            with open(self.state_file, encoding="utf-8") as f:
                return json.load(f)
        return {"processed_sessions": [], "last_consolidation": None}
    
    def _save_state(self):
        """保存状态"""
        self.state["last_consolidation"] = datetime.now().isoformat()
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
    
    def _load_frequent(self) -> dict:
        """加载计数"""
        if self.frequent_file.exists():
            with open(self.frequent_file, encoding="utf-8") as f:
                return json.load(f)
        return {"_last_cleanup": datetime.now().isoformat()}
    
    def _save_frequent(self):
        """保存计数"""
        self.frequent["_last_cleanup"] = datetime.now().isoformat()
        with open(self.frequent_file, "w", encoding="utf-8") as f:
            json.dump(self.frequent, f, indent=2, ensure_ascii=False)
    
    def _init_chroma(self):
        """初始化 ChromaDB"""
        if not HAS_CHROMA:
            return
        
        client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=str(self.chroma_dir),
            anonymized_telemetry=False
        ))
        
        self.collection = client.get_or_create_collection(
            name="memory",
            metadata={"hnsw:space": "cosine"}
        )
    
    def _get_embed_model(self):
        """懒加载 embedding 模型"""
        if self.embed_model is None and HAS_SENTENCE:
            self.embed_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        return self.embed_model
    
    def _embed(self, text: str) -> Optional[List[float]]:
        """生成向量"""
        model = self._get_embed_model()
        if model is None:
            return None
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def _get_unprocessed_sessions(self, force: bool = False) -> List[dict]:
        """获取未处理会话"""
        try:
            result = subprocess.run(
                ["openclaw", "sessions", "list", "--limit", str(CONFIG["max_sessions"]), "--json"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode != 0:
                print(f"获取会话列表失败：{result.stderr}")
                return []
            
            sessions = json.loads(result.stdout)
            processed = set(self.state.get("processed_sessions", []))
            
            unprocessed = []
            for s in sessions:
                key = s.get("sessionKey") or s.get("key")
                if key and (force or key not in processed):
                    unprocessed.append({"sessionKey": key})
            
            return unprocessed
        except Exception as e:
            print(f"获取会话失败：{e}")
            return []
    
    def _get_session_history(self, session_key: str) -> List[dict]:
        """获取会话历史"""
        try:
            result = subprocess.run(
                ["openclaw", "sessions", "history", "--sessionKey", session_key, "--json"],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                return []
            
            data = json.loads(result.stdout)
            return data.get("messages", [])
        except Exception as e:
            print(f"获取会话历史失败：{e}")
            return []
    
    def _write_fragment(self, messages: List[dict], session_key: str) -> Dict[str, List[dict]]:
        """写入碎片，返回按小时分组的消息"""
        if not messages:
            return {}
        
        # 按小时分组
        by_hour = {}
        for msg in messages:
            ts_str = msg.get("timestamp", datetime.now().isoformat())
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except:
                ts = datetime.now()
            
            hour_key = ts.strftime("%Y-%m-%d-%H")
            if hour_key not in by_hour:
                by_hour[hour_key] = []
            by_hour[hour_key].append(msg)
        
        # 写入碎片文件
        for hour_key, msgs in by_hour.items():
            fragment_file = self.fragment_dir / f"{hour_key}.md"
            
            # 创建标题
            if not fragment_file.exists():
                title = datetime.strptime(hour_key, "%Y-%m-%d-%H").strftime("%Y年%m月%d日 %H:00")
                fragment_file.write_text(f"# {title}\n\n---\n\n", encoding="utf-8")
            
            # 追加内容
            parts = [f"## 会话 {session_key}\n\n"]
            for msg in msgs:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if not content:
                    continue
                
                msg_ts = msg.get("timestamp", "")
                try:
                    ts = datetime.fromisoformat(msg_ts.replace("Z", "+00:00"))
                    time_str = ts.strftime("%H:%M")
                except:
                    time_str = "??:??"
                
                role_map = {"user": "用户", "assistant": "助理", "system": "系统"}
                role_cn = role_map.get(role, role)
                
                parts.append(f"[{time_str}] **{role_cn}：** {content}\n\n")
            
            parts.append("---\n\n")
            
            with open(fragment_file, "a", encoding="utf-8") as f:
                f.write("".join(parts))
        
        return by_hour
    
    def _update_index_fragments(self, messages_by_hour: Dict[str, List[dict]]):
        """更新碎片消息的索引"""
        if self.collection is None:
            print("  跳过索引更新（ChromaDB 未初始化）")
            return
        
        for hour_key, msgs in messages_by_hour.items():
            for i, msg in enumerate(msgs):
                content = msg.get("content", "")
                if not content:
                    continue
                
                source = f"fragmentization/{hour_key}.md:{i}"
                embedding = self._embed(content)
                
                if embedding:
                    try:
                        self.collection.add(
                            documents=[content],
                            metadatas=[{"source": source, "type": "fragment"}],
                            embeddings=[embedding],
                            ids=[source]
                        )
                    except Exception as e:
                        print(f"    索引添加失败：{e}")
    
    def _update_frequent(self, results: List[dict], query: str):
        """更新检索计数"""
        distance_threshold = CONFIG["distance_threshold"]
        weights = CONFIG["weights"]
        
        for i, result in enumerate(results[:CONFIG["count_top_n"]]):
            distances = result.get("distances", [1.0])
            if distances and distances[0] >= distance_threshold:
                continue
            
            metas = result.get("metadatas", [{}])
            if not metas:
                continue
            
            source = metas[0].get("source", "")
            if not source:
                continue
            
            weight = weights[i] if i < len(weights) else 0.1
            
            if source not in self.frequent:
                self.frequent[source] = {
                    "score": 0,
                    "queries": [],
                    "message_content": result.get("documents", [""])[0],
                    "last_refined": None
                }
            
            self.frequent[source]["score"] += weight
            self.frequent[source]["queries"].append({
                "time": datetime.now().isoformat(),
                "query": query,
                "rank": i + 1,
                "weight": weight
            })
    
    def _check_refinement_needed(self) -> List[dict]:
        """检查需要提炼的记忆"""
        to_refine = []
        
        for source, data in self.frequent.items():
            if source.startswith("_"):
                continue
            
            if data.get("score", 0) >= CONFIG["refine_threshold"] and not data.get("last_refined"):
                to_refine.append({
                    "source": source,
                    "content": data.get("message_content", ""),
                    "score": data["score"]
                })
        
        return to_refine
    
    def _build_refinement_prompt(self, content: str) -> str:
        """构建 LLM 提炼提示词"""
        return f"""你是一个记忆整理助手。请分析对话，提取值得长期记住的信息。

## 类别定义

| 类别 | 说明 | 示例 |
|------|------|------|
| preferences | 偏好/习惯/喜欢/讨厌 | "用户喜欢吃辣" |
| todos | 待办事项/任务 | "用户需要买牛奶" |
| decisions | 重要决策 | "用户决定用 Python" |
| people | 人物/关系 | "用户的朋友张三" |
| projects | 项目/工作 | "用户在做开源项目" |

## 输出格式

有信息时：
```json
{{"category": "preferences", "content": "用户喜欢吃辣"}}
```

无信息时：
```json
null
```

## 示例

输入："我平时喜欢吃川菜，特别是麻婆豆腐"
输出：{{"category": "preferences", "content": "用户喜欢吃川菜，特别是麻婆豆腐"}}

输入："今天天气不错"
输出：null

输入："我决定了，就用这个方案"
输出：{{"category": "decisions", "content": "用户决定采用该方案"}}

## 对话内容

{content}
"""
    
    def _refine_with_llm(self, content: str) -> Optional[dict]:
        """调用 LLM 提炼（使用 OpenClaw agent）"""
        
        prompt = self._build_refinement_prompt(content)
        
        try:
            # 调用 OpenClaw agent
            result = subprocess.run(
                ["openclaw", "agent", "--message", prompt, "--json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"  LLM 调用失败：{result.stderr}")
                return None
            
            response = json.loads(result.stdout)
            llm_output = response.get("content", "") or response.get("message", "")
            
            # 解析 JSON 输出
            if llm_output.strip() == "null":
                return None
            
            # 尝试提取 JSON
            import re
            json_match = re.search(r'```json\s*({.*?})\s*```', llm_output, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # 直接解析
            return json.loads(llm_output)
            
        except Exception as e:
            print(f"  LLM 解析失败：{e}")
            return None
    
    def _append_to_palace(self, category: str, content: str):
        """追加到宫殿"""
        if category not in self.CATEGORIES:
            category = "preferences"  # 默认
        
        palace_file = self.palace_dir / f"{category}.md"
        
        # 读取现有内容
        if palace_file.exists():
            existing = palace_file.read_text(encoding="utf-8")
        else:
            existing = f"# {category.title()}\n\n_最后更新：{datetime.now().isoformat()}_\n\n---\n\n"
        
        # 追加新记录
        timestamp = datetime.now()
        new_entry = f"""## {timestamp.strftime("%Y-%m-%d %H:%M")}
{content}

---

"""
        
        # 更新最后更新时间
        existing = existing.replace(
            "_最后更新：", 
            f"_最后更新：{timestamp.isoformat()}_\n\n{new_entry}_"
        )
        
        palace_file.write_text(existing, encoding="utf-8")
    
    def _update_index_palace(self, category: str):
        """更新宫殿内容的索引"""
        if self.collection is None:
            return
        
        palace_file = self.palace_dir / f"{category}.md"
        if not palace_file.exists():
            return
        
        content = palace_file.read_text(encoding="utf-8")
        
        # 按段落分割（## 开头）
        sections = content.split("## ")[1:]  # 跳过标题
        
        for section in sections:
            lines = section.strip().split("\n")
            if len(lines) < 2:
                continue
            
            # 提取时间行和内容
            time_line = lines[0].strip()
            content_lines = [l for l in lines[1:] if l.strip() and not l.strip().startswith("---")]
            para_content = "\n".join(content_lines)
            
            if len(para_content) < 10:
                continue
            
            source = f"palace/{category}.md:{time_line}"
            embedding = self._embed(para_content)
            
            if embedding:
                try:
                    self.collection.add(
                        documents=[para_content],
                        metadatas=[{"source": source, "type": "palace", "category": category}],
                        embeddings=[embedding],
                        ids=[source]
                    )
                except:
                    pass
    
    def _cleanup_frequent(self):
        """清理过期计数"""
        cutoff = datetime.now() - timedelta(days=CONFIG["window_days"])
        
        for source in list(self.frequent.keys()):
            if source.startswith("_"):
                continue
            
            data = self.frequent[source]
            valid_queries = []
            
            for q in data.get("queries", []):
                try:
                    q_time = datetime.fromisoformat(q["time"])
                    if q_time > cutoff:
                        valid_queries.append(q)
                except:
                    pass
            
            if valid_queries:
                data["queries"] = valid_queries
                data["score"] = sum(q.get("weight", 0) for q in valid_queries)
            else:
                del self.frequent[source]
    
    def consolidate(self, dry_run: bool = False, force: bool = False):
        """执行心跳整理"""
        print("开始心跳整理...")
        print(f"工作目录：{self.workspace}")
        print()
        
        # 1. 读取未处理会话
        sessions = self._get_unprocessed_sessions(force=force)
        print(f"发现 {len(sessions)} 个待处理会话")
        
        if not sessions:
            print("没有需要处理的会话")
            return
        
        # 2. 写入碎片
        print("\n1. 写入碎片...")
        all_messages_by_hour = {}
        
        for session in sessions:
            session_key = session["sessionKey"]
            print(f"  处理会话：{session_key}")
            
            messages = self._get_session_history(session_key)
            if not messages:
                print(f"    无消息，跳过")
                continue
            
            by_hour = self._write_fragment(messages, session_key)
            
            # 合并
            for hour_key, msgs in by_hour.items():
                if hour_key not in all_messages_by_hour:
                    all_messages_by_hour[hour_key] = []
                all_messages_by_hour[hour_key].extend(msgs)
            
            if not dry_run:
                self.state["processed_sessions"].append(session_key)
        
        # 3. 更新索引（碎片）
        print("\n2. 更新索引（碎片）...")
        self._update_index_fragments(all_messages_by_hour)
        
        # 4. 检查高频记忆
        print("\n3. 检查高频记忆...")
        to_refine = self._check_refinement_needed()
        print(f"  发现 {len(to_refine)} 条需要提炼的记忆")
        
        # 5. 批量 LLM 提炼
        print("\n4. LLM 提炼...")
        for i in range(0, len(to_refine), CONFIG["llm_batch_size"]):
            batch = to_refine[i:i+CONFIG["llm_batch_size"]]
            batch_num = i // CONFIG["llm_batch_size"] + 1
            print(f"  批次 {batch_num}: {len(batch)} 条")
            
            for item in batch:
                result = self._refine_with_llm(item["content"])
                
                if result and result.get("category"):
                    if dry_run:
                        print(f"    [预览] {result['category']}: {result['content'][:50]}...")
                    else:
                        self._append_to_palace(result["category"], result["content"])
                        # 标记已提炼
                        source = item["source"]
                        if source in self.frequent:
                            self.frequent[source]["last_refined"] = datetime.now().isoformat()
        
        # 6. 更新索引（宫殿）
        print("\n5. 更新索引（宫殿）...")
        for cat in self.CATEGORIES:
            self._update_index_palace(cat)
        
        # 7. 清理过期计数
        print("\n6. 清理过期计数...")
        self._cleanup_frequent()
        
        # 保存
        if not dry_run:
            self._save_state()
            self._save_frequent()
        
        print("\n整理完成！")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="心跳整理脚本")
    parser.add_argument("--dry-run", action="store_true", help="预览模式")
    parser.add_argument("--force", action="store_true", help="强制重新处理")
    parser.add_argument("--workspace", default=os.environ.get("WORKSPACE_ROOT", "/home/node/.openclaw/workspace"))
    
    args = parser.parse_args()
    
    consolidator = MemoryConsolidator(args.workspace)
    consolidator.consolidate(dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()
