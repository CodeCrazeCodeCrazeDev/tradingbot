import os
import time
import psutil
import subprocess
import gc
from datetime import datetime

WATCHDOG_INTERVAL = 300  # 5 minutes
MEM_CLEANUP_INTERVAL = 3600  # 1 hour
READINESS_REPORT_INTERVAL = 21600  # 6 hours
CRASH_LOG = 'bot_crash_log.txt'
BOT_CMD = ['py', 'main.py', '--mode', 'paper', '--symbol', 'EURUSD']
MIN_FREE_RAM_MB = 512  # Reduced threshold for constrained environments


def log_crash(reason, module=None):
    with open(CRASH_LOG, 'a') as f:
        f.write(f"{datetime.now()} | {reason} | Module: {module or 'N/A'}\n")

def get_free_ram_mb():
    return psutil.virtual_memory().available // (1024 * 1024)

def cleanup_memory():
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass

def cleanup_temp():
    tmp = os.getenv('TEMP', '/tmp')
    for root, dirs, files in os.walk(tmp):
        for file in files:
            try:
                os.remove(os.path.join(root, file))
            except Exception:
                pass

def is_oom(exit_code, output):
    return exit_code == -536870904 or 'OOM' in output or 'MemoryError' in output

def run_bot():
    env = os.environ.copy()
    process = subprocess.Popen(BOT_CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, encoding='utf-8')
    return process

def check_bot_ready():
    # Placeholder: implement actual health checks (API, log, etc.)
    return True

def main():
    last_mem_cleanup = time.time()
    last_readiness_report = time.time()
    bot_proc = None
    while True:
        if get_free_ram_mb() < MIN_FREE_RAM_MB:
            log_crash('Low RAM, delaying bot launch')
            cleanup_memory()
            cleanup_temp()
            time.sleep(60)
            continue
        if not bot_proc or bot_proc.poll() is not None:
            if bot_proc:
                out, err = bot_proc.communicate()
                exit_code = bot_proc.returncode
                output = (out or b'').decode(errors='ignore') + (err or b'').decode(errors='ignore')
                reason = 'OOM' if is_oom(exit_code, output) else f'Crash code {exit_code}'
                log_crash(reason, module='main.py')
                cleanup_memory()
                cleanup_temp()
                time.sleep(10)
            bot_proc = run_bot()
            time.sleep(5)
            if not check_bot_ready():
                log_crash('Health check failed after restart')
        # Periodic memory cleanup
        if time.time() - last_mem_cleanup > MEM_CLEANUP_INTERVAL:
            cleanup_memory()
            last_mem_cleanup = time.time()
        # Periodic readiness report
        if time.time() - last_readiness_report > READINESS_REPORT_INTERVAL:
            with open('readiness_report.txt', 'a') as f:
                f.write(f'{datetime.now()} | BOT READY: {check_bot_ready()} | Free RAM: {get_free_ram_mb()} MB\n')
            last_readiness_report = time.time()
        time.sleep(WATCHDOG_INTERVAL)

if __name__ == '__main__':
    main()
