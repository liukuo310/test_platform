import json
import time
import logging
from datetime import datetime

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET

from performance.get_service_info import ServicePerformanceCollector

logger = logging.getLogger(__name__)


def service_performance_main(request):
    """服务端性能抓取选择页面"""
    return render(request, "performance/service_main.html")


def service_performance(request):
    """性能图标页面"""
    return render(request, "performance/service_performance.html")


@require_POST
def init_performance_conf(request):
    """
    初始化服务端性能抓取配置

    请求参数:
        - service_ip: str, 服务端IP地址 (格式: username@ip 或 127.0.0.1)
        - password: str, SSH密码（远程时需要）
        - data_type_list: list, 需要抓取的数据类型列表
          (可选值: ['cpu', 'memory', 'disk', 'network'])
        - stress_server_ip: str, 施压服务器IP（可选）
        - stress_server_password: str, 施压服务器密码（可选）
        - api_configs: list, 施压服务器接口配置列表（可选）
          格式: [{'name': str, 'url': str, 'concurrency': int, 'method': str}]

    返回:
        - status: success/failed
        - message: 提示信息
        - session_id: 会话ID
    """
    try:
        data = json.loads(request.body)

        # 验证并保存服务IP和认证信息
        service_ip = data.get("service_ip")
        password = data.get("password")
        print(service_ip, password)

        if not service_ip or not isinstance(service_ip, str):
            return JsonResponse({
                'status': 'failed',
                'message': '需要填写有效的IP地址'
            }, status=400)

        # 判断是本地还是远程
        is_local = _is_local_ip(service_ip)

        if is_local:
            # 本地采集模式
            ip_addr = '127.0.0.1'
            username = 'local'

            # 测试本地psutil是否可用
            try:
                with ServicePerformanceCollector(mode='local') as collector:
                    test_data = collector.collect_cpu()
            except Exception as e:
                return JsonResponse({
                    'status': 'failed',
                    'message': f'本地性能采集模块初始化失败: {str(e)}'
                }, status=500)
        else:
            # 远程SSH模式
            import re
            if '@' in service_ip:
                username, ip_addr = service_ip.split('@', 1)
            else:
                username = 'root'
                ip_addr = service_ip

            # IP或域名格式校验
            # 支持：IPv4、localhost、域名、test（测试模式）
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$|^localhost$|^test$|^[a-zA-Z0-9][a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(ip_pattern, ip_addr):
                return JsonResponse({
                    'status': 'failed',
                    'message': 'IP地址或域名格式不正确'
                }, status=400)

            if not password:
                return JsonResponse({
                    'status': 'failed',
                    'message': '远程连接需要提供密码'
                }, status=400)

            # 如果是测试模式，跳过SSH连接测试
            if ip_addr.lower() == 'test':
                logger.info(f"测试模式：跳过SSH连接测试 - IP: {ip_addr}")
                os_type = 'test'
            else:
                # 测试SSH连接
                try:
                    with ServicePerformanceCollector(ip_addr, username, password, mode='remote') as collector:
                        test_data = collector.collect_cpu()  # 尝试链接一下
                        os_type = collector.remote_os_type

                        # 记录服务器信息
                        logger.info(f"远程服务器类型: {os_type}, IP: {ip_addr}")

                        # 如果是未知系统，给出警告
                        if os_type == 'unknown':
                            logger.warning(f"无法识别远程服务器操作系统类型: {ip_addr}")
                except Exception as e:
                    error_msg = str(e)
                    print("错误信息")
                    print(error_msg)
                    # 针对常见错误提供更友好的提示
                    if 'Authentication failed' in error_msg or 'auth' in error_msg.lower():
                        return JsonResponse({
                            'status': 'failed',
                            'message': 'SSH认证失败，请检查用户名和密码'
                        }, status=401)
                    elif 'Connection refused' in error_msg or 'connect' in error_msg.lower():
                        return JsonResponse({
                            'status': 'failed',
                            'message': 'SSH连接被拒绝，请检查服务器IP和端口是否正确'
                        }, status=500)
                    elif 'timeout' in error_msg.lower():
                        return JsonResponse({
                            'status': 'failed',
                            'message': 'SSH连接超时，请检查网络是否通畅'
                        }, status=500)
                    else:
                        return JsonResponse({
                            'status': 'failed',
                            'message': f'SSH连接失败: {error_msg}'
                        }, status=500)
        # 保存配置到session
        request.session["service_ip"] = ip_addr
        request.session["service_username"] = username
        request.session["service_password"] = password if password else ''
        request.session["is_local"] = is_local

        # 验证并保存数据类型列表
        data_type_list = data.get("data_type_list", [])
        if not isinstance(data_type_list, list):
            return JsonResponse({
                'status': 'failed',
                'message': '数据类型必须是列表格式'
            }, status=400)

        if len(data_type_list) == 0:
            return JsonResponse({
                'status': 'failed',
                'message': '至少需要选择一种要抓取的数据类型'
            }, status=400)

        # 验证数据类型是否合法
        valid_types = {'cpu', 'memory', 'disk', 'network'}
        invalid_types = [t for t in data_type_list if t not in valid_types]
        if invalid_types:
            return JsonResponse({
                'status': 'failed',
                'message': f'不支持的数据类型: {", ".join(invalid_types)}'
            }, status=400)

        request.session["data_type_list"] = data_type_list

        # 处理施压服务器配置（新增）
        stress_server_ip = data.get("stress_server_ip")
        stress_server_password = data.get("stress_server_password")
        api_configs = data.get("api_configs", [])

        if stress_server_ip and stress_server_password and api_configs:
            # 验证施压服务器配置
            if not isinstance(api_configs, list):
                return JsonResponse({
                    'status': 'failed',
                    'message': '接口配置必须是列表格式'
                }, status=400)

            # 验证每个接口配置的字段
            for i, config in enumerate(api_configs):
                if not all(key in config for key in ['name', 'url', 'concurrency', 'method']):
                    return JsonResponse({
                        'status': 'failed',
                        'message': f'第{i + 1}个接口配置缺少必要字段'
                    }, status=400)

                if not isinstance(config['concurrency'], int) or config['concurrency'] <= 0:
                    return JsonResponse({
                        'status': 'failed',
                        'message': f'第{i + 1}个接口的并发数必须为正整数'
                    }, status=400)

            # 保存施压服务器配置到session
            request.session["stress_server_ip"] = stress_server_ip
            request.session["stress_server_password"] = stress_server_password
            request.session["api_configs"] = api_configs

            logger.info(f"施压服务器配置已保存 - IP: {stress_server_ip}, 接口数: {len(api_configs)}")

        # 初始化时间戳和计数器
        request.session["start_time"] = time.time()
        request.session["frame_count"] = 0

        mode_text = "本地" if is_local else f"远程({username}@{ip_addr})"
        stress_info = f", 施压服务器: {stress_server_ip}" if stress_server_ip else ""
        logger.info(f"性能抓取配置初始化成功 - 模式: {mode_text}{stress_info}, 类型: {data_type_list}")

        return JsonResponse({
            'status': 'success',
            'message': f'配置初始化成功（{mode_text}模式）',
            'session_id': request.session.session_key,
            'config': {
                'service_ip': service_ip,
                'mode': 'local' if is_local else 'remote',
                'data_types': data_type_list,
                'has_stress_server': bool(stress_server_ip)
            }
        })

    except json.JSONDecodeError:
        logger.error("请求数据格式错误")
        return JsonResponse({
            'status': 'failed',
            'message': '请求数据格式错误'
        }, status=400)
    except Exception as e:
        logger.error(f"初始化配置失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'failed',
            'message': f'服务器内部错误: {str(e)}'
        }, status=500)

