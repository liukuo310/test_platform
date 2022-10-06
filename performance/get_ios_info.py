from performance.utils import doc_shell
from tidevice._perf import DataType, iter_network_flow
import copy
import os
import time
import tidevice
import queue

PATH = os.path.dirname(os.path.abspath(__file__))


def get_pid(name="Lamour") -> str:
    """获得pid"""
    result = doc_shell("python -m tidevice ps")
    for app_result in result.split("\n")[:-1]:
        app_result_list = app_result.split()
        if app_result_list[1] == name:
            return app_result_list[0]
    else:
        return "没有"


class IosInfo:
    def __init__(self, pack_name, cpu_q, fps_q, net_q, mem_q):
        self.report = {
            "cpu": {"app_value": [], "sys_value": [], "timestamp": []},
            "fps": {"fps_data": [], "timestamp": []},
            "mem": {"mem_data": [], "timestamp": []},
            "net": {"downFlow": [], "upFlow": [], "timestamp": []}
        }  # 日志数据
        self.q = queue.Queue()
        self.t = tidevice.Device()
        self.pack_name = pack_name
        self.cpu_q = cpu_q
        self.fps_q = fps_q
        self.net_q = net_q
        self.mem_q = mem_q
        self.screen_value_list = []
        self.perf = tidevice.Performance(self.t, [DataType.CPU,
                                        DataType.MEMORY,
                                        DataType.NETWORK,
                                        DataType.FPS,
                                        DataType.PAGE]
                                        # DataType.SCREENSHOT]
                                         )

    def callback(self, _type: tidevice.DataType, value: dict):
        """收集性能回执函数"""
        timestamp = value['timestamp']
        value['timestamp'] = self.get_now_time(timestamp)
        if _type.value == "cpu":
            self.cpu_q.put(value)
        elif _type.value == "fps":
            self.fps_q.put(value)
        elif _type.value == "memory":
            self.mem_q.put(value)
        elif _type.value == "network":
            self.net_q.put(value)
        elif _type.value == "screenshot":
            self.screen_value_list.extend(value)
        else:
            pass

    def get_cpu_info(self):
        """获得cpu性能情况"""
        cpu_data = []
        sys_data = []
        timestamp = []
        while not self.cpu_q.empty():
            data = self.cpu_q.get()
            cpu_data.append(data.get("value"))
            sys_data.append(data.get('sys_value'))
            timestamp.append(data.get("timestamp"))
        if len(cpu_data) != 0:
            self.report["cpu"]["app_value"].extend(cpu_data)
            self.report["cpu"]["sys_value"].extend(sys_data)
            self.report["cpu"]["timestamp"].extend(timestamp)
            return {"cpu": {"app_value": cpu_data, "sys_value": sys_data, "timestamp": timestamp}}

    def get_fps_info(self):
        """获得fps性能数据:"""
        fps_data = []
        timestamp = []
        while not self.fps_q.empty():
            data = self.fps_q.get()
            fps_data.append(data.get('fps'))
            timestamp.append(data.get("timestamp"))
        if len(fps_data) != 0:
            self.report["fps"]["fps_data"].extend(fps_data)
            self.report["fps"]["timestamp"].extend(timestamp)
            return {"fps": {"fps_data": fps_data, "timestamp": timestamp}}

    def get_mem_info(self):
        """获得内存性能数据"""
        mem_data = []
        timestamp = []
        while not self.mem_q.empty():
            data = self.mem_q.get()
            mem_data.append(data.get('value'))
            timestamp.append(data.get("timestamp"))
        if len(mem_data) != 0:
            self.report["mem"]["mem_data"].extend(mem_data)
            self.report["mem"]["timestamp"].extend(timestamp)
            return {"mem": {"mem_data": mem_data, "timestamp": timestamp}}

    def get_net_info(self):
        """获得网络性能数据"""
        down_net = []
        up_net = []
        timestamp = []
        now_time = time.time()
        time_local = time.localtime(now_time)
        request_timestamp = time.strftime("%H:%M:%S", time_local)
        while not self.net_q.empty():
            data = self.net_q.get()
            down_net.append(data.get('downFlow'))
            up_net.append(data.get('upFlow'))
            timestamp.append(data.get("timestamp"))
        if len(up_net) != 0:
            avg_up_net = sum(up_net)/len(up_net)
            avg_down_net = sum(down_net)/len(down_net)
            self.report["net"]["downFlow"].append(avg_down_net)
            self.report["net"]["upFlow"].append(avg_up_net)
            self.report["net"]["timestamp"].append(request_timestamp)
            return {"net": {"downFlow": avg_down_net, "upFlow": avg_up_net, "timestamp": request_timestamp}}

    def ios_screen(self):
        """收集ios设备截图"""
        for screen_value in self.screen_value_list:
            photo_path = r"C:\Users\Administrator\Desktop\performance\info\3.11.0\photo_stats\ios_screec" + f"\\{screen_value['timestamp']}.png"
            screen_value["value"].save(photo_path)

    def start_collect(self):
        """开始收集"""
        self.perf.start(self.pack_name, callback=self.callback)

    def stop_collect(self):
        """结束收集"""
        self.perf.stop()

    @staticmethod
    def get_now_time(stimestamp) -> str:
        """获得内部转转的时间戳"""
        now_time = int(str(stimestamp)[:-3])
        time_local = time.localtime(now_time)
        dt = time.strftime("%H:%M:%S", time_local)
        return dt

    def get_report_data(self):
        """生成日志文件"""
        report_data = copy.deepcopy(self.report)
        self.report = {
            "cpu": {"app_value": [], "sys_value": [], "timestamp": []},
            "fps": {"fps_data": [], "timestamp": []},
            "mem": {"mem_data": [], "timestamp": []},
            "net": {"downFlow": [], "upFlow": [], "timestamp": []}
        }  # 初始化日志数据
        return report_data


if __name__ == '__main__':
    cpu_q = queue.Queue()
    fps_q = queue.Queue()
    net_q = queue.Queue()
    mem_q = queue.Queue()
    co = IosInfo("inhouse.dhn.amour", cpu_q, fps_q, net_q, mem_q)
    co.start_collect()
    while True:
        # print("一帧的值是", co.get_cpu_info())
        time.sleep(2)




