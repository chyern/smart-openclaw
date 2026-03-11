#!/usr/bin/env python3
"""
Memory Skill - 碎片记录脚本

将对话内容追加到记忆碎片文件（按小时分割）。

用法:
    python fragmentize.py "会话内容" --session-key abc123
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime


def get_fragment_file(fragment_dir: Path, timestamp: datetime) -> Path:
    """获取（或创建）当前小时的碎片文件"""
    filename = timestamp.strftime("%Y-%m-%d-%H.md")
    file_path = fragment_dir / filename
    
    fragment_dir.mkdir(parents=True, exist_ok=True)
    
    if not file_path.exists():
        title = timestamp.strftime("%Y年%m月%d日 %H:00")
        file_path.write_text(f"# {title}\n\n---\n\n", encoding="utf-8")
    
    return file_path


def append_to_fragment(fragment_dir: Path, messages: list, session_key: str) -> int:
    """追加消息到碎片文件"""
    if not messages:
        return 0
    
    first_msg = messages[0]
    timestamp_str = first_msg.get("timestamp", datetime.now().isoformat())
    
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except:
        timestamp = datetime.now()
    
    fragment_file = get_fragment_file(fragment_dir, timestamp)
    
    parts = [f"## 会话 {session_key}\n\n"]
    
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        
        if not content:
            continue
        
        msg_timestamp = msg.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(msg_timestamp.replace("Z", "+00:00"))
            time_str = ts.strftime("%H:%M")
        except:
            time_str = "??:??"
        
        role_map = {"user": "用户", "assistant": "助理", "system": "系统"}
        role_cn = role_map.get(role, role)
        
        parts.append(f"[{time_str}] **{role_cn}：** {content}\n\n")
    
    parts.append("---\n\n")
    
    with open(fragment_file, "a", encoding="utf-8") as f:
        f.write("".join(parts))
    
    return len(messages)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="碎片记录脚本")
    parser.add_argument("content", nargs="?", help="要记录的内容")
    parser.add_argument("--session-key", help="会话 ID")
    parser.add_argument("--workspace", default=os.environ.get("WORKSPACE_ROOT", "/home/node/.openclaw/workspace"))
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace)
    memory_dir = workspace / "memory"
    fragment_dir = memory_dir / "fragmentization"
    
    if args.content and args.session_key:
        messages = [{
            "role": "user",
            "content": args.content,
            "timestamp": datetime.now().isoformat()
        }]
        count = append_to_fragment(fragment_dir, messages, args.session_key)
        print(f"已追加 {count} 条消息到碎片")
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