@require_GET
def get_performance_data(request):
    """
    抓取一帧服务端性能数据

    根据配置自动选择本地采集或SSH远程采集

    返回:
        - status: success/failed
        - timestamp: 时间戳
        - frame_index: 帧序号
        - data: 性能数据对象
    """
    try:
        # 从session获取配置
        service_ip = request.session.get("service_ip")
        username = request.session.get("service_username")
        password = request.session.get("service_password")
        is_local = request.session.get("is_local", False)

        if not service_ip:
            return JsonResponse({
                'status': 'failed',
                'message': '未初始化配置，请先调用初始化接口'
            }, status=400)

        data_type_list = request.session.get("data_type_list", [])
        if not data_type_list:
            return JsonResponse({
                'status': 'failed',
                'message': '未配置数据类型'
            }, status=400)

        # 更新帧计数
        frame_count = request.session.get("frame_count", 0) + 1
        request.session["frame_count"] = frame_count

        # 检查是否为测试模式
        if "test" in service_ip.lower():
            import random
            # 生成测试数据
            performance_data = {}

            if 'cpu' in data_type_list:
                performance_data['cpu'] = {
                    'usage_percent': random.uniform(20, 80),
                    'cpu_count': 8
                }

            if 'memory' in data_type_list:
                total_mb = 8192
                used_mb = random.uniform(2000, 6000)
                performance_data['memory'] = {
                    'usage_percent': (used_mb / total_mb) * 100,
                    'used_mb': used_mb,
                    'total_mb': total_mb
                }

            if 'disk' in data_type_list:
                total_gb = 500
                used_gb = random.uniform(100, 300)
                performance_data['disk'] = {
                    'usage_percent': (used_gb / total_gb) * 100,
                    'used_gb': used_gb,
                    'total_gb': total_gb,
                    'read_mb_per_sec': random.uniform(10, 60),
                    'write_mb_per_sec': random.uniform(5, 35)
                }

            if 'network' in data_type_list:
                performance_data['network'] = {
                    'bytes_sent_mb': random.uniform(50, 150),
                    'bytes_recv_mb': random.uniform(100, 300)
                }

            return JsonResponse({
                'status': 'success',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'frame_index': frame_count,
                'service_ip': service_ip,
                'mode': 'test',
                'data': performance_data
            })

        # 根据模式选择采集方式
        try:
            if is_local:
                with ServicePerformanceCollector(mode='local') as collector:
                    performance_data = collector.collect_all(data_type_list)
            else:
                if not password:
                    return JsonResponse({
                        'status': 'failed',
                        'message': '远程采集缺少密码信息'
                    }, status=400)

                with ServicePerformanceCollector(service_ip, username, password, mode='remote') as collector:
                    performance_data = collector.collect_all(data_type_list)
        except Exception as e:
            logger.error(f"数据采集失败: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'failed',
                'message': f'数据采集失败: {str(e)}'
            }, status=500)
        # 检查是否有采集错误
        errors = performance_data.pop('_errors', {})

        # 构建响应
        mode_text = "本地" if is_local else f"{username}@"
        response_data = {
            'status': 'success',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'frame_index': frame_count,
            'service_ip': service_ip,
            'mode': 'local' if is_local else 'remote',
            'data': performance_data
        }

        if errors:
            response_data['warnings'] = [f"{k}: {v}" for k, v in errors.items()]

        logger.debug(f"第{frame_count}帧数据采集完成 - {mode_text}{service_ip}")

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"采集性能数据失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'failed',
            'message': f'数据采集失败: {str(e)}'
        }, status=500)


