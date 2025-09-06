qing# ScriptManager (sm) - 脚本管理器

一个用于管理和监控服务器上运行脚本的命令行工具。

## 功能特性

- 🚀 直接运行脚本并在后台管理
- 📊 查看所有脚本的运行状态
- 🔄 启动、停止、重启脚本
- 📝 查看脚本运行日志
- 🗂️ 自动识别脚本类型（Python、Node.js、Go、Shell等）
- 📍 智能路径识别，优先查找当前目录下的文件

## 安装

### 方法1: 使用安装脚本（推荐）

```bash
# 克隆或下载项目到本地
cd /path/to/ScriptManager

# 运行安装脚本
chmod +x install.sh
./install.sh
```

安装脚本会自动：
- 检查Python3和pip3是否已安装
- 安装所需的依赖包（psutil, tabulate）
- 设置可执行权限
- 创建配置目录

### 方法2: 手动安装

1. 确保系统已安装Python 3和所需依赖：
```bash
pip3 install psutil tabulate
```

2. 将脚本复制到系统路径或创建软链接：
```bash
# 方法2a: 复制到系统路径
sudo cp script_manager.py /usr/local/bin/sm
sudo chmod +x /usr/local/bin/sm

# 方法2b: 创建软链接
sudo ln -s /path/to/script_manager.py /usr/local/bin/sm
```

## 使用方法

### 基本命令

```bash
# 直接运行脚本（优先查找当前目录）
sm script.py
sm my_script.js
sm ./server.py "arg1 arg2"

# 查看所有脚本状态
sm ps

# 启动脚本
sm start <script_id>

# 停止脚本
sm stop <script_id>

# 重启脚本
sm restart <script_id>

# 删除脚本
sm rm <script_id>

# 查看脚本日志
sm logs <script_id>
sm logs <script_id> -n 50  # 查看最后50行

# 显示帮助
sm help
```

### 使用示例

```bash
# 运行当前目录下的Python脚本
sm app.py

# 运行带参数的脚本
sm server.py "--port 8080 --debug"

# 查看所有运行中的脚本
sm ps

# 停止特定脚本
sm stop abc12345

# 查看脚本日志
sm logs abc12345 -n 100
```

## 路径识别规则

ScriptManager 会按以下顺序查找脚本文件：

1. **当前目录优先**: 首先在当前工作目录中查找指定的文件
2. **相对路径**: 如果当前目录没找到，尝试相对路径
3. **绝对路径**: 如果提供的是绝对路径，直接使用
4. **错误提示**: 如果所有路径都找不到文件，显示详细的错误信息

## 支持的脚本类型

- **Python** (`.py`): 使用 `python3` 执行
- **JavaScript** (`.js`): 使用 `node` 执行
- **Go** (`.go`): 使用 `go run` 执行
- **Shell** (`.sh`): 使用 `bash` 执行
- **其他**: 尝试直接执行

## 配置文件位置

- 配置目录: `~/.script_manager/`
- 配置文件: `~/.script_manager/config.json`
- 日志目录: `~/.script_manager/logs/`

## 卸载方法

### 完全卸载 ScriptManager

1. **停止所有运行中的脚本**：
```bash
# 查看所有脚本
sm ps

# 停止所有运行中的脚本
sm stop <script_id1>
sm stop <script_id2>
# ... 对每个运行中的脚本执行停止操作
```

2. **删除系统命令**：
```bash
# 如果使用复制方式安装
sudo rm /usr/local/bin/sm

# 如果使用软链接方式安装
sudo rm /usr/local/bin/sm
```

3. **删除配置文件和日志**：
```bash
# 删除所有配置文件、日志和数据
rm -rf ~/.script_manager/
```

4. **删除源文件**（可选）：
```bash
# 删除脚本管理器源文件
rm -rf /path/to/ScriptManager/
```

### 快速卸载脚本

```bash
#!/bin/bash
# 创建卸载脚本 uninstall_sm.sh

echo "正在卸载 ScriptManager..."

# 停止所有脚本（如果sm命令还可用）
if command -v sm &> /dev/null; then
    echo "停止所有运行中的脚本..."
    sm ps --quiet 2>/dev/null | tail -n +2 | awk '{print $1}' | xargs -I {} sm stop {} 2>/dev/null
fi

# 删除系统命令
echo "删除系统命令..."
sudo rm -f /usr/local/bin/sm

# 删除配置文件
echo "删除配置文件和日志..."
rm -rf ~/.script_manager/

echo "ScriptManager 已完全卸载！"
```

使用方法：
```bash
chmod +x uninstall_sm.sh
./uninstall_sm.sh
```

## 注意事项

- 脚本会在后台运行，即使终端关闭也会继续执行
- 所有脚本的输出都会记录到日志文件中
- 删除脚本时会自动停止运行中的进程并清理日志文件
- 建议定期清理不需要的脚本以释放系统资源

## 故障排除

### 常见问题

1. **权限错误**: 确保脚本文件有执行权限
```bash
chmod +x your_script.py
```

2. **找不到命令**: 检查依赖是否安装
```bash
# 检查Python
python3 --version

# 检查Node.js
node --version

# 安装依赖
pip3 install psutil tabulate
```

3. **脚本无法启动**: 检查脚本路径和语法是否正确

4. **日志文件过大**: 定期清理日志文件
```bash
# 清理特定脚本的日志
> ~/.script_manager/logs/<script_id>.log

# 或删除所有日志
rm ~/.script_manager/logs/*.log
```

## 版本信息

- 版本: 1.0.0
- 作者: ScriptManager Team
- 许可证: MIT

## 更新日志

### v1.0.0
- 初始版本发布
- 支持多种脚本类型
- 智能路径识别
- 完整的脚本生命周期管理