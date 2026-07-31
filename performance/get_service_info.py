"""
服务端性能数据采集模块

支持两种采集模式：
1. 本地模式：使用psutil直接采集本机性能数据
2. 远程SSH模式：通过SSH连接远程Linux/macOS服务器执行系统命令采集
"""
import time
import logging
import psutil
import paramiko

logger = logging.getLogger(__name__)


class ServicePerformanceCollector:
    """服务端性能数据采集器（支持本地和远程SSH两种模式）"""

    def __init__(self, hostname='127.0.0.1', username=None, password=None, port=22, mode='auto'):
        """
        初始化采集器

        Args:
            hostname: 服务器IP地址（本地模式可省略或填127.0.0.1）
            username: SSH用户名（本地模式可选）
            password: SSH密码（本地模式可选）
            port: SSH端口，默认22
            mode: 采集模式 'local'（本地）、'remote'（远程）、'auto'（自动识别）
        """
        self.hostname = hostname
        self.username = username or 'root'
        self.password = password
        self.port = port
        self.mode = mode
        self.ssh_client = None
        self.remote_os_type = None  # 远程服务器操作系统类型

        # 自动识别模式
        if mode == 'auto':
            self.mode = self._detect_mode()

        self.is_local = (self.mode == 'local')

    def _detect_mode(self):
        """自动检测采集模式"""
        local_ips = ['127.0.0.1', 'localhost', '0.0.0.0', '::1', 'local']
        if self.hostname.lower() in local_ips:
            return 'local'
        return 'remote'

    def connect(self):
        """建立连接（本地模式无需操作）"""
        if self.is_local:
            logger.info("本地采集模式初始化成功")
            # 测试psutil是否可用
            try:
                psutil.cpu_percent(interval=0.1)
            except Exception as e:
                logger.error(f"本地性能采集模块初始化失败: {str(e)}")
                raise
        else:
            # 远程SSH模式
            if not self.password:
                raise ValueError("远程模式需要提供密码")

            try:
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client.connect(
                    hostname=self.hostname,
                    username=self.username,
                    password=self.password,
                    port=self.port,
                    timeout=10
                )
                logger.info(f"SSH连接成功: {self.username}@{self.hostname}")

                # 检测远程操作系统类型
                self.remote_os_type = self._detect_remote_os_type()
                logger.info(f"远程服务器操作系统: {self.remote_os_type}")
            except Exception as e:
                logger.error(f"SSH连接失败: {str(e)}")
                raise

    def disconnect(self):
        """关闭连接"""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
            logger.debug(f"SSH连接已关闭: {self.hostname}")

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()

    def _execute_command(self, command):
        """
        执行SSH命令并返回结果

        Args:
            command: 要执行的shell命令

        Returns:
            str: 命令输出结果

        Raises:
            Exception: 命令执行失败时抛出异常
        """
        if self.is_local:
            raise RuntimeError("本地模式不支持SSH命令执行")

        if not self.ssh_client:
            raise ConnectionError("SSH未连接，请先调用connect()")

        stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=10)
        exit_code = stdout.channel.recv_exit_status()

        if exit_code != 0:
            error_msg = stderr.read().decode('utf-8').strip()
            raise Exception(f"命令执行失败 (exit={exit_code}): {error_msg}")

        return stdout.read().decode('utf-8').strip()

    def _detect_remote_os_type(self):
        """检测远程服务器的操作系统类型"""
        try:
            result = self._execute_command("uname -s")
            if result.lower() == 'darwin':
                return 'macos'
            elif result.lower() == 'linux':
                return 'linux'
            else:
                logger.warning(f"未识别的操作系统: {result}")
                return 'unknown'
        except Exception:
            return 'unknown'

    def collect_cpu(self):
        """
        采集CPU使用率数据

        Returns:
            dict: CPU性能指标
                - usage_percent: CPU使用率 (%)
                - cpu_count: CPU核心数
                - load_avg: 系统负载 [1min, 5min, 15min]
        """
        try:
            if self.is_local:
                return self._collect_local_cpu()
            else:
                if self.remote_os_type == 'macos':
                    return self._collect_remote_cpu_macos()
                else:
                    return self._collect_remote_cpu_linux()
        except Exception as e:
            logger.error(f"采集CPU数据失败: {str(e)}")
            raise

    def _collect_local_cpu(self):
        """本地采集CPU数据"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        load_avg = list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None

        return {
            'usage_percent': cpu_percent,
            'cpu_count': cpu_count,
            'load_avg': load_avg
        }

    def _collect_remote_cpu_linux(self):
        """Linux系统采集CPU数据"""
        # 读取 /proc/stat 计算CPU使用率
        cmd = "cat /proc/stat | head -1"
        result1 = self._execute_command(cmd)

        # 等待一小段时间再次读取以计算差值
        time.sleep(0.5)
        result2 = self._execute_command(cmd)

        # 解析CPU使用率
        def parse_cpu_stat(stat_line):
            parts = stat_line.split()
            if parts[0] != 'cpu':
                raise ValueError("Invalid CPU stat format")
            values = [int(x) for x in parts[1:]]
            total = sum(values)
            idle = values[3] if len(values) > 3 else 0
            usage = ((total - idle) / total * 100) if total > 0 else 0
            return round(usage, 2)

        cpu_usage = parse_cpu_stat(result2)

        # 获取CPU核心数
        cpu_cores = int(self._execute_command("nproc"))

        # 获取负载平均值
        load_avg_str = self._execute_command("cat /proc/loadavg")
        load_avg = [float(x) for x in load_avg_str.split()[:3]]

        return {
            'usage_percent': cpu_usage,
            'cpu_count': cpu_cores,
            'load_avg': load_avg
        }

    def _collect_remote_cpu_macos(self):
        """macOS系统采集CPU数据"""
        # 使用 top 命令获取CPU使用率
        cmd = "top -l 1 | grep 'CPU usage' | awk '{print $3}' | sed 's/%//'"
        cpu_usage_str = self._execute_command(cmd)
        cpu_usage = float(cpu_usage_str)

        # 获取CPU核心数
        cpu_cores = int(self._execute_command("sysctl -n hw.ncpu"))

        # 获取负载平均值
        load_avg_str = self._execute_command("uptime | awk -F'load averages:' '{print $2}' | awk '{print $1,$2,$3}'")
        load_avg = [float(x) for x in load_avg_str.split()]

        return {
            'usage_percent': round(cpu_usage, 2),
            'cpu_count': cpu_cores,
            'load_avg': load_avg
        }

    def collect_memory(self):
        """
        采集内存使用情况

        Returns:
            dict: 内存性能指标
                - total_mb: 总内存 (MB)
                - used_mb: 已使用内存 (MB)
                - available_mb: 可用内存 (MB)
                - usage_percent: 内存使用率 (%)
                - swap_total_mb: Swap总大小 (MB)
                - swap_used_mb: Swap已使用 (MB)
        """
        try:
            if self.is_local:
                return self._collect_local_memory()
            else:
                if self.remote_os_type == 'macos':
                    return self._collect_remote_memory_macos()
                else:
                    return self._collect_remote_memory_linux()
        except Exception as e:
            logger.error(f"采集内存数据失败: {str(e)}")
            raise

    def _collect_local_memory(self):
        """本地采集内存数据"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            'total_mb': round(mem.total / 1024 / 1024, 2),
            'used_mb': round(mem.used / 1024 / 1024, 2),
            'available_mb': round(mem.available / 1024 / 1024, 2),
            'usage_percent': mem.percent,
            'swap_total_mb': round(swap.total / 1024 / 1024, 2),
            'swap_used_mb': round(swap.used / 1024 / 1024, 2)
        }

    def _collect_remote_memory_linux(self):
        """Linux系统采集内存数据"""
        # 获取内存信息
        mem_result = self._execute_command("free -m | grep Mem")
        parts = mem_result.split()

        if len(parts) < 7:
            raise ValueError("Invalid free command output format")

        total_mb = int(parts[1])
        used_mb = int(parts[2])
        available_mb = int(parts[6])
        usage_percent = round((used_mb / total_mb * 100), 2) if total_mb > 0 else 0

        # 获取swap信息
        swap_result = self._execute_command("free -m | grep Swap || echo 'Swap: 0 0 0'")
        swap_parts = swap_result.split()

        swap_total_mb = int(swap_parts[1]) if len(swap_parts) > 1 and swap_parts[1].isdigit() else 0
        swap_used_mb = int(swap_parts[2]) if len(swap_parts) > 2 and swap_parts[2].isdigit() else 0

        return {
            'total_mb': total_mb,
            'used_mb': used_mb,
            'available_mb': available_mb,
            'usage_percent': usage_percent,
            'swap_total_mb': swap_total_mb,
            'swap_used_mb': swap_used_mb
        }

    def _collect_remote_memory_macos(self):
        """macOS系统采集内存数据"""
        # 使用 vm_stat 获取内存信息
        page_size_cmd = "pagesize"
        page_size = int(self._execute_command(page_size_cmd))

        vm_stat_cmd = "vm_stat"
        vm_stat_result = self._execute_command(vm_stat_cmd)

        # 解析 vm_stat 输出
        stats = {}
        for line in vm_stat_result.split('\n'):
            if ':' in line:
                key, value = line.split(':')
                # 清理数字中的点和空格
                clean_value = value.replace('.', '').strip()
                if clean_value.isdigit():
                    stats[key.strip()] = int(clean_value) * page_size

        # 计算内存使用情况
        total_bytes = stats.get('Pages active', 0) + stats.get('Pages inactive', 0) + \
                     stats.get('Pages wired down', 0) + stats.get('Pages free', 0)
        used_bytes = stats.get('Pages active', 0) + stats.get('Pages wired down', 0)

        total_mb = round(total_bytes / 1024 / 1024, 2)
        used_mb = round(used_bytes / 1024 / 1024, 2)
        available_mb = round((total_bytes - used_bytes) / 1024 / 1024, 2)
        usage_percent = round((used_mb / total_mb * 100), 2) if total_mb > 0 else 0

        # macOS Swap信息
        swap_used_cmd = "sysctl vm.swapusage | awk '{print $2}'"
        try:
            swap_used_bytes = int(self._execute_command(swap_used_cmd))
            swap_used_mb = round(swap_used_bytes / 1024 / 1024, 2)
        except:
            swap_used_mb = 0

        return {
            'total_mb': total_mb,
            'used_mb': used_mb,
            'available_mb': available_mb,
            'usage_percent': usage_percent,
            'swap_total_mb': swap_used_mb,
            'swap_used_mb': swap_used_mb
        }

    def collect_disk(self):
        """
        采集磁盘使用情况

        Returns:
            dict: 磁盘性能指标
                - read_mb_per_sec: 读取速度 (MB/s)
                - write_mb_per_sec: 写入速度 (MB/s)
                - total_gb: 总容量 (GB)
                - used_gb: 已使用 (GB)
                - usage_percent: 使用率 (%)
        """
        try:
            if self.is_local:
                return self._collect_local_disk()
            else:
                if self.remote_os_type == 'macos':
                    return self._collect_remote_disk_macos()
                else:
                    return self._collect_remote_disk_linux()
        except Exception as e:
            logger.error(f"采集磁盘数据失败: {str(e)}")
            raise

    def _collect_local_disk(self):
        """本地采集磁盘数据"""
        disk_io = psutil.disk_io_counters()
        disk_usage = psutil.disk_usage('/')

        read_mb = round(disk_io.read_bytes / 1024 / 1024, 2) if disk_io else 0
        write_mb = round(disk_io.write_bytes / 1024 / 1024, 2) if disk_io else 0

        return {
            'read_mb_per_sec': read_mb,
            'write_mb_per_sec': write_mb,
            'total_gb': round(disk_usage.total / 1024 / 1024 / 1024, 2),
            'used_gb': round(disk_usage.used / 1024 / 1024 / 1024, 2),
            'usage_percent': disk_usage.percent
        }

    def _collect_remote_disk_linux(self):
        """Linux系统采集磁盘数据"""
        # 获取磁盘使用情况
        df_result = self._execute_command("df -BG / | tail -1")
        df_parts = df_result.split()

        total_gb = int(df_parts[1].replace('G', ''))
        used_gb = int(df_parts[2].replace('G', ''))
        usage_percent = int(df_parts[4].replace('%', ''))

        # 尝试获取磁盘IO统计
        read_mb = 0
        write_mb = 0
        try:
            io_result = self._execute_command("iostat -d -x 1 1 | tail -n +4 | head -1")
            io_parts = io_result.split()

            if len(io_parts) >= 4:
                read_kb_s = float(io_parts[2])
                write_kb_s = float(io_parts[3])
                read_mb = round(read_kb_s / 1024, 2)
                write_mb = round(write_kb_s / 1024, 2)
        except Exception:
            logger.debug("iostat命令不可用，跳过磁盘IO采集")

        return {
            'read_mb_per_sec': read_mb,
            'write_mb_per_sec': write_mb,
            'total_gb': total_gb,
            'used_gb': used_gb,
            'usage_percent': usage_percent
        }

    def _collect_remote_disk_macos(self):
        """macOS系统采集磁盘数据"""
        # 获取磁盘使用情况
        df_result = self._execute_command("df -h / | tail -1")
        df_parts = df_result.split()

        # 解析容量（处理Gi单位）
        total_str = df_parts[1].replace('Gi', '').replace('G', '')
        used_str = df_parts[2].replace('Gi', '').replace('G', '')
        usage_percent = int(df_parts[4].replace('%', ''))

        total_gb = int(float(total_str))
        used_gb = int(float(used_str))

        # macOS获取磁盘IO
        read_mb = 0
        write_mb = 0
        try:
            io_result = self._execute_command("iostat -d -x 1 1 | grep disk0 | head -1")
            io_parts = io_result.split()

            if len(io_parts) >= 4:
                read_kb_s = float(io_parts[2])
                write_kb_s = float(io_parts[3])
                read_mb = round(read_kb_s / 1024, 2)
                write_mb = round(write_kb_s / 1024, 2)
        except Exception:
            logger.debug("iostat命令不可用，跳过磁盘IO采集")

        return {
            'read_mb_per_sec': read_mb,
            'write_mb_per_sec': write_mb,
            'total_gb': total_gb,
            'used_gb': used_gb,
            'usage_percent': usage_percent
        }

    def collect_network(self):
        """
        采集网络流量数据

        Returns:
            dict: 网络性能指标
                - bytes_sent_mb: 发送字节总数 (MB)
                - bytes_recv_mb: 接收字节总数 (MB)
                - interface: 网络接口名称
        """
        try:
            if self.is_local:
                return self._collect_local_network()
            else:
                if self.remote_os_type == 'macos':
                    return self._collect_remote_network_macos()
                else:
                    return self._collect_remote_network_linux()
        except Exception as e:
            logger.error(f"采集网络数据失败: {str(e)}")
            raise

    def _collect_local_network(self):
        """本地采集网络数据"""
        net_io = psutil.net_io_counters()

        return {
            'bytes_sent_mb': round(net_io.bytes_sent / 1024 / 1024, 2) if net_io else 0,
            'bytes_recv_mb': round(net_io.bytes_recv / 1024 / 1024, 2) if net_io else 0,
            'interface': 'local'
        }

    def _collect_remote_network_linux(self):
        """Linux系统采集网络数据"""
        # 读取网络接口统计，优先匹配常见接口名
        cmd = "cat /proc/net/dev | grep -E 'eth0|ens|enp|wlan' | head -1"
        result = self._execute_command(cmd)

        # 解析: eth0: rx_bytes rx_packets ... tx_bytes tx_packets ...
        parts = result.split(':')
        if len(parts) < 2:
            raise ValueError("Invalid network stats format")

        stats = parts[1].split()
        if len(stats) < 9:
            raise ValueError("Invalid network stats data")

        rx_bytes = int(stats[0])  # 接收字节
        tx_bytes = int(stats[8])  # 发送字节

        return {
            'bytes_sent_mb': round(tx_bytes / 1024 / 1024, 2),
            'bytes_recv_mb': round(rx_bytes / 1024 / 1024, 2),
            'interface': parts[0].strip()
        }

    def _collect_remote_network_macos(self):
        """macOS系统采集网络数据"""
        # 获取主要网络接口（通常是en0）
        try:
            # 先尝试 en0（WiFi或以太网）
            interface = 'en0'
            cmd = f"netstat -I {interface} -b | tail -1"
            result = self._execute_command(cmd)
            parts = result.split()

            if len(parts) >= 10:
                rx_bytes = int(parts[6])  # 接收字节
                tx_bytes = int(parts[9])  # 发送字节

                return {
                    'bytes_sent_mb': round(tx_bytes / 1024 / 1024, 2),
                    'bytes_recv_mb': round(rx_bytes / 1024 / 1024, 2),
                    'interface': interface
                }
        except Exception:
            pass

        # 备用方法：尝试 en1
        try:
            interface = 'en1'
            cmd = f"netstat -I {interface} -b | tail -1"
            result = self._execute_command(cmd)
            parts = result.split()

            if len(parts) >= 10:
                rx_bytes = int(parts[6])
                tx_bytes = int(parts[9])

                return {
                    'bytes_sent_mb': round(tx_bytes / 1024 / 1024, 2),
                    'bytes_recv_mb': round(rx_bytes / 1024 / 1024, 2),
                    'interface': interface
                }
        except Exception:
            pass

        # 如果都失败，返回默认值
        return {
            'bytes_sent_mb': 0,
            'bytes_recv_mb': 0,
            'interface': 'unknown'
        }

    def collect_all(self, data_types=None):
        """
        采集所有指定类型的性能数据

        Args:
            data_types: 要采集的数据类型列表，如 ['cpu', 'memory']
                       如果为None则采集所有类型

        Returns:
            dict: 各类型性能数据
        """
        if data_types is None:
            data_types = ['cpu', 'memory', 'disk', 'network']

        collectors = {
            'cpu': self.collect_cpu,
            'memory': self.collect_memory,
            'disk': self.collect_disk,
            'network': self.collect_network
        }

        result = {}
        errors = {}

        for data_type in data_types:
            if data_type not in collectors:
                logger.warning(f"不支持的数据类型: {data_type}")
                continue

            try:
                result[data_type] = collectors[data_type]()
            except Exception as e:
                errors[data_type] = str(e)
                logger.error(f"采集{data_type}数据失败: {str(e)}")

        if errors:
            result['_errors'] = errors

        return result


# 便捷函数：一次性采集（适用于简单场景）
def collect_performance_data(hostname='127.0.0.1', username=None, password=None,
                            data_types=None, port=22, mode='auto'):
    """
    便捷函数：采集服务器性能数据（自动识别本地/远程）

    Args:
        hostname: 服务器IP（127.0.0.1为本地）
        username: SSH用户名（本地可选）
        password: SSH密码（本地可选）
        data_types: 要采集的数据类型列表
        port: SSH端口
        mode: 采集模式 'local'/'remote'/'auto'

    Returns:
        dict: 性能数据
    """
    with ServicePerformanceCollector(hostname, username, password, port, mode) as collector:
        return collector.collect_all(data_types)


if __name__ == '__main__':
    # 测试本地采集
    print("=" * 50)
    print("测试本地采集模式")
    print("=" * 50)
    local_info = collect_performance_data(mode='local')
    print(local_info)

    # 测试远程采集
    print("\n" + "=" * 50)
    print("测试远程SSH采集模式")
    print("=" * 50)
    try:
        remote_info = collect_performance_data(
            hostname='192.168.1.9',
            username='kuoliu',
            password='123456',
            mode='remote'
        )
        print(remote_info)
    except Exception as e:
        print(f"远程采集失败: {e}")