@require_POST
def stop_performance_collect(request):
    """
    停止性能数据采集并清理session
    """
    try:
        start_time = request.session.get("start_time")
        frame_count = request.session.get("frame_count", 0)
        service_ip = request.session.get("service_ip")
        is_local = request.session.get("is_local", False)
        stress_server_ip = request.session.get("stress_server_ip")

        # 清理session数据（包括敏感信息）
        request.session.pop("service_ip", None)
        request.session.pop("service_username", None)
        request.session.pop("service_password", None)
        request.session.pop("data_type_list", None)
        request.session.pop("start_time", None)
        request.session.pop("frame_count", None)
        request.session.pop("is_local", None)
        # 清理施压服务器配置
        request.session.pop("stress_server_ip", None)
        request.session.pop("stress_server_password", None)
        request.session.pop("api_configs", None)

        duration = round(time.time() - start_time, 2) if start_time else 0
        mode_text = "本地" if is_local else "远程"
        stress_info = f", 施压服务器: {stress_server_ip}" if stress_server_ip else ""

        logger.info(f"性能采集结束 - {mode_text}{service_ip}{stress_info} - 总帧数: {frame_count}, 持续时间: {duration}秒")

        return JsonResponse({
            'status': 'success',
            'message': '采集已停止',
            'total_frames': frame_count,
            'duration': duration
        })

    except Exception as e:
        logger.error(f"停止采集失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'failed',
            'message': f'停止失败: {str(e)}'
        }, status=500)


