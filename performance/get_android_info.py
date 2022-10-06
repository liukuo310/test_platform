from performance import utils
import re
import time


def get_cpu_info(package_name, q):
    """获得cpu性能数据"""
    data_ = {"total": 0, "download": 0, "im": 0, "master": 0}
    cpu_rate = 0  # 没有启动进程时为0
    cpu_rate_str = utils.find_str('adb shell dumpsys cpuinfo', str(package_name))
    cpu_rate_list = cpu_rate_str.split("\n")[:-1]
    if len(cpu_rate_list) == 0:  # 没有启动app的情况
        q.put({"cpu_data": data_})
    else:
        for cpu_rate_o in cpu_rate_list:
            rate_list_ = cpu_rate_o.split()
            rate_o = float(rate_list_[0].replace("%", ""))
            if "download" in cpu_rate_o:
                data_["download"] = rate_o
            elif "im" in cpu_rate_o:
                data_["im"] = rate_o
            else:  # master
                data_["master"] = rate_o
            cpu_rate += rate_o
        data_.update({"total": round(cpu_rate/len(cpu_rate_list), 2)})
        q.put({"cpu_data": data_})


def get_fps_info(package_name, q):
    """获取fps数据"""
    last_time = time.time()
    last_fps, last_janky_num, carton_num = get_sq_fps(package_name)
    time.sleep(1)  # 最少获取间隔一秒的帧率数据
    current_time = time.time()
    current_fps, current_janky_num, current_carton_nun = get_sq_fps(package_name)
    time_delta = (current_time - last_time)
    fps_delta = current_fps - last_fps
    janky_num = current_janky_num - last_janky_num
    # janky = janky_num/(fps_delta+1)
    carton_num = current_carton_nun - carton_num
    # carton = carton_num/(fps_delta+1)
    fps = round(fps_delta / round(time_delta, 2), 2)
    q.put({"fps_data": {
                    "test_data_fps": fps,
                    "test_data_janky": janky_num,
                    "carton": carton_num
                }})


def get_sq_fps(package_name):
    """获取当前fps总数"""
    current_fps_all = 0
    janky_num = 0
    carton_num = 0
    pid_list = utils.get_app_pid_list(package_name)
    for pid in pid_list:
        command = "adb shell dumpsys gfxinfo " + str(pid)
        all_result = utils.get_doc_lines(command)
        results = utils.result_find_str(all_result, "Total frames")
        if not len(results) == 0:  # 其他进程
            histogram = utils.result_find_str(all_result, "HISTOGRAM")  # 所有帧数总结
            carton_num = utils.get_order_fps(histogram, 36)  # 二倍janck算carton
            current_fps = int(re.findall(r"\d+", results)[0])
            janky_num = int(re.findall(r"\d+", utils.find_str(command, "Janky frames"))[0])
            current_fps_all += current_fps
            return round(current_fps_all, 2), round(janky_num, 2), carton_num
    return round(current_fps_all, 2), round(janky_num, 2), carton_num  # 连接手机未打开app情况


def get_mem_info(package_name, q):
    """获得内存性能数据"""
    native_pss = 0
    dalvik_pss = 0
    total_pss = 0
    mem_data = {'mem_data': {'native_pss': 0.0, 'dalvik_pss': 0.0, 'total_pss': 0.0, 'master': 0.0, 'im': 0.0, 'download': 0.0}}
    pid_dict = utils.get_app_pid_dict(package_name)
    for ps_name, pid in pid_dict.items():
        total_count = 0
        mem_info_str_list = utils.get_doc_lines("adb shell dumpsys meminfo " + str(pid))
        for str_ in mem_info_str_list:
            if re.search("Native Heap ", str_, re.IGNORECASE):
                native_info = str_.split()
                native_pss += float(format(int(native_info[2]) / 1024.0, ".2f"))
                mem_data["mem_data"]["native_pss"] = native_pss
            elif re.search("Dalvik Heap ", str_, re.IGNORECASE):
                dalvik_info = str_.split()
                dalvik_pss += float(format(int(dalvik_info[2]) / 1024.0, ".2f"))
                mem_data["mem_data"]["dalvik_pss"] = dalvik_pss
            elif re.search("TOTAL ", str_, re.IGNORECASE):
                if total_count == 1:
                    total_info = str_.split()
                    total_pss += float(format(int(total_info[2]) / 1024.0, ".2f"))
                    mem_data["mem_data"]["total_pss"] = total_pss
                    mem_data["mem_data"][ps_name] = float(format(int(total_info[2]) / 1024.0, ".2f"))
                total_count += 1
    q.put(mem_data)


