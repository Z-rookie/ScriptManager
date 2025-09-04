#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import signal
import argparse
import subprocess
import time
from datetime import datetime
import psutil
import uuid
import tabulate

CONFIG_DIR = os.path.expanduser("~/.script_manager")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
LOG_DIR = os.path.join(CONFIG_DIR, "logs")

def ensure_dirs():
    """确保配置目录和日志目录存在"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

def load_config():
    """加载配置文件"""
    if not os.path.exists(CONFIG_FILE):
        return {"scripts": {}}
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    """保存配置文件"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def generate_id():
    """生成唯一ID"""
    return str(uuid.uuid4())[:8]

def get_script_status(pid):
    """获取脚本运行状态"""
    if not pid:
        return "stopped"
    try:
        process = psutil.Process(pid)
        return "running" if process.is_running() else "stopped"
    except psutil.NoSuchProcess:
        return "stopped"

def get_process_ports(pid):
    """获取进程占用的端口"""
    if not pid:
        return ""
        
    try:
        # 获取进程及其子进程的PID列表
        pids = [str(pid)]
        try:
            process = psutil.Process(pid)
            for child in process.children(recursive=True):
                pids.append(str(child.pid))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        
        # 使用ss命令检测端口
        result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
        if result.returncode == 0:
            ports = []
            for line in result.stdout.splitlines():
                if 'LISTEN' in line:
                    # 检查是否包含任何相关的PID
                    for p in pids:
                        if f'pid={p}' in line:
                            parts = line.split()
                            if len(parts) >= 4:
                                addr = parts[3]
                                if ':' in addr:
                                    port_str = addr.split(':')[-1]
                                    try:
                                        port = int(port_str)
                                        ports.append(port)
                                    except ValueError:
                                        pass
                            break
            
            if ports:
                ports = sorted(list(set(ports)))
                if len(ports) == 1:
                    return str(ports[0])
                elif len(ports) <= 3:
                    return ",".join(map(str, ports))
                else:
                    return f"{ports[0]},+{len(ports)-1}more"
    except Exception:
        pass
    
    return ""

def list_scripts(args):
    """列出所有注册的脚本"""
    config = load_config()
    scripts = config.get("scripts", {})
    
    if not scripts:
        print("没有注册的脚本")
        return
    
    table_data = []
    headers = ["ID", "名称", "命令", "工作目录", "状态", "PID", "端口", "创建时间"]
    
    for script_id, script in scripts.items():
        pid = script.get("pid", 0)
        status = get_script_status(pid)
        
        # 获取端口信息
        ports_str = ""
        if status == "running" and pid:
            ports_str = get_process_ports(pid)
        
        table_data.append([
            script_id,
            script.get("name", ""),
            script.get("command", ""),
            script.get("working_dir", ""),
            status,
            str(pid) if status == "running" else "",
            ports_str,
            script.get("created_at", "")
        ])
    
    print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))

