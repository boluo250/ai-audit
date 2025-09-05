#!/usr/bin/env python3
"""
资源监控脚本 - 监控系统和进程资源使用情况
当LLM API调用卡住时，帮助分析可能的资源瓶颈
"""

import psutil
import time
import os
import sys
import json
from datetime import datetime
import threading
import signal


class ResourceMonitor:
    def __init__(self, interval=2, log_file=None):
        self.interval = interval
        self.log_file = log_file
        self.running = False
        self.python_processes = []
        
    def get_system_resources(self):
        """获取系统资源使用情况"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': round(memory.total / 1024**3, 2),
            'memory_used_gb': round(memory.used / 1024**3, 2),
            'memory_percent': memory.percent,
            'memory_available_gb': round(memory.available / 1024**3, 2),
            'disk_total_gb': round(disk.total / 1024**3, 2),
            'disk_used_gb': round(disk.used / 1024**3, 2),
            'disk_percent': round((disk.used / disk.total) * 100, 2),
            'network_bytes_sent': network.bytes_sent,
            'network_bytes_recv': network.bytes_recv,
            'network_packets_sent': network.packets_sent,
            'network_packets_recv': network.packets_recv
        }
    
    def get_process_info(self, pid):
        """获取特定进程的资源使用情况"""
        try:
            process = psutil.Process(pid)
            with process.oneshot():
                return {
                    'pid': pid,
                    'name': process.name(),
                    'status': process.status(),
                    'cpu_percent': process.cpu_percent(),
                    'memory_mb': round(process.memory_info().rss / 1024**2, 2),
                    'memory_percent': process.memory_percent(),
                    'num_threads': process.num_threads(),
                    'num_fds': process.num_fds() if hasattr(process, 'num_fds') else 'N/A',
                    'connections': len(process.connections()) if process.connections() else 0,
                    'cmdline': ' '.join(process.cmdline()[:3])  # 只显示前3个参数避免过长
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
    
    def find_python_processes(self):
        """查找所有Python相关进程"""
        python_procs = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and ('python' in proc.info['name'].lower() or 
                                        (proc.info['cmdline'] and any('python' in arg.lower() for arg in proc.info['cmdline']))):
                    python_procs.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return python_procs
    
    def monitor_once(self):
        """执行一次监控"""
        data = {
            'system': self.get_system_resources(),
            'processes': {}
        }
        
        # 监控Python进程
        python_pids = self.find_python_processes()
        for pid in python_pids:
            proc_info = self.get_process_info(pid)
            if proc_info:
                data['processes'][pid] = proc_info
        
        return data
    
    def print_summary(self, data):
        """打印监控摘要"""
        sys_data = data['system']
        print(f"\n=== {sys_data['timestamp']} ===")
        print(f"CPU: {sys_data['cpu_percent']}% | "
              f"Memory: {sys_data['memory_percent']}% "
              f"({sys_data['memory_used_gb']:.1f}GB/{sys_data['memory_total_gb']:.1f}GB) | "
              f"Disk: {sys_data['disk_percent']}%")
        
        if data['processes']:
            print("\nPython进程:")
            for pid, proc in data['processes'].items():
                print(f"  PID {pid}: {proc['name']} | "
                      f"CPU: {proc['cpu_percent']:.1f}% | "
                      f"Memory: {proc['memory_mb']:.1f}MB ({proc['memory_percent']:.1f}%) | "
                      f"线程: {proc['num_threads']} | "
                      f"连接: {proc['connections']} | "
                      f"状态: {proc['status']}")
                print(f"    命令: {proc['cmdline']}")
    
    def log_data(self, data):
        """记录数据到文件"""
        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    def start_monitoring(self):
        """开始持续监控"""
        self.running = True
        print(f"开始资源监控 (间隔: {self.interval}秒)")
        print("按 Ctrl+C 停止监控")
        
        if self.log_file:
            print(f"日志文件: {self.log_file}")
        
        try:
            while self.running:
                data = self.monitor_once()
                self.print_summary(data)
                self.log_data(data)
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\n监控已停止")
            self.running = False
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False


def signal_handler(sig, frame):
    print("\n接收到停止信号，正在退出...")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    import argparse
    parser = argparse.ArgumentParser(description='系统资源监控工具')
    parser.add_argument('--interval', '-i', type=int, default=2, help='监控间隔(秒), 默认2秒')
    parser.add_argument('--log', '-l', type=str, help='日志文件路径')
    parser.add_argument('--once', action='store_true', help='只执行一次监控')
    
    args = parser.parse_args()
    
    monitor = ResourceMonitor(interval=args.interval, log_file=args.log)
    
    if args.once:
        data = monitor.monitor_once()
        monitor.print_summary(data)
        monitor.log_data(data)
    else:
        monitor.start_monitoring()


if __name__ == '__main__':
    main()