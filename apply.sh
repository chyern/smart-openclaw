#!/bin/bash

# apply.sh - 将本项目中的 AGENTS.md 和 SOUL.md 应用到 workspace 根目录

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== smart-openclaw 设定文件应用工具 ===${NC}"
echo "将本项目中的 AGENTS.md 和 SOUL.md 覆盖到 workspace 根目录"
echo ""

# 检查源文件是否存在
SOURCE_DIR="$(dirname "$0")"
AGENTS_SOURCE="$SOURCE_DIR/AGENTS.md"
SOUL_SOURCE="$SOURCE_DIR/SOUL.md"

if [[ ! -f "$AGENTS_SOURCE" ]]; then
    echo -e "${RED}错误: 找不到源文件 $AGENTS_SOURCE${NC}"
    exit 1
fi

if [[ ! -f "$SOUL_SOURCE" ]]; then
    echo -e "${RED}错误: 找不到源文件 $SOUL_SOURCE${NC}"
    exit 1
fi

# 定义目标路径
WORKSPACE_ROOT="$HOME/.openclaw/workspace"
AGENTS_TARGET="$WORKSPACE_ROOT/AGENTS.md"
SOUL_TARGET="$WORKSPACE_ROOT/SOUL.md"

echo -e "${YELLOW}源目录:${NC} $SOURCE_DIR"
echo -e "${YELLOW}目标目录:${NC} $WORKSPACE_ROOT"
echo ""

# 创建备份目录结构
BACKUP_ROOT="$WORKSPACE_ROOT/backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"

echo -e "${YELLOW}创建备份目录:${NC} $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# 备份文件函数
backup_file() {
    local target_file="$1"
    local filename=$(basename "$target_file")
    
    if [[ -f "$target_file" ]]; then
        cp "$target_file" "$BACKUP_DIR/$filename"
        echo -e "${YELLOW}备份:${NC} $filename → $BACKUP_DIR/"
    else
        echo -e "${YELLOW}提示:${NC} $filename 不存在，无需备份"
    fi
}

# 备份原文件
backup_file "$AGENTS_TARGET"
backup_file "$SOUL_TARGET"

echo ""

# 复制文件
echo -e "${GREEN}正在复制文件...${NC}"
cp "$AGENTS_SOURCE" "$AGENTS_TARGET"
echo "✅ 复制 AGENTS.md"

cp "$SOUL_SOURCE" "$SOUL_TARGET"
echo "✅ 复制 SOUL.md"

echo ""
echo -e "${GREEN}=== 完成！ ===${NC}"
echo "AGENTS.md 和 SOUL.md 已成功应用到 workspace 根目录"
echo -e "${YELLOW}备份文件保存在:${NC} $BACKUP_DIR"
echo ""
echo "下次启动 OpenClaw 时会使用新的设定文件。"