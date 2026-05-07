# 水质三维智能监测与分析系统

**Water Quality 3D Intelligent Monitoring & Analysis System**

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.4+-4FC08D)](https://vuejs.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1)](https://www.mysql.com/)
[![Milvus](https://img.shields.io/badge/Milvus-2.4+-00A4FF)](https://milvus.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 目录

- [项目概述](#项目概述)
- [系统架构](#系统架构)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
  - [环境要求](#环境要求)
  - [本地开发](#本地开发)
  - [Docker 部署](#docker-部署)
- [配置说明](#配置说明)
- [API 文档](#api-文档)
- [数据库设计](#数据库设计)
- [核心模块](#核心模块)
  - [数据接入](#数据接入)
  - [空间插值](#空间插值)
  - [异常检测](#异常检测)
  - [可视化](#可视化)
  - [智能检索与报告](#智能检索与报告)
- [前端](#前端)
- [测试](#测试)
- [部署运维](#部署运维)
- [常见问题](#常见问题)
- [开发规范](#开发规范)

---

## 项目概述

“巡深”水下机器人可巡航河、湖、近海等水域，采集高时空分辨率的多深度水质数据。本系统将原始 CSV 数据转化为三维可视化、异常检测报告及知识库检索，服务于水务部门、环保监测站及科研机构。

### 核心能力

| 能力 | 说明 |
|------|------|
| **自动化流水线** | 上传 CSV → 插值 → 可视化 → 异常检测 → 向量入库 → 报告生成，全程异步处理 |
| **三维认知** | Plotly 体渲染 + 等值线图，直观理解水质参数在水体中的立体分布 |
| **智能诊断** | 统计阈值 + Isolation Forest 双重异常检测，自动标注异常区域 |
| **知识复用** | Milvus 向量检索历史相似案例，LLM 生成对比分析报告 |

### 水质指标

温度（°C）、电导率（µS/cm）、盐度（‰）、pH、浊度（NTU）、叶绿素 a（µg/L）、溶解氧（mg/L）

### 用户角色

| 角色 | 权限 |
|------|------|
| 系统管理员 | 用户管理、系统配置、日志审计 |
| 数据分析师 | 数据上传、查看分析、导出报告 |
| 普通访客 | 浏览样例数据，体验功能 |

---

## 系统架构

```
┌──────────────────────────────────────────────────────────┐
│                      前端 (Vue3 + Element Plus)            │
│         UploadView  │  TaskDetailView  │  ReportView       │
│              FileDrop  │  ContourPanel  │  PointCloudFrame │
└──────────────┬───────────────────────────────────────────┘
               │ HTTP / WebSocket
┌──────────────▼───────────────────────────────────────────┐
│                   Nginx (反向代理 + 静态资源)              │
└──────────────┬───────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────┐
│                 FastAPI (app/)                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ upload   │ │  task    │ │ anomaly  │ │ report   │───┐ │
│  │controller│ │controller│ │controller│ │controller│   │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘   │ │
│       │            │            │            │           │ │
│  ┌────▼────────────▼────────────▼────────────▼─────┐     │ │
│  │                 services/                        │     │ │
│  │  data_service  │ interpolation │ anomaly_detect │     │ │
│  │  visualization │ feature_extract│ milvus_service│     │ │
│  │  report_generator │ celery_tasks                │     │ │
│  └─────────────────────────────────────────────────┘     │ │
│                         │                                 │ │
│  ┌──────────────────────▼──────────────────────────┐     │ │
│  │                 config/                          │     │ │
│  │  settings(.env) │ database(async) │ response     │     │ │
│  └─────────────────────────────────────────────────┘     │ │
└──────┬──────────┬──────────┬──────────┬──────────────────┘
       │          │          │          │
┌──────▼──┐ ┌────▼───┐ ┌───▼───┐ ┌───▼────────┐
│  MySQL  │ │ Milvus │ │ Redis │ │    MinIO    │
│ 8.0     │ │  2.4   │ │  7.x  │ │ (对象存储)  │
│ 业务数据│ │向量检索│ │消息队列│ │文件/图片    │
└─────────┘ └────────┘ └───────┘ └────────────┘
```

**数据流水线：**

```
CSV上传 → 编码检测 → 字段映射 → MySQL入库
   │
   └→ Celery异步任务:
       解析数据 → IDW插值(50×50网格/深度层) → Plotly体渲染+等值线
         → 阈值检测 + IsolationForest → OR合并异常点
         → 13维特征提取 → MinMax归一化 → Milvus插入
         → 更新任务状态(success)
              │
              └→ 用户触发: Milvus检索Top5相似案例 → DeepSeek生成DOCX → LibreOffice转PDF
```

---

## 技术栈

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **Web 框架** | FastAPI | ≥0.111 | 异步 REST API |
| **ASGI 服务器** | Uvicorn | ≥0.30 | 支持热重载 |
| **ORM** | SQLAlchemy | ≥2.0 | 异步引擎 (aiomysql) |
| **数据库** | MySQL | 8.0 | 业务数据持久化 |
| **向量数据库** | Milvus | ≥2.4 | IVF_FLAT 索引, L2 度量 |
| **消息队列** | Redis | ≥7.0 | Celery Broker + Backend |
| **异步任务** | Celery | ≥5.4 | CSV 处理流水线 |
| **对象存储** | MinIO | latest | 文件/图片存储 |
| **大模型** | DeepSeek-v4-flash | — | OpenAI 兼容 SDK |
| **前端框架** | Vue 3 | ≥3.4 | Composition API |
| **UI 组件** | Element Plus | ≥2.7 | 企业级组件库 |
| **构建工具** | Vite | ≥5.3 | HMR + 代理配置 |
| **2D 可视化** | Plotly | ≥5.22 | Contour 等值线 |
| **3D 可视化** | Plotly | ≥5.22 | Volume 体渲染 + 等值面 |
| **插值算法** | IDW / Kriging (PyKrige) | — | 空间插值 |
| **异常检测** | scikit-learn | ≥1.5 | Isolation Forest |
| **数值计算** | scipy / numpy / pandas | — | 矩阵运算 |
| **报告生成** | python-docx + LibreOffice | — | DOCX → PDF |
| **认证** | python-jose + passlib | — | JWT + bcrypt |

---

## 项目结构

```
water_analysis/
├── main.py                     # FastAPI 应用入口 (lifespan, 路由, 中间件)
├── init_db.py                  # 数据库初始化脚本 (建表 + Milvus 集合)
├── requirements.txt            # Python 依赖
├── pyproject.toml              # 项目元数据 + Pytest/Ruff 配置
├── Dockerfile                  # Docker 镜像构建
├── docker-compose.yml          # 容器编排 (7 服务)
├── nginx.conf                  # Nginx 反向代理配置
├── Makefile                    # 常用命令快捷方式
├── .env                        # 环境变量 (敏感信息, gitignore)
├── .env.example                # 环境变量模板
├── .gitignore                  # Git 忽略规则
├── .dockerignore               # Docker 构建忽略
├── .editorconfig               # 编辑器统一配置
├── README.md                   # 本文件
│
├── tests/                      # 测试套件
│   ├── conftest.py             #   pytest fixtures (async client)
│   ├── test_health.py          #   API 健康检查
│   └── test_services.py        #   插值 + 特征提取
│
└── app/                        # 应用主目录
    ├── config/                 # 配置层
    │   ├── settings.py         #   环境变量 → pydantic BaseSettings
    │   ├── database.py         #   异步引擎 + get_db() 依赖注入
    │   └── response.py         #   统一响应 ApiResponse + BusinessException
    │
    ├── models/                 # 数据模型层 (ORM)
    │   ├── __init__.py         #   自动扫描 + init_tables()
    │   ├── user.py             #   用户表
    │   ├── task.py             #   任务表 (状态机: pending→processing→success/failed)
    │   ├── raw_data.py         #   原始水质数据表
    │   └── anomaly.py          #   异常记录表
    │
    ├── schemas/                # 数据校验层 (Pydantic)
    │   ├── upload.py           #   上传请求/响应
    │   ├── task.py             #   任务状态/列表/可视化
    │   ├── anomaly.py          #   异常点查询
    │   └── report.py           #   报告生成
    │
    ├── controllers/            # 路由控制层
    │   ├── upload.py           #   POST /api/upload
    │   ├── task.py             #   GET /api/task/{id}/status|visualization + DELETE
    │   ├── anomaly.py          #   GET /api/task/{id}/anomalies
    │   └── report.py           #   POST /api/task/{id}/similar|generate_report
    │
    ├── services/               # 业务逻辑层
    │   ├── data_service.py     #   CSV 解析、编码检测、字段映射、数据入库
    │   ├── interpolation.py    #   IDW/Kriging 空间插值 (50×50 网格)
    │   ├── anomaly_detector.py #   统计阈值 + Isolation Forest 双重检测
    │   ├── feature_extractor.py#   13 维统计特征向量提取
    │   ├── milvus_service.py   #   Milvus 连接/集合/插入/检索/删除
    │   ├── visualization.py    #   Plotly 2D 等值线 + 3D 体渲染
    │   ├── report_generator.py #   LLM 分析 → DOCX → LibreOffice PDF
    │   └── celery_tasks.py     #   Celery 异步任务 (process_csv 完整流水线)
    │
    ├── utils/                  # 工具层
    │   ├── log_config.py       #   彩色日志 + TimedRotatingFileHandler
    │   ├── jwt_util.py         #   JWT 生成/验证 + 密码哈希
    │   ├── auth_middleware.py   #   Starlette 认证中间件
    │   └── exceptions.py       #   全局异常处理器
    │
    ├── frontend/               # Vue3 前端源码
    │   ├── src/
    │   │   ├── views/          #   UploadView, TaskDetailView, AnomalyView, ReportView
    │   │   ├── components/     #   FileDrop, ContourPanel, PointCloudFrame
    │   │   ├── router/         #   Vue Router 配置
    │   │   ├── api/            #   Axios API 封装
    │   │   ├── stores/         #   Pinia 状态管理
    │   │   └── App.vue         #   根组件
    │   ├── vite.config.js      #   代理配置 (/api → :8000)
    │   └── package.json        #   NPM 依赖
    │
    ├── static/                 # 静态资源
    │   └── 3d/                 #   生成的 3D 体渲染 HTML
    │
    ├── data/                   # 运行时数据
    │   ├── uploads/            #   上传的 CSV 文件
    │   ├── reports/            #   生成的 DOCX/PDF 报告
    │   └── samples/            #   样例数据集
    │
    └── logs/                   # 日志文件
        ├── app.log             #   全量日志 (按日滚动, 保留 30 天)
        └── app_error.log       #   错误日志
```

---

## 快速开始

### 环境要求

| 组件 | 最低版本 | 说明 |
|------|---------|------|
| Python | 3.11+ | 异步语法支持 |
| MySQL | 8.0 | 业务数据库 |
| Redis | 7.0+ | Celery 消息队列 |
| Milvus | 2.4+ | 向量检索 (可选, 无部署时降级) |
| Node.js | 18+ | 前端构建 (可选) |
| LibreOffice | — | PDF 转换 (可选, 无部署时仅输出 DOCX) |

### 本地开发

```bash
# 1. 克隆项目
git clone <repo-url> water_analysis
cd water_analysis

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填写 DEEPSEEK_API_KEY、MYSQL_PASSWORD 等

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库 (需先启动 MySQL 和 Milvus)
python init_db.py

# 5. 启动 Celery Worker (新终端)
celery -A app.services.celery_tasks worker --loglevel=info --concurrency=4

# 6. 启动 FastAPI 服务 (新终端)
python main.py
# 访问 http://localhost:8000/api/health 验证

# 7. 启动前端 (可选, 新终端)
cd app/frontend
npm install
npm run dev
# 访问 http://localhost:3000
```

### Docker 部署

```bash
# 一键启动全部服务 (MySQL + Redis + Milvus + MinIO + FastAPI + Celery + Nginx)
docker-compose up -d

# 查看日志
docker-compose logs -f fastapi

# 停止
docker-compose down
```

首次启动后需初始化数据库表结构：

```bash
docker-compose exec fastapi python init_db.py
```

---

## 配置说明

全部配置通过 `.env` 文件管理，`app/config/settings.py` 使用 `pydantic_settings.BaseSettings` 自动加载。

### 必填配置

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | `sk-xxx` |
| `MYSQL_HOST` | MySQL 地址 | `localhost` |
| `MYSQL_PORT` | MySQL 端口 | `3306` |
| `MYSQL_USER` | MySQL 用户 | `root` |
| `MYSQL_PASSWORD` | MySQL 密码 | `123456` |
| `MYSQL_DB` | 数据库名 | `water_quality` |

### 可选配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_PROVIDER` | LLM 提供商 | `deepseek` |
| `DEEPSEEK_MODEL` | 模型名称 | `deepseek-v4-flash` |
| `REDIS_URL` | Redis 连接 | `redis://localhost:6379/0` |
| `MILVUS_HOST` | Milvus 地址 | `localhost` |
| `MILVUS_PORT` | Milvus 端口 | `19530` |
| `USER_AUTHORIZATION` | 是否开启用户认证 | `False` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `GRID_RESOLUTION` | 插值网格分辨率 | `50` |
| `INTERPOLATION_METHOD` | 插值方法 | `idw` |
| `CONTAMINATION` | 异常检测污染率 | `0.05` |

### 空间范围（可配置）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LON_MIN` / `LON_MAX` | 经度范围 | `73` / `135` |
| `LAT_MIN` / `LAT_MAX` | 纬度范围 | `3` / `54` |
| `DEPTH_MIN` / `DEPTH_MAX` | 深度范围 (m) | `0` / `50` |

### 水质阈值

| 变量 | 默认范围 | 说明 |
|------|---------|------|
| `CHL_MIN` / `CHL_MAX` | 0.0 / 20.0 | 叶绿素 (µg/L) |
| `ODO_MIN` / `ODO_MAX` | 4.0 / 12.0 | 溶解氧 (mg/L) |
| `PH_MIN` / `PH_MAX` | 6.5 / 8.5 | pH |
| `TURB_MIN` / `TURB_MAX` | 0.0 / 10.0 | 浊度 (NTU) |
| `TEMP_MIN` / `TEMP_MAX` | 0.0 / 35.0 | 水温 (°C) |

---

## API 文档

服务启动后访问 `http://localhost:8000/docs` 查看交互式 Swagger 文档。

### 接口一览

| 方法 | 路径 | Content-Type | 说明 |
|------|------|-------------|------|
| `GET` | `/api/health` | — | 健康检查 |
| `POST` | `/api/upload` | multipart/form-data | 上传 CSV，返回 task_id |
| `GET` | `/api/task/{id}/status` | — | 查询任务状态与进度 |
| `GET` | `/api/tasks?page=1&page_size=20` | — | 分页任务列表 |
| `GET` | `/api/task/{id}/visualization?indicator=chlorophyll&depth=1` | — | 获取等值线 HTML + 体渲染 URL |
| `GET` | `/api/task/{id}/anomalies?page=1&page_size=50` | — | 分页异常点列表 |
| `GET` | `/api/task/{id}/anomalies/export` | text/csv | 导出异常点 CSV |
| `POST` | `/api/task/{id}/similar` | — | Milvus 检索 Top-5 相似案例 |
| `POST` | `/api/task/{id}/generate_report` | — | 生成 LLM 分析报告 (DOCX/PDF) |
| `DELETE` | `/api/task/{id}` | — | 删除任务及关联数据 |

### 统一响应格式

```json
{
  "status": 1,
  "messages": "操作成功",
  "datas": {}
}
```

`status=1` 成功, `status=0` 失败。业务异常通过 `BusinessException` 抛出，HTTP 状态码 404/400。

### 任务状态机

```
pending ──→ processing ──→ success
                │
                └──→ failed
```

`progress` 字段表示 0–100 的完成百分比。

---

## 数据库设计

### MySQL 表结构

**users** — 用户表
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | CHAR(36) | PK | UUID |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 哈希 |
| role | ENUM('admin', 'user') | DEFAULT 'user' | 角色 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |

**tasks** — 任务表
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | CHAR(36) | PK | UUID |
| user_id | CHAR(36) | FK → users.id | 提交用户 |
| reservoir_name | VARCHAR(100) | — | 水库名称 |
| original_filename | VARCHAR(255) | — | 原始文件名 |
| file_path | VARCHAR(500) | — | 服务器存储路径 |
| total_points | INT | — | 采样点总数 |
| anomaly_count | INT | — | 异常点数量 |
| status | ENUM('pending','processing','success','failed') | — | 任务状态 |
| progress | INT | DEFAULT 0 | 0-100 |
| created_at | DATETIME | — | 创建时间 |
| finished_at | DATETIME | — | 完成时间 |
| report_path | VARCHAR(500) | — | 报告文件路径 |

**raw_data** — 原始水质数据
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 自增主键 |
| task_id | CHAR(36), INDEXED | 关联任务 |
| lon / lat | FLOAT | 经纬度 |
| depth_m | FLOAT | 深度 (m) |
| temperature | FLOAT | 水温 (°C) |
| conductivity | FLOAT | 电导率 (µS/cm) |
| salinity | FLOAT | 盐度 (‰) |
| ph | FLOAT | pH |
| turbidity | FLOAT | 浊度 (NTU) |
| chlorophyll | FLOAT | 叶绿素 a (µg/L) |
| dissolved_oxygen | FLOAT | 溶解氧 (mg/L) |
| suspicious | BOOLEAN | 是否疑似异常 |

**anomaly_records** — 异常记录
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 自增主键 |
| task_id | CHAR(36), INDEXED | 关联任务 |
| lon / lat | FLOAT | 坐标 |
| depth | FLOAT | 深度 |
| indicator | VARCHAR(30) | 指标名 |
| value | FLOAT | 异常值 |
| method | VARCHAR(30) | 检测方法 |
| threshold_low | FLOAT | 下限阈值 |
| threshold_high | FLOAT | 上限阈值 |

### Milvus 集合

| 参数 | 值 |
|------|------|
| 集合名称 | `task_features` |
| 索引类型 | IVF_FLAT |
| 度量 | L2 |
| 维度 | 13 |
| nlist | 128 |
| 元数据 | task_id, reservoir_name, created_at |

13 维特征向量构成：5 指标均值 + 5 指标标准差 + 异常比例 + 经度方差 + 纬度方差

---

## 核心模块

### 数据接入

`app/services/data_service.py`

- 多编码自动检测：UTF-8 → GBK → GB2312 → ISO-8859-1 → latin1
- 字段名智能映射：`FIELD_ALIASES` 字典覆盖乱码/中英文表头
- 数据校验：经纬度范围、深度范围、指标范围检查
- 批量入库：`session.add_all()` 高效写入

### 空间插值

`app/services/interpolation.py`

- **IDW**：反距离加权插值 (power=2)，纯 numpy 实现
- **Kriging**：PyKrige OrdinaryKriging（球形变异函数），降级到 scipy griddata
- **网格**：50×50 分辨率，采样边界外扩 5%
- **分深度层**：独立插值，保持不同深度的空间结构

### 异常检测

`app/services/anomaly_detector.py`

- **统计阈值**：可配置的 min/max 范围，超出即标记
- **Isolation Forest**：contamination=0.05，StandardScaler 预处理
- **合并策略**：OR 逻辑取并集，(lon, lat, depth, indicator) 四元组去重

### 可视化

`app/services/visualization.py`

- **2D 等值线**：Plotly `Contour` trace，11 段 blue-white-red 色阶，支持异常点叠加标注
- **3D 体渲染**：Plotly `Volume` trace，12 层等值面，`opacity=0.2` 半透明，异常点 Scatter3d 叠加
- **回退机制**：深度层不足 2 层时自动降级为 Scatter3d 散点图
- **导出**：Kaleido PNG 导出

### 智能检索与报告

`app/services/feature_extractor.py` — 13 维 Min-Max 归一化

`app/services/milvus_service.py` — IVF_FLAT + L2 检索

`app/services/report_generator.py` — DeepSeek LLM 生成结构化分析报告：

1. 总体水质评价
2. 主要异常区域及可能原因
3. 与历史相似案例对比分析
4. 改善建议

输出 DOCX (`python-docx`) 并可选转换为 PDF (`libreoffice --headless`)。

---

## 前端

Vue3 + Vite + Element Plus，位于 `app/frontend/`。

```bash
cd app/frontend

# 开发
npm run dev          # http://localhost:3000, 自动代理 /api → :8000

# 构建
npm run build        # 输出到 dist/ (可配置 StaticFiles 直接服务)
```

### 页面路由

| 路由 | 组件 | 说明 |
|------|------|------|
| `/` | UploadView | 文件拖拽上传 + 任务创建 |
| `/task/:id` | TaskDetailView | 任务状态 + 2D/3D 可视化 |
| `/task/:id/anomalies` | AnomalyView | 异常点列表 + CSV 导出 |
| `/task/:id/report` | ReportView | 相似案例 + 报告生成 |

### 核心组件

| 组件 | 说明 |
|------|------|
| `FileDrop` | 拖拽/点击上传，进度反馈 |
| `ContourPanel` | 指标/深度选择 + Plotly 等值线 |
| `PointCloudFrame` | 指标选择 + Plotly 3D 体渲染 iframe |

---

## 测试

```bash
# 运行全部测试
pytest -v

# 指定测试文件
pytest tests/test_services.py -v

# 覆盖率
pytest --cov=app --cov-report=html
```

| 测试文件 | 覆盖内容 |
|---------|---------|
| `test_health.py` | API 健康检查端点 |
| `test_services.py` | IDW 插值、网格构建、特征向量维度验证 |

---

## 部署运维

### 日志

日志系统 (`app/utils/log_config.py`) 特性：
- **控制台**：ANSI 彩色输出（Windows/Unix）
- **文件**：`app/logs/app.log`（全量）+ `app/logs/app_error.log`（ERROR+）
- **滚动**：按日分割，保留 30 天
- **级别**：通过 `.env` 中 `LOG_LEVEL` 全局控制，支持模块级独立配置

### 健康检查

```bash
curl http://localhost:8000/api/health
# {"status":"ok","app":"水质三维智能监测与分析系统"}
```

### 数据备份

```bash
# MySQL
mysqldump -u root -p water_quality > backup_$(date +%Y%m%d).sql

# Milvus (需 milvus-backup 工具)
```

### 性能建议

- **大文件**：CSV > 10 万行建议拆分上传
- **并发**：Celery `--concurrency=4` 可根据 CPU 核数调整
- **数据库连接池**：`pool_size=20, max_overflow=10`
- **Milvus nlist**：数据量 < 10 万时 `nlist=128` 即可

---

## 常见问题

**Q: Milvus 未部署能否运行？**
A: 可以。Milvus 初始化失败时仅输出 Warning，其他功能不受影响。相似案例检索和特征入库会跳过，但不影响上传→分析→可视化这条核心链路。

**Q: LibreOffice 未安装能否生成报告？**
A: 可以。系统会生成 `.docx` 文件并直接返回，PDF 转换步骤会静默跳过。

**Q: CSV 编码乱码怎么处理？**
A: `data_service.py` 内置多编码自动检测（GBK/GB2312/UTF-8 等），并维护 `FIELD_ALIASES` 映射表覆盖常见乱码表头。

**Q: 如何切换插值方法？**
A: 在 `.env` 中设置 `INTERPOLATION_METHOD=kriging` 或通过 API 查询参数指定。

---

## 开发规范

### 代码风格

- Python：PEP 8，行宽 120，4 空格缩进
- Vue：2 空格缩进，Composition API
- 配置：`.editorconfig` 统一管理

### Git 提交规范

```bash
<type>(<scope>): <description>

# 类型: feat | fix | refactor | test | docs | chore | style
# 示例: feat(visualization): add Plotly 3D volume rendering
```

### 分支策略

- `main` — 生产分支，受保护
- `develop` — 开发分支
- `feature/*` — 功能分支
- `hotfix/*` — 紧急修复
