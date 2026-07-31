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
            # 支持：IPv4、localhost、域名
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$|^localhost$|^[a-zA-Z0-9][a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
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

            # 测试SSH连接
            try:
                with ServicePerformanceCollector(ip_addr, username, password, mode='remote') as collector:
                    test_data = collector.collect_cpu()  # 尝试链接一下
                    os_type = collector.remote_os_type

                    # 记录服务器信息
                    logger.info(f"远程服务器类型: {os_type}, IP: {                                                          ip_addr}")

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

        # 初始化时间戳和计数器
        request.session["start_time"] = time.time()
        request.session["frame_count"] = 0

        mode_text = "本地" if is_local else f"远程({username}@{ip_addr})"
        logger.info(f"性能抓取配置初始化成功 - 模式: {mode_text}, 类型: {data_type_list}")

        return JsonResponse({
            'status': 'success',
            'message': f'配置初始化成功（{mode_text}模式）',
            'session_id': request.session.session_key,
            'config': {
                'service_ip': service_ip,
                'mode': 'local' if is_local else 'remote',
                'data_types': data_type_list
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

        # 清理session数据（包括敏感信息）
        request.session.pop("service_ip", None)
        request.session.pop("service_username", None)
        request.session.pop("service_password", None)
        request.session.pop("data_type_list", None)
        request.session.pop("start_time", None)
        request.session.pop("frame_count", None)
        request.session.pop("is_local", None)

        duration = round(time.time() - start_time, 2) if start_time else 0
        mode_text = "本地" if is_local else "远程"

        logger.info(f"性能采集结束 - {mode_text}{service_ip} - 总帧数: {frame_count}, 持续时间: {duration}秒")

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


# ==================== 辅助函数 ====================

def _is_local_ip(ip):
    """判断是否为本地IP"""
    local_ips = ['127.0.0.1', 'localhost', '0.0.0.0', '::1', 'local']
    return ip.lower() in local_ips
