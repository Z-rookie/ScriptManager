#!/bin/bash

# 脚本管理器安装脚本

echo "开始安装ScriptManager..."

# 检查Python是否已安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查pip是否已安装
if ! command -v pip3 &> /dev/null; then
    echo "错误: 未找到pip3，请先安装pip"
    exit 1
fi

# 获取当前目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 安装依赖
echo "安装依赖..."
pip3 install -r "$SCRIPT_DIR/requirements.txt"

# 安装ScriptManager
echo "安装ScriptManager..."
pip3 install -e "$SCRIPT_DIR"

# 设置可执行权限
chmod +x "$SCRIPT_DIR/script_manager.py"

# 创建配置目录
mkdir -p ~/.script_manager/logs

echo "ScriptManager安装完成！"
echo "使用方法: sm [command]"
echo "例如: sm help"
echo "      sm /path/to/script.py"
echo "      sm ps"
echo "      sm start <script_id>"