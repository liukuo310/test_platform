# Test Platform 测试平台

> 基于 Django 构建的一站式接口测试与性能测试管理平台，支持 API 管理、用例编排、持续集成任务调度以及客户端性能数据采集。

---

## ✨ 功能特性

### 🔌 接口测试平台（api_platform）

| 功能 | 描述 |
|------|------|
| **接口管理** | 创建、编辑、删除、查询接口，支持 GET/POST/PUT/DELETE 请求方式 |
| **用例管理** | 编排多个接口组成测试用例，支持发布/未发布状态管理 |
| **接口调试** | 选择测试环境（测试/开发/线上）一键运行单个接口或用例 |
| **持续集成** | 创建 CI/CD 任务，按模块/标签筛选用例批量执行，支持邮箱通知 |
| **发布管理** | 接口、用例、任务均支持发布状态切换，便于版本控制 |

### 📊 性能测试（performance）todo中

| 功能 | 描述 |
|------|------|
| **Android 性能采集** | 采集 Android 设备 CPU、内存、FPS 等性能指标 |
| **iOS 性能采集** | 采集 iOS 设备性能数据 |
| **测试报告** | 自动生成可视化性能测试报告 |

### 👤 用户中心（plat）

- 用户注册 / 登录
- Session 会话管理（基于 Redis）
- 平台首页数据概览（接口数、用例数统计）

---

## 🛠 技术栈

后端
├── Django 4.1             # Web 框架
├── Django REST Framework  # RESTful API 序列化
├── django-cors-headers    # 跨域支持
├── django-redis           # Redis 缓存 & Session 存储
├── PyMySQL / mysqlclient  # MySQL 驱动
└── PyYAML                 # YAML 配置文件解析

前端
├── TailwindCSS (CDN)      # 原子化 CSS 框架
├── jQuery 1.10.2          # DOM 操作 & Ajax
└── Font Awesome 6.x       # 图标库

数据存储
├── MySQL 5.7+             # 主数据库
└── Redis                  # 缓存 & Session

---

## 📁 项目结构
test_platform/
├── api_platform/           # 接口测试平台模块
│   ├── models.py           # Api / Case / ApiUsing / Task 模型
│   ├── views.py            # 接口 & 页面视图
│   └── urls.py
├── performance/            # 性能测试模块
│   ├── get_android_info.py # Android 设备信息采集
│   ├── get_ios_info.py     # iOS 设备信息采集
│   ├── report/             # 测试报告生成
│   ├── views.py
│   └── urls.py
├── plat/                   # 用户认证 & 平台基础
│   ├── models.py           # User 模型
│   ├── serializers.py      # DRF 序列化器
│   ├── views.py
│   └── urls.py
├── config/                 # 配置文件目录
│   ├── api_platform.YAML   # 环境配置（测试/开发/线上地址）
│   └── get_fonfig.py       # 配置读取工具类
├── templates/              # HTML 模板
│   ├── api_platform/       # 接口平台页面
│   │   ├── api_main.html   # 平台首页
│   │   ├── api_manage.html # 接口管理
│   │   ├── case_manage.html# 用例管理
│   │   └── ci_di.html      # 持续集成
│   ├── performance/        # 性能测试页面
│   └── plat/               # 登录 / 注册 / 主页
├── test_platform/          # Django 项目配置
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── static/                 # 静态资源
└── manage.py