def start_script(args):
    """启动脚本"""
    config = load_config()
    scripts = config.get("scripts", {})
    
    if args.id not in scripts:
        print(f"找不到ID为 {args.id} 的脚本")
        return
    
    script = scripts[args.id]
    
    # 检查脚本是否已在运行
    if script.get("pid") and get_script_status(script.get("pid")) == "running":
        print(f"脚本 {args.id} 已经在运行中")
        return
    
    # 启动脚本
    log_file = open(script["log_file"], "a")
    process = subprocess.Popen(
        script["command"],
        shell=True,
        stdout=log_file,
        stderr=log_file,
        cwd=script["working_dir"],
        start_new_session=True
    )
    
    # 更新配置
    script["pid"] = process.pid
    script["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_config(config)
    
    print(f"脚本 {args.id} 已启动，PID: {process.pid}")
    print(f"日志文件: {script['log_file']}")

def stop_script(args):
    """停止脚本"""
    config = load_config()
    scripts = config.get("scripts", {})
    
    if args.id not in scripts:
        print(f"找不到ID为 {args.id} 的脚本")
        return
    
    script = scripts[args.id]
    pid = script.get("pid")
    
    if not pid or get_script_status(pid) == "stopped":
        print(f"脚本 {args.id} 未在运行")
        return
    
    try:
        # 发送终止信号给进程组
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        
        # 等待进程终止
        for _ in range(5):
            if get_script_status(pid) == "stopped":
                break
            time.sleep(1)
        
        # 如果进程仍在运行，强制终止
        if get_script_status(pid) == "running":
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        
        print(f"脚本 {args.id} 已停止")
    except ProcessLookupError:
        print(f"进程 {pid} 不存在")
    except Exception as e:
        print(f"停止脚本时出错: {e}")
    
    # 更新配置
    script["pid"] = None
    save_config(config)

def restart_script(args):
    """重启脚本"""
    stop_args = argparse.Namespace(id=args.id)
    stop_script(stop_args)
    
    # 短暂延迟确保进程完全终止
    time.sleep(1)
    
    start_args = argparse.Namespace(id=args.id)
    start_script(start_args)

def remove_script(args):
    """删除脚本"""
    config = load_config()
    scripts = config.get("scripts", {})
    
    if args.id not in scripts:
        print(f"找不到ID为 {args.id} 的脚本")
        return
    
    script = scripts[args.id]
    
    # 如果脚本正在运行，先停止它
    if script.get("pid") and get_script_status(script.get("pid")) == "running":
        stop_args = argparse.Namespace(id=args.id)
        stop_script(stop_args)
    
    # 删除日志文件
    log_file = script.get("log_file")
    if log_file and os.path.exists(log_file):
        os.remove(log_file)
    
    # 从配置中删除
    del scripts[args.id]
    save_config(config)
    
    print(f"脚本 {args.id} 已删除")

def view_logs(args):
    """查看脚本日志"""
    config = load_config()
    scripts = config.get("scripts", {})
    
    if args.id not in scripts:
        print(f"找不到ID为 {args.id} 的脚本")
        return
    
    script = scripts[args.id]
    log_file = script.get("log_file")
    
    if not log_file or not os.path.exists(log_file):
        print(f"脚本 {args.id} 没有日志文件")
        return
    
    # 使用tail命令查看日志
    lines = args.lines or 10
    subprocess.run(["tail", "-n", str(lines), log_file])

def run_script_directly(args):
    """直接运行脚本并在后台管理"""
    # 生成一个唯一ID
    script_id = generate_id()
    
    # 确定脚本路径
    script_path = args.script_path
    
    # 如果路径不是绝对路径，检查当前目录
    if not os.path.isabs(script_path):
        # 首先检查当前目录
        current_dir_path = os.path.join(os.getcwd(), script_path)
        if os.path.exists(current_dir_path):
            script_path = current_dir_path
        elif os.path.exists(script_path):
            # 如果相对路径存在，使用绝对路径
            script_path = os.path.abspath(script_path)
        else:
            # 文件不存在，提示错误
            print(f"错误: 找不到文件 '{args.script_path}'")
            print(f"已检查路径:")
            print(f"  - 当前目录: {current_dir_path}")
            print(f"  - 相对路径: {os.path.abspath(script_path)}")
            return None
    else:
        # 绝对路径，直接检查是否存在
        if not os.path.exists(script_path):
            print(f"错误: 找不到文件 '{script_path}'")
            return None
    
    # 确定脚本名称
    script_name = os.path.basename(script_path)
    
    # 确定工作目录
    working_dir = args.working_dir or os.path.dirname(os.path.abspath(script_path))
    if not working_dir:
        working_dir = os.getcwd()
    
    # 构建完整命令
    if script_path.endswith('.py'):
        command = f"python3 {script_path}"
    elif script_path.endswith('.js'):
        command = f"node {script_path}"
    elif script_path.endswith('.go'):
        command = f"go run {script_path}"
    elif script_path.endswith('.sh'):
        command = f"bash {script_path}"
    else:
        # 尝试直接执行
        command = script_path
    
    # 添加额外的参数
    if args.args:
        command += f" {args.args}"
    
    # 加载配置
    config = load_config()
    
    # 创建脚本信息
    script_info = {
        "name": script_name,
        "command": command,
        "working_dir": working_dir,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pid": None,
        "log_file": os.path.join(LOG_DIR, f"{script_id}.log")
    }
    
    # 保存到配置
    config["scripts"][script_id] = script_info
    save_config(config)
    
    print(f"脚本已注册，ID: {script_id}")
    print(f"脚本路径: {script_path}")
    
    # 直接启动脚本
    start_args = argparse.Namespace(id=script_id)
    start_script(start_args)
    
    return script_id

def show_help(args):
    """显示帮助信息"""
    help_text = """
ScriptManager (sm) - 脚本管理器

用法:
  sm <script_path> [args]           直接运行脚本
  sm ps                            列出所有脚本
  sm start <id>                    启动脚本
  sm stop <id>                     停止脚本
  sm restart <id>                  重启脚本
  sm rm <id>                       删除脚本
  sm logs <id> [-n lines]          查看脚本日志
  sm help                          显示此帮助信息

示例:
  sm /path/to/script.py            直接运行Python脚本
  sm script.py "arg1 arg2"         带参数运行脚本
  sm ps                            查看所有脚本状态
  sm stop abc123                   停止ID为abc123的脚本
  sm logs abc123 -n 50             查看脚本最后50行日志
"""
    print(help_text)

def main():
    """主函数"""
    ensure_dirs()
    
    # 检查是否是直接运行脚本的情况
    if len(sys.argv) > 1 and not sys.argv[1] in ['help', 'ps', 'start', 'stop', 'restart', 'rm', 'logs']:
        # 直接运行脚本模式
        parser = argparse.ArgumentParser(description="脚本管理器 - 直接运行脚本")
        parser.add_argument("script_path", help="要运行的脚本路径")
        parser.add_argument("args", nargs="?", help="脚本的参数")
        parser.add_argument("--working-dir", help="脚本工作目录")
        
        args = parser.parse_args()
        run_script_directly(args)
        return
    
    # 命令模式
    parser = argparse.ArgumentParser(description="脚本管理器 - 管理服务器上运行的脚本")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # help命令
    help_parser = subparsers.add_parser("help", help="显示帮助信息")
    help_parser.set_defaults(func=show_help)
    
    # ps命令
    ps_parser = subparsers.add_parser("ps", help="列出所有脚本")
    ps_parser.set_defaults(func=list_scripts)
    
    # start命令
    start_parser = subparsers.add_parser("start", help="启动脚本")
    start_parser.add_argument("id", help="脚本ID")
    start_parser.set_defaults(func=start_script)
    
    # stop命令
    stop_parser = subparsers.add_parser("stop", help="停止脚本")
    stop_parser.add_argument("id", help="脚本ID")
    stop_parser.set_defaults(func=stop_script)
    
    # restart命令
    restart_parser = subparsers.add_parser("restart", help="重启脚本")
    restart_parser.add_argument("id", help="脚本ID")
    restart_parser.set_defaults(func=restart_script)
    
    # rm命令
    rm_parser = subparsers.add_parser("rm", help="删除脚本")
    rm_parser.add_argument("id", help="脚本ID")
    rm_parser.set_defaults(func=remove_script)
    
    # logs命令
    logs_parser = subparsers.add_parser("logs", help="查看脚本日志")
    logs_parser.add_argument("id", help="脚本ID")
    logs_parser.add_argument("-n", "--lines", type=int, help="显示的行数")
    logs_parser.set_defaults(func=view_logs)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)

if __name__ == "__main__":
    main()