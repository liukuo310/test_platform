from threading import Thread
from django.shortcuts import render
from django.http import HttpResponse
from performance import utils, get_android_info, get_ios_info
from performance.report.make_report import add_test_data, get_result_data, get_report_template, get_ios_result_data
import queue
import json
import time


def get_test_q():
    """获得测试数据的消息队列"""
    cpu_q = queue.Queue()
    fps_q = queue.Queue()
    net_q = queue.Queue()
    mem_q = queue.Queue()
    return cpu_q, fps_q, net_q, mem_q


def performance_main_view(request):
    """性能测试主页"""
    return render(request, "performance/performance_main.html")


def get_device_info(request):
    """获得手机系统情况接口"""
    device_sys = utils.get_device_sys()
    data = {}
    if device_sys:
        request.session["device_sys"] = device_sys  # 测试手机系统名称存入session
        app_list = utils.get_app_list(device_sys)
        data = {"device_sys": device_sys, "app_list": app_list}
        print(f"手机包名情况{data}")
        re = HttpResponse(json.dumps(data, ensure_ascii=False))
        re.set_cookie("device_sys", device_sys, expires=10000)
        return re
    else:
        print("未连接手机")
        return HttpResponse(json.dumps(data, ensure_ascii=False))


def select_test_template(request):
    """选择模板接口"""
    test_package_name = request.POST.get("select_value")
    request.session["test_package_name"] = test_package_name  # 测试包名存入session
    sys = request.COOKIES.get("device_sys")
    data_m = init_data(sys)  # 初始化数据格式
    request.session["test_data"] = data_m  # 测试数据放到session中
    template = ""
    if sys == "android":
        template = "android_template.html"
        print("选中了安卓的测试页面")
    elif sys == "ios":
        template = "ios_template.html"
        cpu_q, fps_q, net_q, mem_q = get_test_q()
        co = get_ios_info.IosInfo(test_package_name, cpu_q, fps_q, net_q, mem_q)
        request.session["co"] = co  # 实例化的ios类对象
        print("选中了ios的测试页面")
    else:
        print("没有选中测试系统")
    return_render = render(request, template)
    return_render.set_cookie("test_package_name", test_package_name, 10000)
    return return_render


def get_android_performance_info(request):
    """获得一帧安卓设备数据"""
    threads = []
    q_a = queue.Queue()
    data = {}
    time_time_label = time.strftime("%H:%M:%S")
    pack_name = request.COOKIES.get("test_package_name")
    t_cpu = Thread(target=get_android_info.get_cpu_info, args=(pack_name, q_a))
    threads.append(t_cpu)
    t_fps = Thread(target=get_android_info.get_fps_info, args=(pack_name, q_a))
    threads.append(t_fps)
    t_mem = Thread(target=get_android_info.get_mem_info, args=(pack_name, q_a))
    threads.append(t_mem)
    t_net = Thread(target=get_android_info.get_net_info, args=(pack_name, q_a))
    threads.append(t_net)
    t_tem = Thread(target=get_android_info.get_temperature_info, args=(q_a,))
    threads.append(t_tem)
    t_w = Thread(target=get_android_info.get_battery_p, args=(q_a,))
    threads.append(t_w)
    for t in threads:
        # t.setDaemon(True)
        t.start()
    t = 0
    while t < 6:
        data.update(q_a.get())
        t += 1
    data.update({"time": time_time_label})
    print(f"{time_time_label}帧的数据是{data}")
    request.session["test_data"] = add_test_data(data, request.session["test_data"])  # 归档测试数据
    return HttpResponse(json.dumps(data))


def ios_collect(request):
    """ios性能收集脚本开关"""
    # pac_name = request.COOKIES.get("test_package_name")
    switch_ = request.POST.get("switch_")
    co = request.session["co"]
    if switch_ == "on":
        co.start_collect()
    elif switch_ == "off":
        co.stop_collect()
    return HttpResponse()


def get_phone_message(request):
    """获得设备信息"""
    info = ""
    sys = request.COOKIES.get("device_sys")
    if sys == "android":
        info = utils.get_android_phone_info()
    elif sys == "ios":
        info = utils.get_ios_phone_info()
    return HttpResponse(json.dumps(info, ensure_ascii=False))


def result_report(request):
    """生成测试报告"""
    print("执行生成日志操作")
    # try:
    test_phone_info = dict()
    result_dict = {"test_data_info": dict(),
                   "test_phone_info": test_phone_info,
                   "test_result_info": dict()}
    sys = request.COOKIES.get("device_sys")
    # try:
    if sys == "android":
        data = request.session["test_data"]
        test_phone_info = utils.get_android_phone_info()
        result_dict["test_phone_info"] = test_phone_info
        result_dict["test_data_info"] = data
        result_dict["test_result_info"] = get_result_data(data)
        get_report_template(sys, result_dict)
        request.session["test_data"] = init_data(sys)  # 清空测试数据
    elif sys == "ios":
        test_phone_info = utils.get_ios_phone_info()
        result_dict["test_phone_info"] = test_phone_info
        co = request.session["co"]
        ios_report_data = co.get_report_data()
        result_dict["test_data_info"] = ios_report_data
        result_dict["test_result_info"] = get_ios_result_data(ios_report_data)
        get_report_template(sys, result_dict)
        request.session["test_data"] = init_data(sys)  # 清空测试数据
    return HttpResponse(json.dumps("生成报告成功"))
    # except:
    #     return HttpResponse(json.dumps("生成报告失败"))


def init_data(sys):
    """初始化测试数据"""
    data = dict()
    if sys == "android":
        data = {
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
    elif sys == "ios":
        pass
    return data


def get_ios_sq_info(request):
    """获得一次ios设备数据"""
    data = {}
    co = request.session["co"]
    cpu_info = co.get_cpu_info()
    fps_info = co.get_fps_info()
    mem_info = co.get_mem_info()
    net_info = co.get_net_info()
    if cpu_info:
        data.update(cpu_info)
    if fps_info:
        data.update(fps_info)
    if mem_info:
        data.update(mem_info)
    if net_info:
        data.update(net_info)  # todo:工具无法抓取准确数据
    print(f"一帧的数据是{data}")
    return HttpResponse(json.dumps(data))
