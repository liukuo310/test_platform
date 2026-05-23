import json


from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.generic import View
from django.db.models import Count, Q
from api_platform.models import Api, Case, ApiUsing
from plat.models import User
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def api_main_view(request):
    """测试试图函数"""
    api_counts = Api.objects.aggregate(
        all_api_count=Count('id'),
        publish_api_count=Count('id', filter=Q(publish=True))
    )
    case_counts = Case.objects.aggregate(
        all_case_count=Count('id'),
        publish_case_count=Count('id', filter=Q(publish=True))
    )
    all_api_count = api_counts['all_api_count']
    all_case_count = case_counts['all_case_count']
    publish_api_count = api_counts['publish_api_count']
    publish_case_count = case_counts['publish_case_count']
    if not all_api_count:
        all_api_count = 10
    if not all_case_count:
        all_case_count = 10
    if not publish_api_count:
        publish_api_count = 5
    if not publish_case_count:
        publish_case_count = 5
    data = {
        "all_api_count": all_api_count,
        "all_case_count": all_case_count,
        "publish_api_count": publish_api_count,
        "publish_case_count": publish_case_count
    }
    return render(request, "api_platform/api_main.html", context=data)


def api_manage_view(request):
    """接口管理页面"""
    return render(request, "api_platform/api_manage.html")


def case_manage_view(request):
    """用例管理页面"""
    return render(request, "api_platform/case_manage.html")


def ci_di(request):
    """持续集成界面"""
    return render(request, "api_platform/ci_di.html")


def create_api(request):
    """创建接口"""
    try:
        # 查看请求携带的cookies
        data = json.loads(request.body)
        acount = request.session.get("user_count")
        print(f"账号：{acount}")
        user_name = User.objects.get(count=acount).name
        api_hoster = user_name
        api_name = data.get("api_name")
        api_url = data.get("api_url")
        api_path = data.get("api_path")
        api_method = data.get("api_method", "GET")
        api_header = data.get("api_header")
        api_body = data.get("api_body")
        api_params = data.get("api_params")
        api_desc = data.get("api_desc")
        # 检查数据库中是否存在相同的接口
        if Api.objects.filter(api_path=api_path).exists() and Api.objects.filter(
                base_url=api_url).exists() and Api.objects.filter(method=api_method).exists() and Api.objects.filter(
                headers=api_header).exists() and Api.objects.filter(body=api_body).exists() and Api.objects.filter(
                params=api_params).exists():
            return JsonResponse({'message': 'API already exists'}, status=400)
        api = Api(
            name=api_name,
            hoster_name=api_hoster,
            base_url=api_url,
            api_path=api_path,
            method=api_method,
            headers=api_header,
            body=api_body,
            params=api_params,
            desc=api_desc,
            publish=False  # 默认不发布
        )
        api.save()
        return JsonResponse({'message': 'Create API successfully'}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON format'}, status=400)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)


def update_api(request):
    """更新接口"""
    data = json.loads(request.body)
    print(f"传递的参数是:{data}")
    api_id = data.get("api_id")
    if not api_id:
        return JsonResponse({'message': 'Invalid API ID'}, status=400)
    try:
        api_data = Api.objects.get(id=api_id)
    except Api.DoesNotExist:
        return JsonResponse({'message': 'API not found'}, status=404)
    for key, value in data.items():
        if key == "api_id":
            continue
        if hasattr(api_data, key):
            setattr(api_data, key, value)
    api_data.save()
    return JsonResponse({'message': "Update API successfully", "data": api_data.to_dict()}, status=200)


@csrf_exempt
def get_api(request):
    """获取接口"""
    try:
        query_params = json.loads(request.body)
        print(f"查询参数是:{query_params}")
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON format'}, status=400)
    page = int(query_params.get("page", 1))  # 不传参数情况默认为1
    page_size = int(query_params.get("page_size", 10))
    # 初始化查询集
    apis = Api.objects.all()
    # 处理查询参数
    query = Q()
    for key, value in query_params.items():
        if not value:
            continue
        if key == "page" or key == "page_size":
            continue
        if key in [field.name for field in Api._meta.fields]:
            field_name = f"{key}__icontains"
            query &= Q(**{field_name: value})
    apis_query = apis.filter(query).order_by('id')
    if not apis_query:
        return JsonResponse({'message': 'API not found'}, status=404)
    paginator = Paginator(apis_query, page_size)
    try:
        paginated_apis = paginator.page(page)
    except PageNotAnInteger:
        paginated_apis = paginator.page(1)
    except EmptyPage:
        paginated_apis = paginator.page(paginator.num_pages)
        page = paginator.num_pages
    # 将查询结果转换为字典列表
    data_list = []
    for api in paginated_apis:
        api_dict = api.to_dict()
        api_dict['id'] = api.id  # 手动添加ID字段
        data_list.append(api_dict)
    # 返回分页数据
    data = {
        "data": data_list,
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_count": paginator.count,
            "total_pages": paginator.num_pages,
            "has_next": paginated_apis.has_next(),
            "has_previous": paginated_apis.has_previous(),
            "next_page": paginated_apis.next_page_number() if paginated_apis.has_next() else None,
            "previous_page": paginated_apis.previous_page_number() if paginated_apis.has_previous() else None
        }
    }
    return JsonResponse(data, status=200)


