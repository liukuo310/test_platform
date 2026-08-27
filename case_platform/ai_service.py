import json
import logging
import requests
import os
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

    def generate_test_case_from_requirement(self, requirement_text, user_name, code_url=""):
        """
        根据需求文档或需求文字自动生成测试用例（仅生成数据，不入库）

        Args:
            requirement_text (str): 需求文档内容或需求描述文字
            user_name (str): 创建人姓名
            code_url (str): 代码地址、代码片段或本地文件路径（可选）

        Returns:
            dict: 生成的测试用例数据结构（未保存到数据库）
        """
        try:
            logger.info(f"开始根据需求生成测试用例，需求长度: {len(requirement_text)}")

            prompt = f"""
            你是一个专业的测试工程师，请根据以下需求描述生成详细的测试用例。

            需求描述：
            {requirement_text}
            """

            if code_url:
                code_content = self._read_code_content(code_url)
                prompt += f"""

            参考代码：
            {code_content}

            请结合上述代码逻辑，生成能够覆盖所有代码分支的测试用例，包括：
            1. 正常路径测试（主流程）
            2. 异常路径测试（错误处理、边界条件）
            3. 边界值测试（临界值、空值、特殊字符等）
            4. 条件分支覆盖（if/else 的所有分支）
            5. 循环边界测试（如果有循环结构）

            目标：实现 100% 的代码覆盖率
            """
            else:
                prompt += """

            要求：
            1. 至少生成 3-5 个测试用例
            2. 覆盖正常场景、异常场景和边界场景
            3. 步骤清晰明确，可执行
            4. 断言具体可验证
            """

            prompt += """

            请按照以下 JSON 格式返回测试用例数据（不要包含其他文本）：
            {
                "test_cases": [
                    {
                        "name": "测试用例名称",
                        "annotation": "用例描述",
                        "case_tag": "功能模块标签",
                        "case_setup": "前置条件",
                        "case_teardown": "后置条件",
                        "case_steps": [
                            {
                                "step_number": 1,
                                "step_description": "步骤描述",
                                "expected_result": "预期结果"
                            }
                        ],
                        "case_asserts": ""
                    }
                ]
            }

            重要要求：
            1. 只返回 JSON 格式，不要包含其他文本
            2. 确保测试用例能够覆盖所有代码路径
            3. 对于每个条件判断，都要有对应的测试用例
            4. 考虑所有可能的输入组合和边界情况
            """

            messages = [
                {"role": "system", "content": "你是专业的测试用例设计专家，擅长通过代码分析生成高覆盖率的测试用例"},
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
                    "case_asserts": case_data.get("case_asserts", ""),
                    "exec_status": {"status": "待执行"},
                    "last_update_person": user_name
                }
                generated_cases.append(test_case_data)

            coverage_info = f"（基于代码分析，目标覆盖率 100%）" if code_url else ""
            logger.info(f"成功生成 {len(generated_cases)} 个测试用例{coverage_info}")

            return {
                "success": True,
                "message": f"成功生成 {len(generated_cases)} 个测试用例{coverage_info}，请确认后创建",
                "data": generated_cases
            }

        except Exception as e:
            logger.error(f"生成测试用例失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"生成失败: {str(e)}"
            }

    def _read_code_content(self, code_path):
        """
        读取代码文件或目录的内容（支持本地路径和网络 Git URL）

        Args:
            code_path (str): 文件路径、目录路径或 Git URL

        Returns:
            str: 代码内容
        """
        try:
            if not code_path:
                return ""

            if self._is_git_url(code_path):
                return self._fetch_code_from_git(code_path)

            if not os.path.exists(code_path):
                return f"[警告] 路径不存在: {code_path}"

            if os.path.isfile(code_path):
                with open(code_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif os.path.isdir(code_path):
                code_content = []
                for root, dirs, files in os.walk(code_path):
                    for file in files:
                        if file.endswith(('.py', '.js', '.java', '.go', '.ts')):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    code_content.append(f"=== {file_path} ===\n{f.read()}\n")
                            except Exception as e:
                                code_content.append(f"[无法读取 {file_path}: {str(e)}]\n")
                return "\n".join(code_content) if code_content else "[目录为空或无可读文件]"
            else:
                return f"[无效路径]: {code_path}"
        except Exception as e:
            logger.error(f"读取代码内容失败: {str(e)}")
            return f"[读取失败]: {str(e)}"

    def _is_git_url(self, url):
        """
        判断是否为 Git URL

        Args:
            url (str): URL 字符串

        Returns:
            bool: 是否为 Git URL
        """
        return url.startswith(('http://', 'https://', 'git@')) and (
                    'github.com' in url or 'gitlab' in url or 'gitee' in url)

    def _fetch_code_from_git(self, git_url):
        """
        从 Git 仓库获取代码内容

        Args:
            git_url (str): Git 仓库 URL

        Returns:
            str: 代码内容
        """
        try:
            if git_url.startswith('git@'):
                git_url = git_url.replace('git@', 'https://').replace(':', '/')

            if 'github.com' in git_url:
                return self._fetch_from_github(git_url)
            elif 'gitee.com' in git_url:
                return self._fetch_from_gitee(git_url)
            else:
                return f"[暂不支持的 Git 平台]: {git_url}"
        except Exception as e:
            logger.error(f"从 Git 获取代码失败: {str(e)}")
            return f"[Git 获取失败]: {str(e)}"

    def _fetch_from_github(self, git_url):
        """
        从 GitHub 获取代码

        Args:
            git_url (str): GitHub 仓库 URL

        Returns:
            str: 代码内容
        """
        try:
            repo_info = self._parse_github_url(git_url)
            if not repo_info:
                return f"[无法解析 GitHub URL]: {git_url}"

            owner, repo, branch, path = repo_info

            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
            if branch:
                api_url += f"?ref={branch}"

            headers = {
                "Accept": "application/vnd.github.v3+json"
            }

            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            if isinstance(data, list):
                content_parts = []
                for item in data:
                    if item['type'] == 'file' and item['name'].endswith(('.py', '.js', '.java', '.go', '.ts')):
                        file_content = self._decode_github_file(item['download_url'])
                        content_parts.append(f"=== {item['path']} ===\n{file_content}\n")
                return "\n".join(content_parts) if content_parts else "[目录下无可读文件]"
            elif isinstance(data, dict):
                if data['type'] == 'file':
                    return self._decode_github_file(data['download_url'])
                else:
                    return f"[不支持的文件类型]: {data['type']}"
            else:
                return "[未知的响应格式]"
        except Exception as e:
            logger.error(f"从 GitHub 获取代码失败: {str(e)}")
            return f"[GitHub 获取失败]: {str(e)}"

    def _parse_github_url(self, url):
        """
        解析 GitHub URL

        Args:
            url (str): GitHub URL

        Returns:
            tuple: (owner, repo, branch, path) 或 None
        """
        try:
            url = url.rstrip('/')
            if 'github.com' not in url:
                return None

            parts = url.split('github.com/')[1].split('/')
            if len(parts) < 2:
                return None

            owner = parts[0]
            repo = parts[1]

            branch = ''
            path = ''

            if len(parts) > 4 and parts[2] == 'tree':
                branch = parts[3]
                path = '/'.join(parts[4:])
            elif len(parts) > 2:
                path = '/'.join(parts[2:])

            return owner, repo, branch, path
        except Exception as e:
            logger.error(f"解析 GitHub URL 失败: {str(e)}")
            return None

    def _decode_github_file(self, download_url):
        """
        下载并解码 GitHub 文件内容

        Args:
            download_url (str): 文件下载地址

        Returns:
            str: 文件内容
        """
        try:
            response = requests.get(download_url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            return f"[下载失败]: {str(e)}"

    def _fetch_from_gitee(self, git_url):
        """
        从 Gitee 获取代码

        Args:
            git_url (str): Gitee 仓库 URL

        Returns:
            str: 代码内容
        """
        try:
            repo_info = self._parse_gitee_url(git_url)
            if not repo_info:
                return f"[无法解析 Gitee URL]: {git_url}"

            owner, repo, branch, path = repo_info

            api_url = f"https://gitee.com/api/v5/repos/{owner}/{repo}/contents/{path}"
            params = {}
            if branch:
                params['ref'] = branch

            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if isinstance(data, list):
                content_parts = []
                for item in data:
                    if item['type'] == 'file' and item['name'].endswith(('.py', '.js', '.java', '.go', '.ts')):
                        file_content = self._decode_gitee_file(item['download_url'])
                        content_parts.append(f"=== {item['path']} ===\n{file_content}\n")
                return "\n".join(content_parts) if content_parts else "[目录下无可读文件]"
            elif isinstance(data, dict):
                if data['type'] == 'file':
                    return self._decode_gitee_file(data['download_url'])
                else:
                    return f"[不支持的文件类型]: {data['type']}"
            else:
                return "[未知的响应格式]"
        except Exception as e:
            logger.error(f"从 Gitee 获取代码失败: {str(e)}")
            return f"[Gitee 获取失败]: {str(e)}"

    def _parse_gitee_url(self, url):
        """
        解析 Gitee URL

        Args:
            url (str): Gitee URL

        Returns:
            tuple: (owner, repo, branch, path) 或 None
        """
        try:
            url = url.rstrip('/')
            if 'gitee.com' not in url:
                return None

            parts = url.split('gitee.com/')[1].split('/')
            if len(parts) < 2:
                return None

            owner = parts[0]
            repo = parts[1]

            branch = ''
            path = ''

            if len(parts) > 4 and parts[2] == 'blob':
                branch = parts[3]
                path = '/'.join(parts[4:])
            elif len(parts) > 2:
                path = '/'.join(parts[2:])

            return owner, repo, branch, path
        except Exception as e:
            logger.error(f"解析 Gitee URL 失败: {str(e)}")
            return None

    def _decode_gitee_file(self, download_url):
        """
        下载并解码 Gitee 文件内容

        Args:
            download_url (str): 文件下载地址

        Returns:
            str: 文件内容
        """
        try:
            response = requests.get(download_url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            return f"[下载失败]: {str(e)}"

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
            # 清理响应文本，移除可能的代码块标记
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
        code_url = data.get('code_url', '')

        # if len(requirement_text) < 10:
        #     return JsonResponse({
        #         'status': 'failed',
        #         'message': '需求描述过于简短，请提供更详细的信息'
        #     }, status=400)

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
        # result = {'success': True, 'message': '成功生成 5 个测试用例，请确认后创建', 'data': [{'name': '正常登录：输入正确的账号和密码', 'hoster_name': 'liukuo', 'case_models': [], 'case_tag': '登录功能', 'annotation': '验证使用合法且已注册的账号密码可成功登录', 'case_setup': '用户已在系统中注册，账号状态为启用；登录页面已 加载完成', 'case_teardown': '退出登录，清理浏览器会话（如适用）', 'case_steps': [{'step_number': 1, 'step_description': '在账号输入框中输入已注册的合法用户名（如：testuser）', 'expected_result': '账号输入框显示输入内容，无校验提示'}, {'step_number': 2, 'step_description': '在密码输入框中输入对应正确密码（如：Passw0rd!）', 'expected_result': '密码输入框显示掩码字符（•），无校验提示'}, {'step_number': 3, 'step_description': '点击【登录】按钮', 'expected_result': '跳转至首页/用户仪表盘，页面顶部显示欢迎信息及用户头像'}], 'case_asserts': '', 'exec_status': {'status': '待执行'}, 'last_update_person': 'liukuo'}, {'name': '异常场景：账号为空，密码非空', 'hoster_name': 'liukuo', 'case_models': [], 'case_tag': '登录功能', 'annotation': '验证账号为空时提交登录请求的前端校验行为', 'case_setup': '登录页面已加载完成；账号与密码输入框初始为空', 'case_teardown': '清空输入框，保持页面状态干净', 'case_steps': [{'step_number': 1, 'step_description': '清空账号输入框（确保为空字符串）', 'expected_result': '账号输入框为空'}, {'step_number': 2, 'step_description': '在密码输入框中输入任意有效密码（如：123456）', 'expected_result': '密码输入框显示掩码字符'}, {'step_number': 3, 'step_description': '点击【登录】按钮', 'expected_result': '不发起网络请求；账号输入框获得焦点；显示红色提示文本‘请输入账号’'}], 'case_asserts': '', 'exec_status': {'status': '待执行'}, 'last_update_person': 'liukuo'}, {'name': '边界场景：密码长度为最小允许值（如6位）', 'hoster_name': 'liukuo', 'case_models': [], 'case_tag': '登录功能', 'annotation': '验证密码满足最小长度限制（假设系统要求密码≥6位）时能否通过前端校验并提交', 'case_setup': '登录页面已加载；系统配置密码最小长度为6', 'case_teardown': '清空输入框', 'case_steps': [{'step_number': 1, 'step_description': '在账号输入框中输入合法账号（如：validuser）', 'expected_result': '账号输入框显示输入内容'}, {'step_number': 2, 'step_description': '在密码输入框中输入恰好6位字符（如：Abc123）', 'expected_result': '密码输入框接受输入，无实时错误提示'}, {'step_number': 3, 'step_description': '点击【登录】按钮', 'expected_result': '发起登录请求（若后端校验通过则登录成功；否则返回通用错误）'}], 'case_asserts': '', 'exec_status': {'status': '待执行'}, 'last_update_person': 'liukuo'}, {'name': '异常场景：账号格式非法（含空格开头/结尾）', 'hoster_name': 'liukuo', 'case_models': [], 'case_tag': '登录功能', 'annotation': '验证账号前后存在空白字符时的处理逻辑（应自动trim或明确提示）', 'case_setup': '登录页面已加载', 'case_teardown': '清空输入框', 'case_steps': [{'step_number': 1, 'step_description': '在账号输入框中输入‘  testuser  ’（首尾各两个空格）', 'expected_result': '输入框显示含空格的原始字符串'}, {'step_number': 2, 'step_description': '在密码输入框中输入正确密码', 'expected_result': '密码输入框显示掩码字符'}, {'step_number': 3, 'step_description': '点击【登录】按钮', 'expected_result': '前端自动去除首尾空格后提交；或显示提示‘账号不能包含首尾空格’'}], 'case_asserts': '', 'exec_status': {'status': '待执行'}, 'last_update_person': 'liukuo'}, {'name': '安全场景：密码输入框是否启用密码掩码', 'hoster_name': 'liukuo', 'case_models': [], 'case_tag': '安全合规', 'annotation': '验证密码输入框type属性为password，防止明文泄露', 'case_setup': '登录页面已加载完成', 'case_teardown': '无', 'case_steps': [{'step_number': 1, 'step_description': '检查密码输入框的HTML属性', 'expected_result': "input元素的type属性值为'password'"}], 'case_asserts': '', 'exec_status': {'status': '待执行'}, 'last_update_person': 'liukuo'}]}
        result = generator.generate_test_case_from_requirement(requirement_text, user_name, code_url)
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

