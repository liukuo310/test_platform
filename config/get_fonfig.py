import yaml


class Fonfig:
    def get_config(self, app_name):
        """获取配置文件"""
        try:
            with open(f"config.yaml/{app_name}.YAML", "r", encoding="utf-8") as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
                return config
        except Exception as e:
            print(e)