def delete_api(request):
    """删除接口"""
    try:
        query_params = json.loads(request.body)
        api_id = query_params.get("api_id")
        if not api_id:
            return JsonResponse({'message': 'Invalid API ID'}, status=400)
        api = Api.objects.get(id=api_id)
        if not api:
            return JsonResponse({'message': 'API not found'}, status=404)
        api.delete()
        return JsonResponse({'message': 'Delete API successfully'}, status=200)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)


def update_case(request):
    """修改用例"""
    try:
        data = json.loads(request.body)
        case_id = data.get("case_id")
        if not case_id:
            return JsonResponse({'message': 'Invalid Case ID'}, status=400)
        case = Case.objects.get(id=case_id)
        # 更新用例数据
        case.name = data.get("case_name")
        case.hoster_name = data.get("case_hoster")
        case.publish = data.get("case_publish")
        case.api_ids = data.get("api_ids")
        case.annotation = data.get("case_desc")
        case.save()
    except Case.DoesNotExist:
        return JsonResponse({'message': 'Case not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON format'}, status=400)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)


def get_case(request):
    """查询用例"""
    try:
        query_params = json.loads(request.body)
        print(f"传递的参数是:{query_params}")
        page = int(query_params.get("page", 1))  # 不传参数情况默认为1
        page_size = int(query_params.get("page_size", 10))
        cases = Case.objects.all()
        query = Q()
        for key, value in query_params.items():
            if not value:  # 防止传空值
                 continue
            if key == "page" or key == "page_size":
                continue
            if key in [field.name for field in Case._meta.fields]:
                field_name = f"{key}__icontains"
                query &= Q(**{field_name: value})
        print(query)
        cases_ = cases.filter(query).order_by('id')
        if not cases_:
            return JsonResponse({'message': 'Case not found'}, status=404)
        print(f"case的值{cases_}")
        paginator = Paginator(cases_, page_size)
        try:
            paginated_cases = paginator.page(page)
        except PageNotAnInteger:
            paginated_cases = paginator.page(1)
        except EmptyPage:
            paginated_cases = paginator.page(paginator.num_pages)
            page = paginator.num_pages
        data_list = []
        for case in paginated_cases:
            api_dict = case.to_dict()
            api_dict['id'] = case.id  # 手动添加ID字段
            data_list.append(api_dict)
        data = {
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
        print(data)
        return JsonResponse(data, status=200)
    except Case.DoesNotExist:
        return JsonResponse({'message': 'Case not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON format'}, status=400)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)


