import json
import logging
import requests
from django.http import JsonResponse
from case_platform.models import TestCase
from plat.models import User

logger = logging.getLogger(__name__)


class AITestCaseGenerator:
    """AI 测试用例生成服务类"""

    def __init__(self, api_key=None, model=None, api_url=None):
        self.api_key = "sk-ws-H.EILLXHR.ZOhD.MEUCIQCsjv_Qc05jQSGpFu-2vkgLm3Ovv6uUSzLVM1L5SSav0QIgIS5mOn0eRROH5rMrIFiL_I5VASumduJRDDi0cbf1L64"
        self.model = model or "qwen-plus"
        self.api_url = api_url or "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

    def generate_test_case_from_requirement(self, requirement_text, user_name):
        """
        根据需求文档或需求文字自动生成测试用例（仅生成数据，不入库）

        Args:
            requirement_text (str): 需求文档内容或需求描述文字
            user_name (str): 创建人姓名

        Returns:
            dict: 生成的测试用例数据结构（未保存到数据库）
        """
        try:
            logger.info(f"开始根据需求生成测试用例，需求长度: {len(requirement_text)}")

            prompt = f"""
            你是一个专业的测试工程师，请根据以下需求描述，生成详细的测试用例。
            
            需求描述：
            {requirement_text}
            
            请按照以下 JSON 格式返回测试用例数据（不要包含 markdown 格式）：
            {{
                "test_cases": [
                    {{
                        "name": "测试用例名称",
                        "annotation": "用例描述",
                        "case_tag": "功能模块标签",
                        "case_setup": "前置条件",
                        "case_teardown": "后置条件",
                        "case_steps": [
                            {{
                                "step_number": 1,
                                "step_description": "步骤描述",
                                "expected_result": "预期结果"
                            }}
                        ],
                        "case_asserts": [
                            {{
                                "assert_type": "响应断言",
                                "assert_field": "字段名",
                                "expected_value": "期望值"
                            }}
                        ]
                    }}
                ]
            }}
            
            要求：
            1. 至少生成 3-5 个测试用例
            2. 覆盖正常场景、异常场景和边界场景
            3. 步骤清晰明确，可执行
            4. 断言具体可验证
            5. 只返回 JSON 格式，不要包含其他文本
            """

            messages = [
                {"role": "system", "content": "你是专业的测试用例设计专家"},
                {"role": "user", "content": prompt}
            ]

            ai_response = self._call_ai_api(messages)

            parsed_data = self._parse_ai_response(ai_response)

            # 生成测试用例数据（不保存到数据库）
            generated_cases = []
            for case_data in parsed_data.get("test_cases", []):
                test_case_data = {
                    "name": case_data.get("name", "自动生成的用例"),
                    "hoster_name": user_name,
                    "case_models": [],
                    "case_tag": case_data.get("case_tag", "AI生成"),
                    "annotation": case_data.get("annotation", ""),
                    "case_setup": case_data.get("case_setup", ""),
                    "case_teardown": case_data.get("case_teardown", ""),
                    "case_steps": case_data.get("case_steps", []),
                    "case_asserts": case_data.get("case_asserts", []),
                    "exec_status": {"status": "待执行"},
                    "last_update_person": user_name
                }
                generated_cases.append(test_case_data)

            logger.info(f"成功生成 {len(generated_cases)} 个测试用例（待确认）")

            return {
                "success": True,
                "message": f"成功生成 {len(generated_cases)} 个测试用例，请确认后创建",
                "data": generated_cases
            }

        except Exception as e:
            logger.error(f"生成测试用例失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"生成失败: {str(e)}"
            }


    def _call_ai_api(self, messages):
        """
        调用 AI API

        Args:
            messages: 对话消息列表

        Returns:
            str: AI 返回的文本
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 3000
            }

            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            logger.error(f"调用 AI API 网络请求失败: {str(e)}", exc_info=True)
            raise Exception(f"AI API 调用失败: {str(e)}")
        except KeyError as e:
            logger.error(f"解析 AI API 响应失败: {str(e)}", exc_info=True)
            raise Exception(f"AI API 响应格式错误: {str(e)}")
        except Exception as e:
            logger.error(f"调用 AI API 未知错误: {str(e)}", exc_info=True)
            raise

    def _parse_ai_response(self, response_text):
        """
        解析 AI 返回的响应

        Args:
            response_text (str): AI 返回的文本

        Returns:
            dict: 解析后的 JSON 数据
        """
        try:
            # 清理响应文本，移除可能的 markdown 代码块标记
            cleaned_text = response_text.strip()

            # 移除可能的 ```json 或 ``` 开头和结尾
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            elif cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]

            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]

            cleaned_text = cleaned_text.strip()

            # 解析 JSON
            parsed_json = json.loads(cleaned_text)

            # 验证必要字段
            if "test_cases" not in parsed_json:
                raise ValueError("AI 返回的数据缺少 test_cases 字段")

            if not isinstance(parsed_json["test_cases"], list):
                raise ValueError("test_cases 字段必须是数组")

            logger.info(f"成功解析 AI 响应，包含 {len(parsed_json['test_cases'])} 个测试用例")

            return parsed_json

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {str(e)}")
            logger.error(f"原始响应: {response_text[:500]}...")
            raise ValueError(f"AI 返回的数据格式不正确，无法解析为 JSON: {str(e)}")
        except Exception as e:
            logger.error(f"解析 AI 响应时发生错误: {str(e)}", exc_info=True)
            raise

def generate_test_case_view(request):
    """
    根据需求生成测试用例的视图接口

    请求方法: POST
    请求体:
    {
        "requirement_text": "需求描述文字...",
        "api_key": "可选的 API Key"
    }
    """
    if request.method != 'POST':
        return JsonResponse({
            'status': 'failed',
            'message': '仅支持 POST 请求'
        }, status=405)

    try:
        data = json.loads(request.body)
        requirement_text = data.get('requirement_text')
        if not requirement_text:
            return JsonResponse({
                'status': 'failed',
                'message': '缺少需求描述'
            }, status=400)

        if len(requirement_text) < 10:
            return JsonResponse({
                'status': 'failed',
                'message': '需求描述过于简短，请提供更详细的信息'
            }, status=400)

        user_count = request.session.get("user_count")
        if not user_count:
            return JsonResponse({
                'status': 'failed',
                'message': '用户未登录'
            }, status=401)

        try:
            user = User.objects.get(count=user_count)
            user_name = user.name
        except User.DoesNotExist:
            return JsonResponse({
                'status': 'failed',
                'message': '用户不存在'
            }, status=404)

        api_key = data.get('api_key')
        if not api_key:  # 暂时用做测试todo:后续有key在使用
            api_key = "sk-ws-H.EILLXHR.ZOhD.MEUCIQCsjv_Qc05jQSGpFu-2vkgLm3Ovv6uUSzLVM1L5SSav0QIgIS5mOn0eRROH5rMrIFiL_I5VASumduJRDDi0cbf1L64"
        if not api_key:
            from django.conf import settings
            api_key = getattr(settings, 'AI_API_KEY', None)

        if not api_key:
            return JsonResponse({
                'status': 'failed',
                'message': '请提供 AI API Key 或在 settings.py 中配置 AI_API_KEY'
            }, status=400)

        generator = AITestCaseGenerator(api_key=api_key)

        result = generator.generate_test_case_from_requirement(requirement_text, user_name)
        print("结果")
        print(result)
        if result['success']:
            return JsonResponse({
                'status': 'success',
                'message': result['message'],
                'data': result['data']
            }, status=201)
        else:
            return JsonResponse({
                'status': 'failed',
                'message': result['message']
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'failed',
            'message': 'JSON 格式错误'
        }, status=400)
    except Exception as e:
        logger.error(f"生成测试用例接口异常: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'failed',
            'message': f'服务器内部错误: {str(e)}'
        }, status=500)

