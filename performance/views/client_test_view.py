from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import json
import time
import random


def performance_main_test_view(request):
    """客户端性能测试主页"""
    return render(request, "performance/client_test_main.html")


def performance_view(request):
    """客户端性能数据页"""
    # 从GET参数或session中获取测试配置
    device_info = request.GET.get('device', '')
    app_info = request.GET.get('app', '')

    context = {
        'device_info': device_info,
        'app_info': app_info,
    }

    return render(request, "performance/client_test_performance.html", context)


def performance_test_data(request):
    """获得测试数据（模拟数据接口）"""
    if request.method == 'GET':
        # test_mode = request.GET.get('mode', 'normal')
        test_mode = 'test'
        if test_mode == 'test':
            data = generate_mock_data()
        else:
            data = get_real_device_data(request)

        return JsonResponse(data)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


def generate_mock_data():
    """生成模拟测试数据"""
    print("获取测试数据")
    return {
        'time': time.strftime('%H:%M:%S'),
        'cpu_data': {
            'total': round(random.uniform(20, 80), 2),
            'master': round(random.uniform(10, 40), 2),
            'im': round(random.uniform(5, 20), 2),
            'download': round(random.uniform(3, 15), 2)
        },
        'fps_data': {
            'test_data_fps': round(random.uniform(45, 60), 2),
            'test_data_janky': random.randint(0, 5),
            'carton': random.randint(0, 2)
        },
        'mem_data': {
            'total_pss': round(random.uniform(200, 500), 2),
            'native_pss': round(random.uniform(80, 150), 2),
            'dalvik_pss': round(random.uniform(50, 100), 2),
            'master': round(random.uniform(100, 250), 2),
            'im': round(random.uniform(40, 100), 2),
            'download': round(random.uniform(30, 80), 2)
        },
        'net_data': {
            'test_data_up_net': round(random.uniform(10, 100), 2),
            'test_data_down_net': round(random.uniform(50, 300), 2),
            'rec_master': round(random.uniform(20, 100), 2),
            'sen_master': round(random.uniform(5, 50), 2),
            'rec_download': round(random.uniform(15, 80), 2),
            'sen_download': round(random.uniform(3, 30), 2),
            'rec_im': round(random.uniform(10, 60), 2),
            'sen_im': round(random.uniform(2, 20), 2)
        },
        'temperature_data': {
            'battery_temperature': round(random.uniform(25, 40), 2)
        },
        'battery_level': round(random.uniform(50, 100), 2)
    }


def get_real_device_data(request):
    """获取真实设备数据（需要连接设备）"""
    try:
        from performance import utils, get_android_info
        import queue
        from threading import Thread

        package_name = request.session.get('test_package_name', '')
        if not package_name:
            return {'error': '未设置测试包名', 'mode': 'mock'}

        q = queue.Queue()
        threads = []
        data = {}

        t_cpu = Thread(target=get_android_info.get_cpu_info, args=(package_name, q))
        threads.append(t_cpu)
        t_fps = Thread(target=get_android_info.get_fps_info, args=(package_name, q))
        threads.append(t_fps)
        t_mem = Thread(target=get_android_info.get_mem_info, args=(package_name, q))
        threads.append(t_mem)
        t_net = Thread(target=get_android_info.get_net_info, args=(package_name, q))
        threads.append(t_net)
        t_tem = Thread(target=get_android_info.get_temperature_info, args=(q,))
        threads.append(t_tem)
        t_bat = Thread(target=get_android_info.get_battery_p, args=(q,))
        threads.append(t_bat)

        for t in threads:
            t.start()

        for _ in range(6):
            data.update(q.get())

        data['time'] = time.strftime('%H:%M:%S')
        return data

    except Exception as e:
        print(f"获取真实数据失败: {e}")
        return generate_mock_data()