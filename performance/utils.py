import csv
import os
import subprocess
import time
import re


PATH = os.path.dirname(os.path.abspath(__file__))
the_time = time.time()


def get_shell_result(command):
    """获得shell命令结果数据"""
    p_obj = subprocess.Popen(
        args=command,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True, encoding="utf-8", errors="ignore")
    return p_obj


def get_doc_lines(doc_cmd):
    """获得列表形式命令行返回值"""
    p_obj = get_shell_result(doc_cmd)
    result_list = p_obj.stdout.readlines()
    return result_list


def doc_shell(command: str) -> str:
    """获得shell命令行结果"""
    p_obj = get_shell_result(command)
    result = p_obj.stdout.read()
    return result


def find_str(doc_cmd, find_str_):
    """模拟doc的find /I命令"""
    result_str = ""
    result_list = get_doc_lines(doc_cmd)
    for re_ in result_list:
        if re.search(find_str_, re_, re.IGNORECASE):
            result_str += re_
    return result_str


def get_device_sys() -> str:
    """获得当前连接手机的系统（android、ios）"""
    if get_devices_num("android") == 1:
        return "android"
    elif get_devices_num("ios") == 1:
        return "ios"
    else:
        print("没有连接手机")


def get_devices_num(sys) -> int:
    """获得当前链接设备数量"""
    num = 0
    if sys == "android":
        command = "adb devices"
        re_ = doc_shell(command)
        li = re_.split("\n")
        num = len(list(filter(None, li))) - 1
    elif sys == "ios":
        command = "python -m tidevice list"
        re_ = doc_shell(command)
        li = re_.split("\n")
        num = len(list(filter(None, li)))
    return num


def get_app_list(sys) -> list:
    """获得当前设备上的所有app包名"""
    result = []
    if sys == "android":
        cmd = "adb shell pm list packages"
        result_ = doc_shell(cmd)
        result = [re.findall(r".*:(.*)", i)[0] for i in result_.split()]
    elif sys == "ios":
        result = dict()
        cmd = "python -m tidevice applist"
        result_ = doc_shell(cmd)
        result_list = result_.split("\n")
        print(result_list)
        for i in result_list[:-1]:
            result[i.split()[0]] = i.split()[1]
    return result


def get_app_pid_dict(package_name):
    """根据包名获得{pid:ps_name}对象字典"""
    result_dict = {}
    result = find_str("adb shell ps", package_name)
    result_split = result.split("\n")
    for i in result_split:
        result_list_m = i.split()
        if result_list_m:
            pid = result_list_m[1]
            if "download" in result_list_m[-1]:
                result_dict["download"] = pid
            elif "im" in result_list_m[-1]:
                result_dict["im"] = pid
            else:
                result_dict["master"] = pid
    return result_dict


def get_android_phone_info():
    """
    获得手机设备信息
    """
    data = {
        "phone_os(操作系统版本号)": None,
        "os_api_version(手机系统api版本)": None,
        "cpu_type(cpu类型)": None,
        "cpu_arch(cpu芯片位数)": None,
        "cpu_core_num(cpu核数)": None,
        "cpu_freq(CPU硬件支持频率区间)": None,
        "GPU_type(GPU型号)": None,
        "openGL(编程作图,主要负责手机显示的东西)": None,
        "GPU_Freq()": None,  # todo
        "wm_size(屏幕分辨率)": None,
        "ram_size(手机内存总量)": None,
        "swap(交换空间大小)": None
    }
    release_result = doc_shell("adb shell getprop ro.build.version.release")
    if release_result:
        data["phone_os(操作系统版本号)"] = release_result.replace("\n", "")
    os_api_version = doc_shell("adb shell getprop ro.build.version.sdk")
    if os_api_version:
        data["os_api_version(手机系统api版本)"] = os_api_version.replace("\n", "")
    cpu_type = doc_shell("adb shell getprop ro.product.board")
    if cpu_type:
        data["cpu_type(cpu类型)"] = cpu_type.replace("\n", "")
    cpu_arch = doc_shell("adb shell getprop ro.product.cpu.abi")
    if cpu_arch:
        data["cpu_arch(cpu芯片位数)"] = cpu_arch.replace("\n", "")
    cpu_num = len(get_doc_lines("adb shell cat /proc/cpuinfo | findstr processor"))
    if cpu_num:
        data["cpu_core_num(cpu核数)"] = cpu_num
    cpu_freq_min_str = doc_shell("adb shell cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq")
    cpu_freq_max_str = doc_shell("adb shell cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq")
    if cpu_freq_min_str and cpu_freq_max_str:
        cpu_freq_min = int(cpu_freq_min_str.replace("\n", ""))/1000000
        cpu_freq_max = int(cpu_freq_max_str.replace("\n", "")) / 1000000
        data["cpu_freq(CPU硬件支持频率区间)"] = str(cpu_freq_min) + "MHz" + "-" + str(cpu_freq_max) + "MHz"
    gles_result = doc_shell("adb shell dumpsys SurfaceFlinger | findstr GLES")
    if gles_result:
        gles_result_str = gles_result.replace("\n", "")
        GLES = re.findall(r"GLES:(.*)OpenGL(.*)", gles_result_str)[0]
        data["GPU_type(GPU型号)"] = GLES[0]
        data["openGL(编程作图,主要负责手机显示的东西)"] = "OpenGL" + GLES[1]
    wm_size_str = doc_shell("adb shell wm size")
    if wm_size_str:
        data["wm_size(屏幕分辨率)"] = re.findall(r"Physical size:(.*)", wm_size_str)[0]
    ram_size_str = doc_shell("adb shell cat /proc/meminfo | findstr MemTotal")
    if ram_size_str:
        ram_size = str(int(float(re.findall(r"\d+", ram_size_str)[0])/1024))
        data["ram_size(手机运行内存总量)"] = ram_size + "Mb"
    swap_size_str = doc_shell("adb shell cat /proc/meminfo | findstr SwapTotal")
    if swap_size_str:
        data["swap(交换空间大小)"] = str(int(float(re.findall(r"\d+", swap_size_str)[0])/1024)) + "Mb"
    return data


