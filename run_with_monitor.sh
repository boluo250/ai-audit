#!/bin/bash
# LLM API调用监控辅助脚本
# 同时启动资源监控和程序，便于分析API调用卡住时的资源状态

set -e

# 配置
LOG_DIR="logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
MONITOR_LOG="$LOG_DIR/resource_monitor_$TIMESTAMP.log"
APP_LOG="$LOG_DIR/app_with_monitor_$TIMESTAMP.log"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

echo "=== LLM API监控启动脚本 ==="
echo "时间: $(date)"
echo "监控日志: $MONITOR_LOG"
echo "应用日志: $APP_LOG"
echo

# 检查Python环境
if [ ! -d "venv" ]; then
    echo "警告: 虚拟环境不存在，使用系统Python"
else
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

# 检查psutil依赖
if ! python3 -c "import psutil" 2>/dev/null; then
    echo "安装psutil依赖..."
    pip install psutil
fi

echo "启动资源监控 (后台运行)..."
python3 monitor_resources.py --interval 1 --log "$MONITOR_LOG" &
MONITOR_PID=$!

echo "监控进程PID: $MONITOR_PID"
echo

# 清理函数
cleanup() {
    echo
    echo "=== 清理进程 ==="
    if kill -0 $MONITOR_PID 2>/dev/null; then
        echo "停止资源监控进程 ($MONITOR_PID)"
        kill $MONITOR_PID
    fi
    
    echo "监控数据已保存到: $MONITOR_LOG"
    echo "应用日志已保存到: $APP_LOG"
    
    # 显示最后几行监控数据的摘要
    if [ -f "$MONITOR_LOG" ]; then
        echo
        echo "=== 最终资源状态摘要 ==="
        tail -3 "$MONITOR_LOG" | while read line; do
            echo "$line" | python3 -c "
import json, sys
try:
    data = json.loads(sys.stdin.read())
    sys_data = data['system']
    print(f\"时间: {sys_data['timestamp']}\")
    print(f\"CPU: {sys_data['cpu_percent']}% | Memory: {sys_data['memory_percent']}% | Disk: {sys_data['disk_percent']}%\")
    if data['processes']:
        print(f\"Python进程数: {len(data['processes'])}\")
        for pid, proc in data['processes'].items():
            if proc['memory_mb'] > 100:  # 只显示内存占用大的进程
                print(f\"  PID {pid}: {proc['memory_mb']:.1f}MB, CPU: {proc['cpu_percent']:.1f}%\")
    print('---')
except:
    pass
"
        done
    fi
    
    exit 0
}

# 注册信号处理
trap cleanup INT TERM

echo "启动应用程序..."
echo "提示: 当API调用卡住时，资源监控会记录当时的系统状态"
echo "按 Ctrl+C 停止监控和应用"
echo

# 启动主程序并记录日志
python3 src/main.py 2>&1 | tee "$APP_LOG"

# 如果程序正常退出，也执行清理
cleanup