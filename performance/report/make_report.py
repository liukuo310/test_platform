from jinja2 import Template
import os
import numpy
import time


PATH = os.path.dirname(os.path.abspath(__file__))
# report_path = os.path.abspath(PATH + "/report/")
# report_template_path = os.path.abspath(PATH + "/templates/report_template.html")
# result_path = os.path.abspath(PATH + "/report/result")

report_path = os.path.abspath(PATH + "/report/")
android_report_template_path = os.path.abspath(PATH + "/../templates/report_template.html")
ios_report_template_path = os.path.abspath(PATH + "/../templates/ios_report_template.html")
result_path = os.path.abspath(PATH + "/result")


def make_dir(dirs):
    """创建文件夹"""
    if not os.path.exists(dirs):
        os.makedirs(dirs)


def get_report_template(sys, template_data):
    """生成报告模板,根据时间戳命名"""
    print(f"模板数据是{template_data}")
    report_template_path = ""
    if sys == "ios":
        report_template_path = ios_report_template_path
    elif sys == "android":
        report_template_path = android_report_template_path
    with open(report_template_path, encoding="utf-8") as f:
        template_str = f.read()
    report = Template(template_str)
    result = report.render(data=template_data)
    make_dir(result_path)
    with open(result_path+"/"+str(int(time.time()))+"_result.html", "w", encoding="utf-8") as f:
        f.write(result)


def get_result_data(test_data_info):
    """根据测试数据得出结果数据
    android_data = {
    "time": [],
    "total_cpu": [],
    "master_cpu": [],
    "im_cpu": [],
    "download_cpu": [],
    "fps": [],
    "jancky": [],
    "total_mem": [],
    "native_mem": [],
    "dalvik_mem": [],
    "master_ps": [],
    "im_ps": [],
    "download_ps": [],
    "net_up": [],
    "net_down": [],
    "master_up": [],
    "im_up": [],
    "download_up": [],
    "master_down": [],
    "im_down": [],
    "download_down": [],
    "battery_temperature": [],
    "battery": [],
}
    """
    # print(f"结果原数据是{test_data_info}")
    result_data = dict()
    avg_memory = numpy.average(test_data_info["total_mem"])
    result_data["avg_memory"] = avg_memory
    max_memory = max(test_data_info["total_mem"])
    result_data["max_memory"] = max_memory
    avg_cpu = numpy.average(test_data_info["total_cpu"])
    result_data["avg_cpu"] = avg_cpu
    max_cpu = max(test_data_info["total_cpu"])
    result_data["max_cpu"] = max_cpu
    avg_fps = numpy.average(test_data_info["fps"])
    result_data["avg_fps"] = avg_fps
    avg_Jank = numpy.average(test_data_info["jancky"])
    result_data["avg_Jank"] = avg_Jank
    avg_send = numpy.average(test_data_info["net_up"])
    result_data["avg_send"] = avg_send
    sum_send = sum(test_data_info["net_up"])
    result_data["sum_send"] = sum_send
    avg_rec = numpy.average(test_data_info["net_down"])
    result_data["avg_rec"] = avg_rec
    sum_rec = sum(test_data_info["net_down"])
    result_data["sum_rec"] = sum_rec
    avg_tem = numpy.average(test_data_info["battery_temperature"])
    result_data["avg_tem"] = avg_tem
    max_tem = max(test_data_info["battery_temperature"])
    result_data["max_tem"] = max_tem
    max_battery_level = max(test_data_info["battery"])
    result_data["max_battery_level"] = max_battery_level
    avg_battery_level = numpy.average(test_data_info["battery"])
    result_data["avg_battery_level"] = avg_battery_level
    return result_data


def add_test_data(test_data, result_data):
    """将每一帧测试数据归档"""
    result_data["time"].append(test_data["time"])
    result_data["total_cpu"].append(test_data["cpu_data"]["total"])
    result_data["master_cpu"].append(test_data["cpu_data"]["master"])
    result_data["im_cpu"].append(test_data["cpu_data"]["im"])
    result_data["download_cpu"].append(test_data["cpu_data"]["download"])
    result_data["fps"].append(test_data["fps_data"]["test_data_fps"])
    result_data["jancky"].append(test_data["fps_data"]["test_data_janky"])
    result_data["total_mem"].append(test_data["mem_data"]["total_pss"])
    result_data["native_mem"].append(test_data["mem_data"]["native_pss"])
    result_data["dalvik_mem"].append(test_data["mem_data"]["dalvik_pss"])
    result_data["master_ps"].append(test_data["mem_data"]["master"])
    result_data["im_ps"].append(test_data["mem_data"]["im"])
    result_data["download_ps"].append(test_data["mem_data"]["download"])
    result_data["net_up"].append(test_data["net_data"]["test_data_up_net"])
    result_data["net_down"].append(test_data["net_data"]["test_data_down_net"])
    result_data["master_up"].append(test_data["net_data"]["sen_master"])
    result_data["im_up"].append(test_data["net_data"]["sen_im"])
    result_data["download_up"].append(test_data["net_data"]["sen_download"])
    result_data["master_down"].append(test_data["net_data"]["rec_master"])
    result_data["im_down"].append(test_data["net_data"]["rec_im"])
    result_data["download_down"].append(test_data["net_data"]["rec_download"])
    result_data["battery_temperature"].append(test_data["temperature_data"]["battery_temperature"])
    result_data["battery"].append(test_data["battery_level"])
    return result_data


def get_ios_result_data(test_data_info):
    """获得ios设备结果数据"""
    result_data = dict()
    # print(f"test_data_info数据是{test_data_info}")
    result_data["avg_memory"] = numpy.average(test_data_info["mem"]["mem_data"])
    result_data["max_memory"] = max(test_data_info["mem"]["mem_data"])
    result_data["avg_cpu"] = numpy.average(test_data_info["cpu"]["app_value"])
    result_data["max_cpu"] = max(test_data_info["cpu"]["app_value"])
    result_data["avg_sys"] = numpy.average(test_data_info["cpu"]["sys_value"])
    result_data["max_sys"] = max(test_data_info["cpu"]["sys_value"])
    result_data["avg_fps"] = numpy.average(test_data_info["fps"]["fps_data"])
    result_data["avg_send"] = numpy.average(test_data_info["net"]["upFlow"])
    result_data["sum_send"] = sum(test_data_info["net"]["upFlow"])
    result_data["avg_rec"] = numpy.average(test_data_info["net"]["downFlow"])
    result_data["sum_rec"] = sum(test_data_info["net"]["downFlow"])
    return result_data


if __name__ == '__main__':
    pass

