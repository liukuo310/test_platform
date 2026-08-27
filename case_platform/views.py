import json
import logging

from django.db.models.query_utils import Q
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from case_platform.models import TestCase
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from case_platform.ai_service import generate_test_case_view


logger = logging.getLogger(__name__)


def test_case_view(request):
    return render(request, 'case_platform/case_main.html')


def ai_complete_view(request):
    return render(request, 'case_platform/ai_complete.html')


def batch_import_view(request):
    return render(request, 'case_platform/batch_import.html')


def create_test_case(request):
    try:
        data = json.loads(request.body)

        # 判断是批量创建还是单个创建
        if isinstance(data, list):
            # 批量创建（AI生成的用例列表）
            if len(data) == 0:
                return JsonResponse({
                    'status': 'failed',
                    'message': '用例列表不能为空'
                }, status=400)

            created_cases = []
            failed_cases = []

            for index, case_data in enumerate(data):
                try:
                    print(case_data)
                    test_case = TestCase.objects.create(
                        name=case_data.get('name'),
                        hoster_name=case_data.get('hoster_name'),
                        case_models=case_data.get('models', []),
                        case_tag=case_data.get('tag'),
                        annotation=case_data.get('annotation'),
                        case_setup=case_data.get('case_setup'),
                        case_teardown=case_data.get('case_teardown'),
                        case_steps=case_data.get('case_steps', []),
                        case_asserts=case_data.get('case_asserts', ""),
                        exec_status=case_data.get('exec_status', {}),
                        last_update_person=case_data.get('last_update_person', '')
                    )
                    created_cases.append(test_case.to_dict())
                except Exception as e:
                    logger.error(f"创建第 {index + 1} 个用例失败: {str(e)}")
                    failed_cases.append({
                        'index': index,
                        'name': case_data.get('name', '未知'),
                        'error': str(e)
                    })

            # 返回批量创建结果
            return JsonResponse({
                'status': 'success',
                'message': f'批量创建完成：成功 {len(created_cases)} 个，失败 {len(failed_cases)} 个',
                'data': {
                    'success_count': len(created_cases),
                    'failed_count': len(failed_cases),
                    'case_ids': [case['case_id'] for case in created_cases],
                    'cases': created_cases,
                    'failed_details': failed_cases
                }
            })

        elif isinstance(data, dict):
            # 单个创建（手动填写或前端逐个创建）
            test_case = TestCase.objects.create(
                name=data.get('name'),
                hoster_name=data.get('hoster_name'),
                case_models=data.get('models', []),
                case_tag=data.get('tag'),
                annotation=data.get('annotation'),
                case_setup=data.get('case_setup'),
                case_teardown=data.get('case_teardown'),
                case_steps=data.get('case_steps', []),
                case_asserts=data.get('case_asserts', ""),
                exec_status=data.get('exec_status', {}),
                last_update_person=data.get('last_update_person', '')
            )

            return JsonResponse({
                'status': 'success',
                'message': '创建成功',
                'data': {
                    'case_id': test_case.case_id
                }
            })

        else:
            return JsonResponse({
                'status': 'failed',
                'message': '数据格式错误，必须是对象或数组'
            }, status=400)

    except json.JSONDecodeError:
        logger.error("JSON格式错误")
        return JsonResponse({
            'status': 'failed',
            'message': 'JSON格式错误'
        }, status=400)
    except Exception as e:
        logger.error(f"创建测试用例失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'failed',
            'message': f'服务器内部错误: {str(e)}'
        }, status=500)


def delete_test_case(request):
    try:
        data = json.loads(request.body)
        case_id = data.get('case_id')

        if not case_id:
            return JsonResponse({
                'status': 'failed',
                'message': '缺少用例ID'
            }, status=400)

        try:
            test_case = TestCase.objects.get(case_id=case_id)
            test_case.delete()
            return JsonResponse({
                'status': 'success',
                'message': '删除成功'
            })
        except TestCase.DoesNotExist:
            return JsonResponse({
                'status': 'failed',
                'message': '测试用例不存在'
            }, status=404)

    except json.JSONDecodeError:
        logger.error("JSON格式错误")
        return JsonResponse({
            'status': 'failed',
            'message': 'JSON格式错误'
        }, status=400)
    except Exception as e:
        logger.error(f"删除测试用例失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'failed',
            'message': f'服务器内部错误: {str(e)}'
        }, status=500)