def get_ios_phone_info():
    """获得ios设备信息"""
    info_dict = dict()
    phone_info = doc_shell("python -m tidevice info")
    phone_info_list = phone_info.split("\n")[:-1]
    print(phone_info_list)
    for i in phone_info_list:
        i_list = i.split()
        info_dict[i_list[0]] = "".join(i_list[1:])
    return info_dict

def get_android_phone_info():
    """
    获得手机设备信息
    """
    data = {
        "phone_os(操作系统版本号)": None,
        "os_api_version(手机系统api版本)": None,
        "cpu_type(cpu类型)": None,
        "cpu_arch(cpu芯片位数)": None,
        "cpu_core_num(cpu核数)": None,
        "cpu_freq(CPU硬件支持频率区间)": None,
        "GPU_type(GPU型号)": None,
        "openGL(编程作图,主要负责手机显示的东西)": None,
        "GPU_Freq()": None,  # todo
        "wm_size(屏幕分辨率)": None,
        "ram_size(手机内存总量)": None,
        "swap(交换空间大小)": None
    }
    release_result = doc_shell("adb shell getprop ro.build.version.release")
    if release_result:
        data["phone_os(操作系统版本号)"] = release_result.replace("\n", "")
    os_api_version = doc_shell("adb shell getprop ro.build.version.sdk")
    if os_api_version:
        data["os_api_version(手机系统api版本)"] = os_api_version.replace("\n", "")
    cpu_type = doc_shell("adb shell getprop ro.product.board")
    if cpu_type:
        data["cpu_type(cpu类型)"] = cpu_type.replace("\n", "")
    cpu_arch = doc_shell("adb shell getprop ro.product.cpu.abi")
    if cpu_arch:
        data["cpu_arch(cpu芯片位数)"] = cpu_arch.replace("\n", "")
    cpu_num = len(get_doc_lines("adb shell cat /proc/cpuinfo | findstr processor"))
    if cpu_num:
        data["cpu_core_num(cpu核数)"] = cpu_num
    cpu_freq_min_str = doc_shell("adb shell cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq")
    cpu_freq_max_str = doc_shell("adb shell cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq")
    if cpu_freq_min_str and cpu_freq_max_str:
        cpu_freq_min = int(cpu_freq_min_str.replace("\n", ""))/1000000
        cpu_freq_max = int(cpu_freq_max_str.replace("\n", "")) / 1000000
        data["cpu_freq(CPU硬件支持频率区间)"] = str(cpu_freq_min) + "MHz" + "-" + str(cpu_freq_max) + "MHz"
    gles_result = doc_shell("adb shell dumpsys SurfaceFlinger | findstr GLES")
    if gles_result:
        gles_result_str = gles_result.replace("\n", "")
        GLES = re.findall(r"GLES:(.*)OpenGL(.*)", gles_result_str)[0]
        data["GPU_type(GPU型号)"] = GLES[0]
        data["openGL(编程作图,主要负责手机显示的东西)"] = "OpenGL" + GLES[1]
    wm_size_str = doc_shell("adb shell wm size")
    if wm_size_str:
        data["wm_size(屏幕分辨率)"] = re.findall(r"Physical size:(.*)", wm_size_str)[0]
    ram_size_str = doc_shell("adb shell cat /proc/meminfo | findstr MemTotal")
    if ram_size_str:
        ram_size = str(int(float(re.findall(r"\d+", ram_size_str)[0])/1024))
        data["ram_size(手机运行内存总量)"] = ram_size + "Mb"
    swap_size_str = doc_shell("adb shell cat /proc/meminfo | findstr SwapTotal")
    if swap_size_str:
        data["swap(交换空间大小)"] = str(int(float(re.findall(r"\d+", swap_size_str)[0])/1024)) + "Mb"
    return data
