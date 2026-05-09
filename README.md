# 水质三维智能监测与分析系统

**Water Quality 3D Intelligent Monitoring & Analysis System**

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.4+-4FC08D)](https://vuejs.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1)](https://www.mysql.com/)
[![Milvus](https://img.shields.io/badge/Milvus-2.4+-00A4FF)](https://milvus.io/)

---

## 目录

- [项目概述](#项目概述)
- [系统架构](#系统架构)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [用户认证](#用户认证)
- [API 文档](#api-文档)
- [数据库设计](#数据库设计)
- [核心模块](#核心模块)
- [Milvus 策略](#milvus-策略)
- [前端](#前端)
- [测试](#测试)
- [部署运维](#部署运维)

---

## 项目概述

"巡深"水下机器人巡航河、湖、近海等水域，采集高时空分辨率的多深度水质数据。本系统将 CSV 数据转化为三维可视化、异常检测报告及知识库检索。

### 核心能力

| 能力 | 说明 |
|------|------|
| **自动化流水线** | 上传 CSV → 插值 → 可视化 → 异常检测 → 向量入库 → 报告生成，Celery 异步处理 |
| **三维可视化** | Plotly 体渲染 + 等值线图，直观理解水质参数在水体中的立体分布 |
| **双重异常检测** | 统计阈值 + Isolation Forest，自动标注并去重异常区域 |
| **知识复用** | Milvus 向量检索历史相似案例，LLM 生成对比分析报告 |
| **抗阻塞设计** | 启动不加载 Milvus 数据，熔断器 + 独立线程池 + 全链路超时 |

### 水质指标

温度（°C）、电导率（µS/cm）、盐度（‰）、pH、浊度（NTU）、叶绿素 a（µg/L）、溶解氧（mg/L）

---

## 系统架构

```
┌──────────────────────────────────────────────────────────┐
│                   前端 (Vue 3 + Element Plus)              │
│    Dashboard │ Upload │ TaskList │ TaskDetail │ Anomaly   │
│    Report │ Compare │ Map │ UserManage                     │
│    FileDrop  │  ContourPanel  │  PointCloudFrame           │
└──────────────┬───────────────────────────────────────────┘
               │ HTTP (Vite dev proxy / Nginx production)
┌──────────────▼───────────────────────────────────────────┐
│                 FastAPI (app/)                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ upload   │ │  task    │ │ anomaly  │ │ report   │───┐ │
│  │ router   │ │ router   │ │ router   │ │ router   │   │ │
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
│  │         config/  │  middlewares/  │  handlers/   │     │ │
│  │  settings  │ database  │ response  │ logging     │     │ │
│  └─────────────────────────────────────────────────┘     │ │
└──────┬──────────┬──────────┬──────────────────────────────┘
       │          │          │
┌──────▼──┐ ┌────▼───┐ ┌───▼───┐
│  MySQL  │ │ Milvus │ │ Redis │
│ 8.0     │ │  2.4   │ │  7.x  │
│ 业务数据│ │向量检索│ │消息队列│
└─────────┘ └────────┘ └───────┘
```

**数据流水线：**

```
CSV 上传 → 编码检测 → 字段映射 → MySQL 入库
   │
   └→ Celery 异步任务:
       解析数据 → IDW 插值 (50×50 网格/深度层) → Plotly 体渲染 + 等值线
         → 阈值检测 + IsolationForest → OR 合并异常点
         → 13 维特征提取 → MinMax 归一化 → Milvus 插入
         → 更新任务状态 (success)
              │
              └→ 用户触发: Milvus 检索 Top-5 相似案例 → DeepSeek 生成 DOCX → LibreOffice PDF
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
| **大模型** | DeepSeek-v4-pro | — | OpenAI 兼容 SDK |
| **前端框架** | Vue 3 | ≥3.4 | Composition API |
| **UI 组件** | Element Plus | ≥2.7 | 企业级组件库 |
| **构建工具** | Vite | ≥5.3 | HMR + 代理配置 |
| **2D/3D 可视化** | Plotly | ≥5.22 | Contour 等值线 + Volume 体渲染 |
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
├── requirements.txt            # Python 依赖
├── pyproject.toml              # 项目元数据 + Pytest/Ruff 配置
├── .env                        # 环境变量 (敏感信息, gitignore)
├── .env.example                # 环境变量模板
├── .gitignore                  # Git 忽略规则
├── .editorconfig               # 编辑器统一配置
├── Makefile                    # 常用命令快捷方式
├── README.md                   # 本文件
│
├── scripts/                    # 管理脚本
│   ├── init_db.py              #   数据库初始化 (建表 + Milvus 集合)
│   └── seed_admin.py           #   创建默认管理员账号
│
├── docs/                       # 项目文档
│   └── core_requirements.md    #   核心需求说明
│
├── deploy/                     # 部署相关
│   ├── Dockerfile              #   Docker 镜像构建
│   ├── docker-compose.yml      #   容器编排
│   └── nginx.conf              #   Nginx 反向代理配置
│
├── tests/                      # 测试套件
│   └── test_full.py            #   55 项综合 API 测试 (16 个测试组)
│
├── app/                        # Python 应用包
│   ├── config/                 # 配置层
│   │   ├── settings.py         #   环境变量 → pydantic BaseSettings
│   │   ├── database.py         #   异步引擎 + get_db() 依赖注入
│   │   ├── response.py         #   统一响应 ApiResponse + BusinessException
│   │   └── logging.py          #   彩色日志 + TimedRotatingFileHandler
│   │
│   ├── models/                 # ORM 模型
│   │   ├── __init__.py         #   自动扫描 + init_tables()
│   │   ├── user.py             #   用户表
│   │   ├── task.py             #   任务表 (含 report_phase 生命周期字段)
│   │   ├── raw_data.py         #   原始水质数据表
│   │   └── anomaly.py          #   异常记录表
│   │
│   ├── schemas/                # Pydantic 数据校验
│   │   ├── upload.py           #   上传请求/响应
│   │   ├── task.py             #   任务状态/列表/可视化
│   │   ├── anomaly.py          #   异常点查询
│   │   └── report.py           #   报告生成
│   │
│   ├── routers/                # API 路由层
│   │   ├── auth.py             #   POST /api/auth/login|register|logout, GET /api/auth/me
│   │   ├── upload.py           #   POST /api/upload
│   │   ├── task.py             #   GET /api/task/{id}/* (visualization, statistics, raw_data 等)
│   │   ├── anomaly.py          #   GET /api/anomalies, GET /api/task/{id}/anomalies
│   │   ├── report.py           #   POST /api/task/{id}/similar|generate_report, GET /api/reports
│   │   └── dashboard.py        #   GET /api/dashboard/stats
│   │
│   ├── services/               # 业务逻辑层
│   │   ├── data_service.py     #   CSV 解析、编码检测、字段映射
│   │   ├── interpolation.py    #   IDW/Kriging 空间插值 (50×50 网格)
│   │   ├── anomaly_detector.py #   统计阈值 + Isolation Forest 双重检测
│   │   ├── feature_extractor.py#   13 维统计特征向量提取
│   │   ├── milvus_service.py   #   Milvus 连接/集合管理/插入/检索 (四层防御)
│   │   ├── visualization.py    #   Plotly 2D 等值线 + 3D 体渲染
│   │   ├── report_generator.py #   LLM 分析 → 图表 → DOCX → LibreOffice PDF
│   │   └── celery_tasks.py     #   Celery 异步任务 (process_csv 完整流水线)
│   │
│   ├── middlewares/            # 中间件
│   │   └── auth.py             #   JWT 认证 + get_current_user / require_admin
│   │
│   ├── handlers/               # 异常处理器
│   │   └── error_handlers.py   #   BusinessException / HTTPException / 全局兜底
│   │
│   └── utils/                  # 工具层
│       └── jwt_util.py         #   JWT 生成/验证 + 密码哈希
│
├── frontend/                   # Vue 3 前端源码
│   ├── src/
│   │   ├── views/              #   11 个页面视图
│   │   ├── components/         #   FileDrop, ContourPanel, PointCloudFrame
│   │   ├── composables/        #   useTask 组合式函数
│   │   ├── router/             #   Vue Router 配置
│   │   ├── api/                #   按模块拆分: client/auth/task/report/anomaly/dashboard
│   │   ├── stores/             #   Pinia 状态管理
│   │   └── App.vue             #   根组件
│   ├── vite.config.js          #   构建配置 (outDir: ../static)
│   └── package.json            #   NPM 依赖
│
├── static/                     # 前端构建产物 (Vite 输出, FastAPI StaticFiles 服务)
│
├── data/                       # 运行时数据
│   ├── uploads/                #   上传的 CSV 文件
│   ├── reports/                #   生成的 DOCX/PDF 报告
│   └── 3d/                     #   生成的 3D 体渲染 HTML
│
└── logs/                       # 日志文件
    ├── app.log                 #   全量日志 (按日滚动, 保留 30 天)
    └── app_error.log           #   错误日志
```

---

## 快速开始

### 环境要求

| 组件 | 最低版本 | 说明 |
|------|---------|------|
| Python | 3.11+ | 异步语法支持 |
| MySQL | 8.0 | 业务数据库 |
| Redis | 7.0+ | Celery 消息队列 |
| Milvus | 2.4+ | 向量检索 (可选, 不可用时降级) |
| Node.js | 18+ | 前端构建 (可选) |
| LibreOffice | — | PDF 转换 (可选, 不可用时仅输出 DOCX) |

### 本地开发

```bash
# 1. 克隆项目
git clone <repo-url> water_analysis
cd water_analysis

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填写 DEEPSEEK_API_KEY、DATABASE_URL 等

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库 (需先启动 MySQL 和 Milvus)
python scripts/init_db.py

# 5. 创建默认管理员 (可选，启用认证时需要)
python scripts/seed_admin.py

# 6. 启动 Celery Worker (新终端)
celery -A app.services.celery_tasks worker --loglevel=info --concurrency=4

# 7. 启动 FastAPI 服务 (新终端)
python main.py
# 访问 http://localhost:8000/api/health 验证

# 8. 启动前端开发服务器 (可选, 新终端)
cd frontend
npm install
npm run dev
# 访问 http://localhost:3000
```

### Docker 部署

```bash
# 一键启动全部服务
docker-compose -f deploy/docker-compose.yml up -d

# 初始化
docker-compose -f deploy/docker-compose.yml exec fastapi python scripts/init_db.py
docker-compose -f deploy/docker-compose.yml exec fastapi python scripts/seed_admin.py
```

---

## 配置说明

全部配置通过 `.env` 文件管理，`app/config/settings.py` 使用 `pydantic_settings.BaseSettings` 自动加载。

### 必填配置

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | `sk-xxx` |
| `DATABASE_URL` | MySQL 连接串 | `mysql+aiomysql://root:pass@localhost:3306/water_quality` |

### 可选配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_PROVIDER` | LLM 提供商 (`deepseek` / `openai`) | `deepseek` |
| `DEEPSEEK_MODEL` | DeepSeek 模型名称 | `deepseek-v4-pro` |
| `REDIS_URL` | Redis 连接 | `redis://localhost:6379/0` |
| `MILVUS_HOST` | Milvus 地址 | `localhost` |
| `MILVUS_PORT` | Milvus 端口 | `19530` |
| `USER_AUTHORIZATION` | 是否开启登录验证 | `False` |
| `JWT_SECRET` | JWT 签名密钥 | `change-me-in-production` |
| `JWT_EXPIRE_HOURS` | Token 过期时间 (小时) | `2` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `GRID_RESOLUTION` | 插值网格分辨率 | `50` |
| `INTERPOLATION_METHOD` | 插值方法 (`idw` / `kriging`) | `idw` |
| `CONTAMINATION` | Isolation Forest 污染率 | `0.05` |

### 空间范围

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

## 用户认证

系统支持基于 JWT 的登录验证，通过 `USER_AUTHORIZATION` 开关控制。

### 启用认证

```env
USER_AUTHORIZATION=True
```

### 默认管理员

| 项目 | 值 |
|------|-----|
| 用户名 | `admin` |
| 密码 | `admin123` |
| 角色 | 管理员 |

```bash
python scripts/seed_admin.py
```

### 白名单路由 (无需登录)

`/api/health`、`/api/auth/login`、`/api/auth/register`、`/docs`、`/static/*`、`/reports/*`

---

## API 文档

服务启动后访问 `http://localhost:8000/docs` 查看 Swagger 文档。

### 接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/auth/register` | 用户注册 |
| `POST` | `/api/auth/login` | 登录，返回 JWT |
| `GET` | `/api/auth/me` | 获取当前用户信息 |
| `GET` | `/api/dashboard/stats` | 仪表盘统计数据 |
| `POST` | `/api/upload` | 上传 CSV，返回 task_id |
| `GET` | `/api/tasks?page=1&page_size=20` | 分页任务列表 (支持搜索/筛选/排序) |
| `PUT` | `/api/task/{id}` | 更新任务信息 (如水库名称) |
| `DELETE` | `/api/task/{id}` | 删除任务及关联数据 |
| `GET` | `/api/task/{id}/status` | 任务状态与进度 |
| `GET` | `/api/task/{id}/statistics` | 各指标统计 (均值/标准差/异常率) |
| `GET` | `/api/task/{id}/visualization?indicator=ch&depth=1` | 等值线 HTML URL + 体渲染 URL + 网格 |
| `GET` | `/api/task/{id}/contour_html?indicator=ch&depth=1` | 等值线图独立 HTML (iframe 加载) |
| `GET` | `/api/task/{id}/depth_profile?indicator=ch` | 深度剖面数据 |
| `GET` | `/api/task/{id}/depth_profile_html?indicator=ch` | 深度剖面图独立 HTML |
| `GET` | `/api/task/{id}/distribution?indicator=ch&bins=20` | 指标分布直方图数据 |
| `GET` | `/api/task/{id}/raw_data?page=1&page_size=50` | 分页原始数据预览 |
| `GET` | `/api/anomalies?task_id=&indicator=ph&page=1` | 跨任务异常点列表 (多条件筛选) |
| `GET` | `/api/task/{id}/anomalies?page=1&page_size=50` | 单任务异常点列表 |
| `GET` | `/api/task/{id}/anomalies/export` | 导出异常点 CSV |
| `GET` | `/api/reports?page=1&page_size=20` | 跨任务报告列表 |
| `GET` | `/api/task/{id}/report_status` | 报告生成状态 (DB 管控生命周期) |
| `POST` | `/api/task/{id}/similar` | Milvus 检索 Top-5 相似案例 |
| `POST` | `/api/task/{id}/generate_report` | 生成 LLM 分析报告 (DOCX/PDF) |
| `DELETE` | `/api/report/{id}` | 删除报告文件 |

### 统一响应格式

```json
{
  "status": 1,
  "messages": "操作成功",
  "datas": {}
}
```

`status=1` 成功, `status=0` 失败。

### 任务状态机

```
pending → processing → success
              │
              └→ failed
```

---

## 数据库设计

### MySQL 表结构

**users** — 用户表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增主键 |
| username | VARCHAR(50) UNIQUE | 用户名 |
| password_hash | VARCHAR(255) | bcrypt 哈希 |
| role | ENUM('admin','user') | 角色 |
| created_at | DATETIME | 创建时间 |

**tasks** — 任务表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | CHAR(36) PK | UUID |
| user_id | INT FK → users.id | 提交用户 |
| reservoir_name | VARCHAR(64) | 水库名称 |
| original_filename | VARCHAR(255) | 原始文件名 |
| file_path | VARCHAR(512) | 服务器存储路径 |
| total_points | INT | 采样点总数 |
| anomaly_count | INT | 异常点数量 |
| status | ENUM('pending','processing','success','failed') | 任务状态 |
| progress | INT DEFAULT 0 | 0-100 |
| created_at | DATETIME | 创建时间 |
| finished_at | DATETIME | 完成时间 |
| report_path | VARCHAR(512) | 报告文件路径 |
| report_phase | VARCHAR(64) | 报告生成阶段 (null=空闲, 非空=生成中) |

**raw_data** — 原始水质数据
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增主键 |
| task_id | CHAR(36) INDEXED | 关联任务 |
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
| id | INT PK | 自增主键 |
| task_id | CHAR(36) INDEXED | 关联任务 |
| lon / lat | FLOAT | 坐标 |
| depth | FLOAT | 深度 |
| indicator | VARCHAR(30) | 指标名 |
| value | FLOAT | 异常值 |
| method | VARCHAR(30) | 检测方法 (threshold / isolation_forest) |
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

13 维特征向量：5 指标均值 + 5 指标标准差 + 异常比例 + 经度方差 + 纬度方差

---

## 核心模块

### 数据接入 (`data_service.py`)

- 多编码自动检测：UTF-8 → GBK → GB2312 → ISO-8859-1 → latin1
- 字段名智能映射：`FIELD_ALIASES` 字典覆盖乱码/中英文表头
- 数据校验：经纬度范围、深度范围、指标范围检查

### 空间插值 (`interpolation.py`)

- **IDW**：反距离加权插值 (power=2)，纯 numpy 实现
- **Kriging**：PyKrige OrdinaryKriging (球形变异函数)，降级到 scipy griddata
- **网格**：50×50 分辨率，采样边界外扩 5%
- **分深度层**：独立插值，保持不同深度的空间结构

### 异常检测 (`anomaly_detector.py`)

- **统计阈值**：可配置的 min/max 范围，超出即标记
- **Isolation Forest**：contamination=0.05，StandardScaler 预处理
- **合并策略**：OR 逻辑取并集，(lon, lat, depth, indicator) 四元组去重

### 可视化 (`visualization.py`)

- **2D 等值线**：Plotly Contour trace，11 段 blue-white-red 色阶，异常点 X 标注
- **3D 体渲染**：Plotly Volume trace，12 层等值面，半透明渲染，异常点 Scatter3d 叠加
- **回退机制**：深度层不足 2 层时自动降级为 Scatter3d 散点图
- **输出分离**：等值线 HTML 保存到文件，API 返回 URL 而非内联 HTML（响应体从 ~500KB 降至 ~300B）

### 报告生成 (`report_generator.py`)

- DeepSeek LLM 生成结构化分析报告：总体评价 → 异常区域 → 相似案例对比 → 改善建议
- 输出 DOCX (`python-docx`)，可选转换为 PDF (`libreoffice --headless`)
- **纯 DB 生命周期**：`report_phase` 字段管控生成状态，服务器重启可通过库状态检测中断

---

## Milvus 策略

Milvus 接入采用四层防御策略，解决 pymilvus 无超时参数导致线程阻塞的核心问题。

### 1. 启动不加载数据

`init_collection()` 只创建/获取 Collection 对象（毫秒级），不调用 `col.load()`。

`col.load()` 是同步 gRPC 调用，将全部向量加载到 Milvus 内存，放在启动路径会卡死整个服务。该行已从启动路径移除。

### 2. 懒加载

`search()` 首次调用时执行 `col.load()`。正常运行时只加载一次，后续搜索复用。

### 3. 熔断器

- TCP 探活（3s 超时）先于 `connections.connect()` — pymilvus 的 connect 内部 C 层 socket 无超时，必须预先探测
- 连接失败后缓存 5 分钟快速失败，防止请求排队阻塞线程池
- 所有 public 函数入口先检查熔断状态

实现见 `app/services/milvus_service.py:_probe()` 和 `connect()`。

### 4. 独立线程池 + 外层超时

`report.py` 中创建专用 `ThreadPoolExecutor(max_workers=2, thread_name_prefix="milvus_")`，与 FastAPI 默认线程池隔离：

```python
_MILVUS_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="milvus_")

def _call_milvus(func, *args, timeout=6):
    future = _MILVUS_EXECUTOR.submit(func, *args)
    try:
        return future.result(timeout=timeout)
    except FutureTimeoutError:
        future.cancel()
        raise TimeoutError(...)
```

`future.result(timeout=N)` 是 Python 线程唯一可靠的超时手段。`asyncio.wait_for` + `run_in_executor` 取消 Future 但杀不掉阻塞线程，需要此层做真正隔离。

### 失败降级

所有 Milvus 调用失败时不影响核心功能：
- 相似案例检索返回空列表
- 特征向量入库跳过
- 上传→分析→可视化核心链路独立运行

---

## 前端

Vue 3 + Vite + Element Plus，独立于 `frontend/` 目录。

```bash
cd frontend
npm run dev          # http://localhost:3000, 代理 /api → :8000
npm run build        # 输出到 ../static/ (FastAPI StaticFiles 直接服务)
```

### 页面路由

| 路由 | 组件 | 说明 |
|------|------|------|
| `/` | DashboardView | ECharts 统计仪表盘 (30s 自动刷新) |
| `/login` | LoginView | 登录/注册 |
| `/upload` | UploadView | CSV 拖拽上传 |
| `/tasks` | TaskListView | 任务列表 (搜索/筛选/排序, 表格/卡片双视图) |
| `/task/:id` | TaskDetailView | 任务详情 (6 标签页: 信息/统计/等值线/3D/剖面/原始数据) |
| `/task/:id/anomalies` | AnomalyView | 异常点列表 + 地图标记 + CSV 导出 |
| `/task/:id/report` | ReportView | 智能报告生成 + DOCX/PDF 下载 + 相似案例 |
| `/anomalies` | AnomalyView | 跨任务异常检索 |
| `/reports` | ReportManageView | 报告管理 |
| `/compare` | CompareView | 双任务统计对比 |
| `/map` | MapView | 采样点空间分布地图 |
| `/users` | UserManageView | 用户管理 (管理员) |

---

## 测试

```bash
# 快速测试 (跳过报告生成, 约 30 秒)
python tests/test_full.py

# 完整测试 (含报告生成, 需 Milvus 运行, 约 2 分钟)
python tests/test_full.py

# 跳过慢速测试
SKIP_SLOW=1 python tests/test_full.py
```

### 测试覆盖

`tests/test_full.py` — 55 项综合 API 测试，16 个测试组：

| 组 | 内容 |
|----|------|
| 1. Health | 健康检查 |
| 2. Auth | 注册、登录、获取当前用户 |
| 3. Dashboard | 统计面板数据完整性 |
| 4. Task List | 分页、筛选、排序 |
| 5. Task Status | 任务状态与进度 |
| 6. Task Update | 更新水库名称并验证持久化 |
| 7. Statistics | 各指标异常数合计校验 |
| 8. Visualization | 返回 URL 而非内联 HTML，grid/depths 完整性 |
| 9. Depth Profile | 深度剖面数据层数 |
| 10. Distribution | 三指标直方图 bins/counts |
| 11. Raw Data | 分页、字段、列标签 |
| 12. Anomalies | 列表、筛选、多条件组合 |
| 13. Reports | 报告列表、状态、相似案例 |
| 14. HTML Endpoints | 独立等值线/剖面 HTML |
| 15. Report Generation | 端到端生成 + 轮询 (SKIP_SLOW=1 跳过) |
| 16. Error Handling | 404/401/422/400 |

---

## 部署运维

### 日志

- 控制台：ANSI 彩色输出
- 文件：`logs/app.log` (全量) + `logs/app_error.log` (ERROR+)
- 按日滚动，保留 30 天
- 通过 `LOG_LEVEL` 全局控制级别

### 健康检查

```bash
curl http://localhost:8000/api/health
# {"status":"ok","app":"水质三维智能监测与分析系统"}
```

### 性能建议

- **大文件**：CSV > 10 万行建议拆分上传
- **并发**：Celery `--concurrency=4` 可根据 CPU 核数调整
- **数据库连接池**：`pool_size=20, max_overflow=10`
- **Milvus nlist**：数据量 < 10 万时 `nlist=128` 即可

### 常见问题

**Q: Milvus 未部署能否运行？**
A: 可以。Milvus 初始化失败时仅输出 Warning，核心链路（上传→分析→可视化）不受影响。相似案例检索和特征入库会跳过。

**Q: LibreOffice 未安装能否生成报告？**
A: 可以。系统生成 `.docx` 并直接返回，PDF 转换步骤静默跳过。

**Q: CSV 编码乱码？**
A: `data_service.py` 内置多编码自动检测（GBK/GB2312/UTF-8 等），`FIELD_ALIASES` 映射表覆盖常见乱码表头。

**Q: 如何切换插值方法？**
A: 在 `.env` 中设置 `INTERPOLATION_METHOD=kriging`。

**Q: 报告生成状态卡在 "生成中"？**
A: 服务器重启后，`report_status` 端点会自动检测到 `report_phase` 非空但 `progress=0` 且无报告文件，将状态重置为可重新生成，不会永久卡死。