@require_POST
def monitor_stress_server(request):
    """
    监控施压服务器的实时性能数据

    参数:
        - stress_server_ip: 施压服务器IP
        - stress_server_user: SSH用户名
        - stress_server_password: SSH密码
        - api_list: 要监控的接口列表
          格式: [{'name': str, 'path': str}]

    返回:
        - status: success/failed
        - data: {
            summary: {
                total_concurrency: int,
                total_requests: int,
                avg_response_time: float,
                failed_requests: int
            },
            api_stats: [
                {
                    name: str,
                    path: str,
                    concurrency: int,
                    total_requests: int,
                    avg_response_time: float,
                    failed_requests: int
                }
            ],
            concurrency_history: {
                timestamps: [str],
                total_concurrency: [int],
                api_concurrency: [{'name': str, 'data': [int]}]
            }
          }
    """
    try:
        data = json.loads(request.body)

        stress_ip = data.get('stress_server_ip')
        stress_user = data.get('stress_server_user')
        stress_password = data.get('stress_server_password')
        api_list = data.get('api_list', [])

        # 获取施压服务器的实际数据
        try:
            if "test" in stress_ip:  # 测试数据，动态生成
                import time as _time
                import math
                import random

                current_time = _time.strftime('%H:%M:%S', _time.localtime())

                # 根据前端传递的接口数量生成数据
                num_apis = len(api_list) if api_list else 1

                # 生成动态的基础并发数（正弦波 + 随机波动）
                base_concurrency = 200 + 100 * math.sin(2 * math.pi * random.random() * 60)
                noise = random.randint(-30, 30)
                total_concurrency = max(50, int(base_concurrency + noise))

                # 根据接口数量分配并发数
                api_concurrencies = []

                if num_apis > 0:
                    remaining = total_concurrency
                    for i in range(num_apis):
                        if i == num_apis - 1:
                            api_concurrencies.append(remaining)
                        else:
                            ratio = random.uniform(0.3, 0.5)
                            allocated = int(remaining * ratio)
                            api_concurrencies.append(allocated)
                            remaining -= allocated

                # 生成请求数
                requests_per_api = []
                for i in range(num_apis):
                    new_requests = random.randint(1000, 50000)
                    requests_per_api.append(new_requests)

                total_requests = sum(requests_per_api)

                # 生成响应时间（带波动）
                response_times = []
                for i in range(num_apis):
                    rt = 45.0 + random.uniform(-15, 15) + (random.random() * 10)
                    response_times.append(max(10.0, rt))

                avg_response_time = sum(response_times) / len(response_times) if response_times else 50.0

                # 生成失败请求数（偶尔出现）
                failed_per_api = []
                for i in range(num_apis):
                    fail_rate = random.random()
                    if fail_rate < 0.1:  # 10%概率有失败
                        failed = random.randint(0, int(requests_per_api[i] * 0.02))
                    else:
                        failed = 0
                    failed_per_api.append(failed)

                total_failed = sum(failed_per_api)

                # 构建API统计数据
                api_stats = []
                api_concurrency_history = []

                for i in range(num_apis):
                    # 从前端配置中获取接口名称和路径
                    api_name = api_list[i]['name'] if i < len(api_list) else f'接口{i+1}'
                    api_path = api_list[i]['path'] if i < len(api_list) else f'/api/{i+1}'

                    api_stats.append({
                        'name': api_name,
                        'path': api_path,
                        'concurrency': api_concurrencies[i],
                        'total_requests': requests_per_api[i],
                        'avg_response_time': round(response_times[i], 1),
                        'failed_requests': failed_per_api[i]
                    })

                    # 为图表生成单个数据点
                    api_concurrency_history.append({
                        'name': api_name,
                        'data': [api_concurrencies[i]]
                    })

                stress_data = {
                    'summary': {
                        'total_concurrency': total_concurrency,
                        'total_requests': total_requests,
                        'avg_response_time': round(avg_response_time, 1),
                        'failed_requests': total_failed
                    },
                    'api_stats': api_stats,
                    'concurrency_history': {
                        'timestamps': [current_time],
                        'total_concurrency': [total_concurrency],
                        'api_concurrency': api_concurrency_history
                    }
                }
            else:
                if not all([stress_ip, stress_user, stress_password]):
                    return JsonResponse({
                        'status': 'failed',
                        'message': '缺少施压服务器配置信息'
                    }, status=400)

                if not api_list or not isinstance(api_list, list):
                    return JsonResponse({
                        'status': 'failed',
                        'message': '没有配置要监控的接口'
                    }, status=400)
                stress_data = _fetch_stress_server_metrics(stress_ip, stress_user, stress_password, api_list)

            return JsonResponse({
                'status': 'success',
                'data': stress_data
            })

        except Exception as e:
            logger.error(f"获取施压服务器数据失败: {str(e)}")
            # 返回模拟数据用于演示
            import random

            # 生成总体统计
            mock_summary = {
                'total_concurrency': sum([random.randint(50, 500) for _ in api_list]),
                'total_requests': sum([random.randint(1000, 50000) for _ in api_list]),
                'avg_response_time': random.uniform(20, 150),
                'failed_requests': random.randint(0, 20)
            }

            # 为每个接口生成统计数据
            mock_api_stats = []
            for api in api_list:
                mock_api_stats.append({
                    'name': api['name'],
                    'path': api['path'],
                    'concurrency': random.randint(50, 500),
                    'total_requests': random.randint(1000, 50000),
                    'avg_response_time': random.uniform(20, 150),
                    'failed_requests': random.randint(0, 10)
                })

            return JsonResponse({
                'status': 'success',
                'data': {
                    'summary': mock_summary,
                    'api_stats': mock_api_stats
                }
            })

    except json.JSONDecodeError:
        logger.error("请求数据格式错误")
        return JsonResponse({
            'status': 'failed',
            'message': '请求数据格式错误'
        }, status=400)
    except Exception as e:
        logger.error(f"监控施压服务器失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'failed',
            'message': f'监控失败: {str(e)}'
        }, status=500)


