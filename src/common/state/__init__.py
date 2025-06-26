import time

import psutil

start_time = time.time()


def running_time(timestamp: int | float) -> str:
    t = time.time() - timestamp
    day = t / 3600 / 24
    hour = (t % (3600 * 24)) / 3600
    minute = t % 3600 / 60
    second = t % 60
    start_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
    state_str = "开始运行于%s\n已经运行了%d天%d小时%d分%d秒" % (start_time_str, day, hour, minute, second)
    return state_str


def state(bot_start_time: float | int = start_time) -> str:
    split_str = "\n" + "-" * 6 + "\n"
    state_str = "系统" + running_time(psutil.boot_time()) + split_str
    state_str += "Bot" + running_time(bot_start_time) + split_str
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    used_memory = memory.used / 1024 / 1024 / 1024 # GB
    # 转成GB保留两位小数
    used_memory = round(used_memory, 2)
    total_memory = memory.total / 1024 / 1024 / 1024 # GB
    total_memory = round(total_memory, 2)
    state_str += f"CPU使用率：{cpu_percent}%\n内存使用率：{memory.percent}%, {used_memory}GB / {total_memory}GB\n"
    return state_str


__all__ = ['state']

if __name__ == '__main__':
    start_time = psutil.boot_time() - 7090
    print(state())