def get_net_info(package_name, q):
    """获得网络性能数据"""
    net_data_before = get_sq_net(package_name)
    time.sleep(1)
    net_data_after = get_sq_net(package_name)
    rec_master = round((net_data_after["master"]['rec']-net_data_before["master"]['rec'])/1024, 2)
    sen_master = round((net_data_after["master"]['sen']-net_data_before["master"]['sen'])/1024, 2)
    rec_download = round((net_data_after["download"]['rec'] - net_data_before["download"]['rec']) / 1024, 2)
    sen_download = round((net_data_after["download"]['sen'] - net_data_before["download"]['sen']) / 1024, 2)
    rec_im = round((net_data_after["im"]['rec'] - net_data_before["im"]['rec']) / 1024, 2)
    sen_im = round((net_data_after["im"]['sen'] - net_data_before["im"]['sen']) / 1024, 2)
    rec_tal = round((net_data_after["rec_tal"]-net_data_before["rec_tal"])/1024, 2)
    sen_tal = round((net_data_after["sen_tal"]-net_data_before["sen_tal"])/1024, 2)
    q.put({"net_data": {
                    "test_data_up_net": sen_tal,
                    "test_data_down_net": rec_tal,
                    "rec_master": rec_master,
                    "sen_master": sen_master,
                    "rec_download": rec_download,
                    "sen_download": sen_download,
                    "rec_im": rec_im,
                    "sen_im": sen_im
                }})


def get_sq_net(package_name):
    """获得当前网络流量数据"""
    rec_tal = 0
    sen_tal = 0
    net_data = {'master': {'rec': 0.0, 'sen': 0.0}, "download": {'rec': 0.0, 'sen': 0.0}, "im": {'rec': 0.0, 'sen': 0.0}, 'rec_tal': 0, 'sen_tal': 0}
    pid_dict = utils.get_app_pid_dict(package_name)
    for ps_name, pid in pid_dict.items():
        net_data[ps_name] = {}  # 初始化
        res_list = utils.adb_shell(f"cat /proc/{pid}/net/dev").split("\n")
        for res in res_list:
            if "wlan0" in res:
                se_list = res.split()
                rec = se_list[1]
                sen = se_list[9]
                rec_tal += float(rec)
                net_data[ps_name]["rec"] = float(rec)
                sen_tal += float(sen)
                net_data[ps_name]["sen"] = float(sen)
    net_data["rec_tal"] = rec_tal
    net_data["sen_tal"] = sen_tal
    return net_data


def get_temperature_info(q):
    """获取安卓设备温度值"""
    battery_temperature = float(get_battery_info("temperature"))/10
    q.put({"temperature_data": {
        "battery_temperature": battery_temperature
    }})


def get_battery_p(q):
    """获得电池功率（w）"""
    battery_v = float(get_battery_info("voltage"))
    battery_level = float(get_battery_info("level"))
    # battery_w = round(battery_v*battery_a, 2)
    q.put({"battery_level": battery_level})


def get_battery_info(b_str):
    """
    AC powered：false  是否连接AC（电源）充电线

    USB powered：true  是否连接USB（PC或笔记本USB插口）充电

    Wireless powered：false  是否使用了无线电源

    status: 1    电池状态，2为充电状态，其他为非充电状态

    level：58     电量（%）

    scale: 100.        电量最大数值

    voltage: 3977      当前电压（mV）

    current now: -335232.     当前电流（mA）负数代表充电中

    temperature:355      电池温度，单位为0.1摄氏度

    technology:Li-poly.    电池种类
    """
    cmd = "adb shell dumpsys battery"
    battery_info_str = utils.find_str(cmd, b_str)
    result_ = re.findall("(.*):(.*)", battery_info_str)[0][1]
    return result_


def get_all_cpu_info(q):
    """获得所有cpu数据"""