def _fetch_stress_server_metrics(ip, username, password, api_list):
    """
    从施压服务器获取实际的性能指标数据

    参数:
        ip: 施压服务器IP
        username: SSH用户名
        password: SSH密码
        api_list: 要监控的接口列表 [{'name': str, 'path': str}]

    返回格式示例:
    {
        'summary': {
            'total_concurrency': 856,
            'total_requests': 125678,
            'avg_response_time': 45.2,
            'failed_requests': 12
        },
        'api_stats': [
            {
                'name': '登录接口',
                'path': '/api/login',
                'concurrency': 200,
                'total_requests': 30000,
                'avg_response_time': 35.5,
                'failed_requests': 2
            },
            ...
        ]
    }
    """
    # TODO: 根据实际压测工具实现数据获取逻辑
    #
    # 实现方案示例：
    #
    # 方案1: 如果使用 JMeter
    # - 通过 paramiko SSH连接到施压服务器
    # - 读取JMeter的CSV结果文件或JTL文件
    # - 解析每个接口的统计数据
    # - 或者调用JMeter Plugins Manager的API
    #
    # 方案2: 如果使用 Locust
    # - 调用Locust的Web API: http://stress-server:8089/stats/requests
    # - API会返回所有接口的详细统计
    # - 解析JSON并按接口路径匹配数据
    #
    # 方案3: 如果使用 wrk/ab 等命令行工具
    # - 通过SSH执行命令获取进程信息
    # - 解析输出获取每个接口的并发数和请求统计
    #
    # 方案4: 如果是自定义压测脚本
    # - 脚本需要将统计数据写入文件或数据库
    # - 通过SSH读取该文件或查询数据库
    # - 解析并返回结构化数据

    # 临时返回None，让上层函数使用模拟数据
    return None

# ==================== 辅助函数 ====================

def _is_local_ip(ip):
    """判断是否为本地IP"""
    local_ips = ['127.0.0.1', 'localhost', '0.0.0.0', '::1', 'local']
    return ip.lower() in local_ips