def create_case(request):
    """创建用例"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON format'}, status=400)
    acount = request.session.get("user_count")
    api_all_obj = Api.objects.all()
    user_name = User.objects.get(count=acount).name
    api_id_list = []
    case = Case(
        name=data.get("case_name"),
        hoster_name=user_name,
        publish=False,
        api_ids=[],
        annotation=data.get("case_desc"),
    )
    case.save()
    api_data_list = data.get("api_data_list")
    if api_data_list:  # 允许没有借口的情况，仅创建用例
        for api_data in api_data_list:
            api_id = api_data.get("api_id")
            api_obj = api_all_obj.filter(id=api_id).first()
            api_id_list.append(api_id)
            ApiUsing.objects.create(
                case_id=case,
                api_id=api_id,
                hoster_name=user_name,
                params=api_data.get("params", api_obj.params if api_obj else ""),
                headers=api_data.get("headers", api_obj.headers if api_obj else ""),
                body=api_data.get("body", api_obj.body if api_obj else ""),
                method=api_data.get("method", api_obj.method if api_obj else "GET"),
                assert_result=api_data.get("assert_result", ""),
                globla_values=api_data.get("globla_values", ""),
            )

    case.api_ids = api_id_list
    case.save()
    return JsonResponse({'message': '用例创建成功', 'case_id': case.id})


def delete_case(request):
    """删除接口"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON format'}, status=400)
    case_id = data.get("case_id")
    if not case_id:
        return JsonResponse({'message': 'Invalid case ID'}, status=400)
    case = Case.objects.get(id=case_id)
    if not case:
        return JsonResponse({'message': 'case not found'}, status=404)
    ApiUsing.objects.filter(case_id=case_id).delete()  # 删除用例关联的接口信息
    case.delete()
    return JsonResponse({'message': 'Delete case successfully'}, status=200)

def update_using_api(request):
    """修改接口关联信息"""
    try:
        data = json.loads(request.body)
        api_using_id = data.get("api_using_id")
        if not api_using_id:
            return JsonResponse({'message': 'Invalid API Using ID'}, status=400)
        api_using = ApiUsing.objects.get(id=api_using_id)
        api_using.params = data.get("params")
        api_using.headers = data.get("headers")
        api_using.body = data.get("body")
        api_using.method = data.get("method")
        api_using.assert_result = data.get("assert_result")
        api_using.globla_values = data.get("globla_values")
        api_using.save()
        return JsonResponse({'message': '修改接口关联信息成功'}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON format'}, status=400)
    except User.DoesNotExist:
        return JsonResponse({'message': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'message': f'Internal server error: {str(e)}'}, status=500)

def create_using_api(request):
    """创建接口关联信息"""
    try:
        data = json.loads(request.body)
        acount = request.session.get("user_count")
        user_name = User.objects.get(count=acount).name
        ApiUsing.objects.create(
            case_id=data.get("case_id"),
            api_id=data.get("api_id"),
            hoster_name=user_name,
            params=data.get("params"),
            headers=data.get("headers"),
            body=data.get("body"),
            method=data.get("method"),
            assert_result=data.get("assert_result"),
            globla_values=data.get("globla_values"),
        )
        return JsonResponse({'message': '接口关联信息创建成功'}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON format'}, status=400)
    except User.DoesNotExist:
        return JsonResponse({'message': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'message': f'Internal server error: {str(e)}'}, status=500)

def delete_using_api(request):
    """删除接口关联信息"""
    try:
        data = json.loads(request.body)
        ApiUsing.objects.get(id=data.get("api_using_id")).delete()
        return JsonResponse({'message': '接口关联信息删除成功'}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON format'}, status=400)
    except User.DoesNotExist:
        return JsonResponse({'message': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'message': f'Internal server error: {str(e)}'}, status=500)

def query_using_api(request):
    """查询接口关联信息"""
    try:
        data = json.loads(request.body)
        return JsonResponse({'message': '接口关联信息查询成功', 'data': list(ApiUsing.objects.filter(case_id=data.get("case_id")).values())}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON format'}, status=400)
    except User.DoesNotExist:
        return JsonResponse({'message': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'message': f'Internal server error: {str(e)}'}, status=500)