def update_test_case(request):
    try:
        data = json.loads(request.body)
        case_id = data.get('case_id')

        if not case_id:
            return JsonResponse({
                'status': 'failed',
                'message': '缺少用例ID'
            }, status=400)

        try:
            test_case = TestCase.objects.get(case_id=case_id)

            if 'name' in data:
                test_case.name = data['name']
            if 'hoster_name' in data:
                test_case.hoster_name = data['hoster_name']
            if 'models' in data:
                test_case.case_models = data['models']
            if 'tag' in data:
                test_case.case_tag = data['tag']
            if 'annotation' in data:
                test_case.annotation = data['annotation']
            if 'case_setup' in data:
                test_case.case_setup = data['case_setup']
            if 'case_teardown' in data:
                test_case.case_teardown = data['case_teardown']
            if 'case_steps' in data:
                test_case.case_steps = data['case_steps']
            if 'case_asserts' in data:
                test_case.case_asserts = data['case_asserts']
            if 'exec_status' in data:
                test_case.exec_status = data['exec_status']
            if 'last_update_person' in data:
                test_case.last_update_person = data['last_update_person']

            test_case.save()

            return JsonResponse({
                'status': 'success',
                'message': '更新成功'
            })
        except TestCase.DoesNotExist:
            return JsonResponse({
                'status': 'failed',
                'message': '测试用例不存在'
            }, status=404)

    except json.JSONDecodeError:
        logger.error("JSON格式错误")
        return JsonResponse({
            'status': 'failed',
            'message': 'JSON格式错误'
        }, status=400)
    except Exception as e:
        logger.error(f"更新测试用例失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'failed',
            'message': f'服务器内部错误: {str(e)}'
        }, status=500)


def get_test_case(request):
    try:

        query_params = json.loads(request.body)
        case_id = query_params.get("case_id")
        if case_id:
            try:
                test_case = TestCase.objects.get(case_id=case_id)
                return JsonResponse({
                    'status': 'success',
                    'data': test_case.to_dict()
                })
            except TestCase.DoesNotExist:
                return JsonResponse({
                    'status': 'failed',
                    'message': '测试用例不存在'
                }, status=404)
        page = int(query_params.get("page", 1))  # 不传参数情况默认为1
        page_size = int(query_params.get("page_size", 10))
        cases = TestCase.objects.all()
        query = Q()
        for key, value in query_params.items():
            if not value:
                continue
            if key == "page" or key == "page_size":
                continue
            if key in [field.name for field in TestCase._meta.fields]:
                query &= Q(**{key: value})
        case_query = cases.filter(query).order_by("-case_id")
        paginator = Paginator(case_query, page_size)
        try:
            paginated_cases = paginator.page(page)
        except PageNotAnInteger:
            paginated_cases = paginator.page(1)
        except EmptyPage:
            paginated_cases = paginator.page(paginator.num_pages)
            page = paginator.num_pages
        # 将查询结果转换为字典列表
        data_list = []
        for case in paginated_cases:
            api_dict = case.to_dict()
            data_list.append(api_dict)
        data = {
            "status": "success",
            "data": data_list,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_count": paginator.count,
                "total_pages": paginator.num_pages,
                "has_next": paginated_cases.has_next(),
                "has_previous": paginated_cases.has_previous(),
                "next_page": paginated_cases.next_page_number() if paginated_cases.has_next() else None,
                "previous_page": paginated_cases.previous_page_number() if paginated_cases.has_previous() else None
            }
        }
        return JsonResponse(data, status=200)
    except json.JSONDecodeError:
        logger.error("JSON格式错误")
        return JsonResponse({
            'status': 'failed',
            'message': 'JSON格式错误'
        }, status=400)
    except Exception as e:
        logger.error(f"获取测试用例失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'failed',
            'message': f'服务器内部错误: {str(e)}'
        }, status=500)


def generate_test_case(request):
    """根据需求自动生成测试用例（转发到 ai_service）"""
    print(request.body)
    return generate_test_case_view(request)
