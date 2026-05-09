# 水质三维智能监测与分析系统 - 技术需求文档

## 文档版本

- **版本**：v2.1
- **日期**：2025-05-07
- **状态**：待开发

------

## 1. 项目概述

### 1.1 背景

“巡深”水下机器人可巡航河、湖、近海等水域，采集高时空分辨率的多深度水质数据（温度、盐度、pH、浊度、叶绿素 a、溶解氧等），每个采样点包含多个水深层的指标。本项目旨在开发一套**全流程水质数据分析与智能决策系统**，将原始 CSV 数据转化为直观的三维可视化、异常检测报告及知识库检索，服务于水务部门、环保监测站及科研机构。

### 1.2 核心价值

- **自动化**：从数据上传到报告生成，无需人工干预。
- **三维认知**：通过 3D 点云/体渲染，直观理解水质参数在水体中的立体分布。
- **智能诊断**：融合统计阈值与无监督学习，自动识别异常区域并给出可能原因。
- **知识复用**：基于向量检索，快速定位历史相似事件，辅助决策。

### 1.3 用户角色





| 角色                 | 职责                             |
| -------------------- | -------------------------------- |
| 系统管理员           | 用户管理、系统配置、日志审计     |
| 数据分析师           | 上传数据、查看分析结果、导出报告 |
| 普通访客（演示模式） | 浏览样例数据，体验功能           |

------

## 2. 功能需求

### 2.1 数据管理模块

#### 2.1.1 数据上传

- **支持格式**：CSV（UTF-8 编码）。
- **必填字段**：`lon`, `lat`, `depth_m`，以及至少一个水质指标（如 `chl(ug/L)`）。
- **可选字段**：`temp °C`, `cond (µS/cm)`, `salt ‰`, `pH`, `turb NTU`, `odo(mg/L)`。
- **上传方式**：Web 界面拖拽/点击上传，支持多文件批量上传。每个文件作为一个独立任务处理。
- **数据校验**：
  - 经纬度范围：经度 73~135，纬度 3~54（中国范围可配置）。
  - 深度范围：0~50 米，可配置。
  - 水质指标范围：叶绿素 0~100 µg/L，溶解氧 0~20 mg/L 等，超出则标记为“疑似异常”但不拒绝上传。

#### 2.1.2 数据存储

- **原始数据**：存入 MySQL 表 `raw_data`，关联任务 ID。
- **插值结果**：每个深度层的插值网格（JSON 或 GeoTIFF）存入对象存储（本地文件系统或 MinIO）。
- **特征向量**：计算后的统计特征向量存入 Milvus，关联任务 ID 及元数据。

### 2.2 空间插值模块

#### 2.2.1 插值方法

- 默认使用 **IDW**（反距离加权）或 **克里金**（用户可选）。
- 网格分辨率：**50×50**（可配置为 100×100）。
- 对每个深度层独立插值。

#### 2.2.2 插值边界处理

- 插值范围取所有采样点经纬度外扩 5% 的矩形。
- 边缘无数据区域用空白或设定背景值（默认 0）填充。

#### 2.2.3 输出

- 生成每个深度层的插值网格（JSON 格式：`{ "x": [], "y": [], "z": [[]] }`）。
- 保留每个深度层的插值信息，用于前端绘图。

### 2.3 可视化模块

#### 2.3.1 2D 等值线图（Plotly）

- 功能：
  - 下拉选择深度层（自动从数据中提取所有出现的 `depth_m` 值）。
  - 下拉选择水质指标（叶绿素、溶解氧、水温等）。
  - 色标、缩放、悬停显示数值。
  - 叠加异常点（红色标记）。
- 实现方式：后端生成封闭 HTML 片段，前端嵌入显示。

#### 2.3.2 3D 点云图

- 数据来源：所有采样点（所有深度）。
- 效果：
  - 每个点用小球表示，颜色映射水质指标（例如叶绿素高为红色，低为绿色）。
  - Y 轴表示经度，X 轴表示纬度，Z 轴表示水深（倒置，水面在上：深度越大 Z 值越小）。
  - 支持鼠标旋转/缩放/平移。
  - 可选：添加热力图叠加层。
- 性能要求：支持 10,000 个点同时渲染，帧率≥30fps。
- 实现方式：后端使用 `pydeck` 库生成独立的 3D 点云 HTML 文件，前端通过 `iframe` 或直接嵌入该文件展示。

#### 2.3.3 异常高亮

- 在 2D 等值线图上用**散点标记**标出异常点。
- 在 3D 点云图中，异常点用**不同颜色**（如红色）且加**外发光**效果。

### 2.4 异常检测模块

#### 2.4.1 统计阈值检测

- 管理员可配置各指标的正常范围（默认值：叶绿素 0-20，溶解氧 4-12，pH 6.5-8.5，浊度 0-10，水温 0-35）。
- 任一指标超出范围即标记为“超标异常”。

#### 2.4.2 无监督异常检测（孤立森林）

- 特征输入：所有水质指标（归一化后）。
- 模型参数：`contamination` 可配置（默认 0.05），表示预期异常比例。
- 输出：每个采样点的异常得分（-1 异常，1 正常）。
- 结果与阈值检测合并：只要任意一种方法判定异常，即最终标记为异常。

#### 2.4.3 异常详情展示

- 表格列出所有异常点：坐标、深度、异常指标及数值、异常类型（阈值/孤立森林）。
- 支持分页、导出 CSV。

### 2.5 智能检索与报告

#### 2.5.1 特征向量提取（Milvus 入库）

- **特征维度**（共 13 维）：
  1. 各指标的平均值（叶绿素、溶解氧、水温、pH、浊度）——5 维
  2. 各指标的标准差——5 维
  3. 异常点数量（占总数比例）——1 维
  4. 空间离散度（经纬度方差）——2 维（经度方差+纬度方差）
- **归一化**：Min-Max 归一化，使各维度值域 [0,1]。
- **元数据存储**：任务 ID、巡航时间、水库名称、数据路径。

#### 2.5.2 相似事件检索

- 用户可点击“检索相似案例”。
- 系统计算当前任务的 13 维向量，在 Milvus 中检索 **Top-5 最相似**的历史任务（欧氏距离）。
- 返回结果包括：相似度得分、任务名、巡航时间、异常数量、报告链接。

#### 2.5.3 智能报告生成（LLM）

- **触发**：用户点击“生成报告”。
- **输入内容**：
  - 巡航基础信息（时间、点位数量、深度范围）
  - 各指标统计摘要（均值、标准差、异常比例）
  - 异常点列表（最多 20 条）
  - 相似案例简述（由检索结果提供）
- **生成方式**：调用大模型 API（OpenAI gpt-3.5-turbo 或 DeepSeek）基于结构化 Prompt 生成中文报告。
- **输出格式**：Word（.docx）和 PDF（.pdf），内嵌等值线图静态图片（使用 `plotly.io.to_image` 或 `kaleido` 导出）。
- **报告章节**：
  1. 概述
  2. 水质总体评价
  3. 异常区域分析
  4. 历史相似案例对照
  5. 建议措施

### 2.6 用户与权限管理（可选）

- 提供简单的 JWT 登录。
- 管理员可创建/禁用用户。
- 普通用户只能访问自己上传的任务，管理员可访问所有任务。

------

## 3. 技术架构

### 3.1 整体架构图

text

```
[前端 Vue3] → [FastAPI 后端] → [MySQL] (任务/用户)
       ↓              ↓
   [Nginx]        [Milvus] (特征向量)
       ↓              ↓
  静态HTML        [本地存储] (CSV, 插值网格, 报告)
```

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _33882ae"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _28d7e84"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

### 3.2 技术栈详情





| 类别       | 技术                                 | 版本/说明                          |
| ---------- | ------------------------------------ | ---------------------------------- |
| 前端框架   | Vue3 + Vite                          | 组合式 API，Element Plus 组件库    |
| 3D 可视化  | [Deck.gl](https://deck.gl/) (pydeck) | 后端生成静态 HTML，前端嵌入        |
| 2D 可视化  | Plotly.js                            | 动态渲染等值线图                   |
| 后端框架   | FastAPI                              | Python 3.10+，异步 API             |
| 异步任务   | Celery + Redis                       | 处理耗时任务（插值、异常检测）     |
| 数据库     | MySQL 8.0                            | 存储任务信息、用户、原始数据元数据 |
| 向量数据库 | Milvus 2.3+                          | 独立部署或 Docker                  |
| 对象存储   | MinIO 或本地文件系统                 | 存储上传的 CSV、插值结果、报告     |
| 插值与算法 | Scipy, Scikit-learn, PyKrige         | 空间插值、孤立森林                 |
| 大模型     | OpenAI API / DeepSeek API            | 报告生成（可配置）                 |
| 部署       | Docker Compose                       | 一键启动所有服务                   |

------

## 4. 接口设计（API）

所有接口返回 JSON 格式，成功标志 `"code": 0`。错误响应格式统一为：

json

```
{
  "code": 40001,
  "message": "错误描述",
  "detail": "详细信息（可选）"
}
```

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _33882ae"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _28d7e84"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

### 4.1 数据上传

text

```
POST /api/upload
Content-Type: multipart/form-data
Parameters:
  - file: CSV 文件
  - reservoir_name: 水库名称（可选）
Response:
{
  "code": 0,
  "task_id": "uuid",
  "message": "upload success"
}
```

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _33882ae"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _28d7e84"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

### 4.2 获取分析状态

text

```
GET /api/task/{task_id}/status
Response:
{
  "code": 0,
  "status": "pending|processing|success|failed",
  "progress": 70   # 百分比
}
```

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _33882ae"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _28d7e84"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

### 4.3 获取可视化数据

text

```
GET /api/task/{task_id}/visualization
Parameters:
  - indicator: chl|odo|temp|ph|turb
  - depth: 数值（从数据中提取的实际深度值）
Response:
{
  "code": 0,
  "contour_html": "<div>...</div>",   # Plotly 生成的 HTML 片段
  "grid": { "x": [], "y": [], "z": [[]] },  # 原始网格（备用）
  "scatter_3d_url": "/static/3d/task_id.html"   # pydeck 生成的静态文件 URL
}
```

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _33882ae"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _28d7e84"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

### 4.4 获取异常点列表

text

```
GET /api/task/{task_id}/anomalies
Parameters:
  - page: 1 (默认)
  - page_size: 20 (默认)
Response:
{
  "code": 0,
  "total": 45,
  "data": [
    {"lon": xx, "lat": xx, "depth": 2, "indicator": "chl", "value": 25.3, "method": "threshold"}
  ]
}
```

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _33882ae"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _28d7e84"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

### 4.5 相似检索

text

```
POST /api/task/{task_id}/similar
Response:
{
  "code": 0,
  "similar_tasks": [
    {"task_id": "xxx", "similarity": 0.92, "reservoir": "xx水库", "date": "2025-04-01", "report_url": "/reports/xxx.pdf"}
  ]
}
```

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _33882ae"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _28d7e84"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

### 4.6 生成报告

text

```
POST /api/task/{task_id}/generate_report
Response:
{
  "code": 0,
  "report_url": "/reports/xxx.pdf"
}
```

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _33882ae"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _28d7e84"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

------

## 5. 数据库设计

### 5.1 MySQL 表结构

#### `users`





| 字段          | 类型                 | 说明   |
| ------------- | -------------------- | ------ |
| id            | INT PK               | 自增   |
| username      | VARCHAR(32)          | 唯一   |
| password_hash | VARCHAR(128)         | bcrypt |
| role          | ENUM('admin','user') | 权限   |
| created_at    | DATETIME             |        |

#### `tasks`





| 字段              | 类型                                            | 说明       |
| ----------------- | ----------------------------------------------- | ---------- |
| id                | CHAR(36) PK                                     | UUID       |
| user_id           | INT FK                                          | 上传者     |
| reservoir_name    | VARCHAR(64)                                     | 水库名称   |
| original_filename | VARCHAR(255)                                    | 原始文件名 |
| file_path         | VARCHAR(512)                                    | 存储路径   |
| total_points      | INT                                             | 总采样点数 |
| anomaly_count     | INT                                             | 异常点数量 |
| status            | ENUM('pending','processing','success','failed') |            |
| created_at        | DATETIME                                        |            |
| finished_at       | DATETIME                                        | NULL       |
| report_path       | VARCHAR(512)                                    | NULL       |

### 5.2 Milvus 集合设计

- **集合名称**：`task_features`
- **字段**：
  - `task_id` (VARCHAR, 主键)
  - `feature_vector` (FLOAT_VECTOR, 维度 13)
  - `created_at` (INT64, 时间戳，Unix 秒)
  - `reservoir_name` (VARCHAR, 辅助过滤)
- **索引**：IVF_FLAT, 距离度量 L2。

------

## 6. 关键实现细节

### 6.1 插值与网格生成

- 使用 `scipy.interpolate.griddata`，方法默认 `'cubic'`，若点太少则降级为 `'linear'`。
- 网格生成边界：`min(lon)-0.005` 到 `max(lon)+0.005`，步长取 (范围/50)。
- 每个深度层独立插值，保存为 NumPy `.npy` 或 JSON。

### 6.2 3D 点云性能优化

- 后端使用 `pydeck` 生成静态 HTML，默认启用点云抽稀：超过 5000 点时，每 2 个点保留 1 个（随机采样）。
- 颜色映射：根据所选指标线性插值颜色（如叶绿素低=绿，高=红）。
- 前端通过 `iframe` 嵌入，避免主线程阻塞。

### 6.3 异常检测流程

1. 读取原始数据，过滤缺失值。
2. 统计阈值检测：生成 `anomaly_threshold` 列。
3. 孤立森林：选取 `['chl(ug/L)','odo(mg/L)','temp °C','pH','turb NTU']`，标准化后训练（`contamination` 使用用户配置值，默认 0.05）。
4. 合并结果：最终 `anomaly_flag = anomaly_threshold OR (predict == -1)`。
5. 异常点数量及详细信息存入 MySQL。

### 6.4 Milvus 入库时机

- 在任务处理完成（插值、异常检测结束）后。
- 提取 13 维特征，归一化后插入 Milvus。
- 删除任务时同步删除 Milvus 中对应向量。

### 6.5 大模型报告生成提示词模板

text

```
你是一名资深水质分析专家。请根据以下数据生成一份专业的水质巡航分析报告。

巡航基础信息：
水库：{reservoir_name}
时间：{date}
采样点数：{point_count}，深度层：{depth_layers}

水质指标统计：
【叶绿素】均值 {chl_mean}，标准差 {chl_std}，异常比例 {chl_anomaly_rate}
【溶解氧】均值 {odo_mean}，标准差 {odo_std}，异常比例 {odo_anomaly_rate}
...（其他指标）

异常点位（示例）：
{anomaly_sample_list}

历史相似案例：
{cases_summary}

请按以下大纲撰写：
1. 总体水质评价
2. 主要异常区域及可能原因
3. 与历史相似案例对比分析
4. 改善建议
```

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _33882ae"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12" fill="none" class="_9bc997d _28d7e84"><path d="M-5.24537e-07 0C-2.34843e-07 6.62742 5.37258 12 12 12L0 12L-5.24537e-07 0Z" fill="currentColor"></path></svg>

------

## 7. 非功能需求





| 类别   | 要求                                         |
| ------ | -------------------------------------------- |
| 性能   | 插值与异常检测总时间 ≤ 2 分钟（1000 点以内） |
| 可扩展 | 支持增加新的水质指标，无需修改核心代码       |
| 安全性 | 上传文件类型限制；防止路径遍历；MySQL 防注入 |
| 可用性 | 所有错误有中文提示，操作可回退               |
| 兼容性 | 前端 Chrome/Firefox/Edge 最新版              |

------

## 8. 交付物清单

1. **完整源代码**：
   - 后端 FastAPI 项目（含 Dockerfile）
   - 前端 Vue3 项目
   - 数据库初始化脚本（MySQL + Milvus）
2. **部署文档**：Docker Compose 一键启动说明，环境变量配置。
3. **API 文档**：Swagger 自动生成（FastAPI 自带）。
4. **演示视频**（≤5 分钟）：上传数据、查看 2D/3D 图、异常检测、检索相似案例、生成报告。
5. **示例数据集**：至少 3 个巡航的 CSV（脱敏），覆盖不同季节/异常状况。
6. **项目技术报告**（PDF）：需求分析、架构设计、算法说明、测试报告。

------

## 9. 风险与应对





| 风险               | 概率 | 影响 | 应对措施                                              |
| ------------------ | ---- | ---- | ----------------------------------------------------- |
| 插值结果边缘误差大 | 中   | 中   | 提供边缘裁剪选项，或允许用户手动设置插值范围          |
| 3D 渲染浏览器卡顿  | 中   | 高   | 实现点云抽稀，并提供低/中/高三档质量开关              |
| Milvus 检索不准确  | 低   | 中   | 特征工程可迭代，先用 PCA 降维，后期可转为深度度量学习 |
| 大模型 API 费用高  | 中   | 低   | 支持本地模型（如 Qwen-7B）或限流 + 缓存报告           |
| 多用户并发性能     | 低   | 中   | 使用 Celery 异步任务队列，避免阻塞                    |

------

## 10. 实施计划（建议 8 周）





| 阶段         | 周次 | 任务                                                         |
| ------------ | ---- | ------------------------------------------------------------ |
| 基础搭建     | 1-2  | MySQL + Milvus 环境；FastAPI 项目骨架；文件上传与解析；Celery 异步任务配置 |
| 插值与可视化 | 3-4  | 插值模块（IDW）；2D等值线生成；前端上传页面与 Plotly 集成；报告图片导出（kaleido） |
| 异常检测与3D | 5-6  | 异常检测（阈值+孤立森林）；3D点云（pydeck）；前端3D视图嵌入  |
| 检索与报告   | 7    | 特征提取+Milvus检索；LLM报告生成；报告下载功能               |
| 完善与交付   | 8    | 集成测试，性能调优，文档撰写，演示视频录制                   |

------

## 附录 A：示例 CSV 字段映射





| CSV 原始字段 | 内部字段名       | 单位   |
| ------------ | ---------------- | ------ |
| lon          | longitude        | 度     |
| lat          | latitude         | 度     |
| depth_m      | depth            | 米     |
| temp °C      | temperature      | 摄氏度 |
| cond (µS/cm) | conductivity     | µS/cm  |
| salt ‰       | salinity         | ppt    |
| pH           | ph               | 无量纲 |
| turb NTU     | turbidity        | NTU    |
| chl(ug/L)    | chlorophyll      | µg/L   |
| odo(mg/L)    | dissolved_oxygen | mg/L   |

------

## 附录 B：Milvus 集合 Schema（示例）

json

```
{
  "collection_name": "task_features",
  "fields": [
    {"name": "task_id", "type": "VarChar", "max_length": 36, "is_primary": true},
    {"name": "feature_vector", "type": "FloatVector", "dim": 13},
    {"name": "created_at", "type": "Int64"},
    {"name": "reservoir_name", "type": "VarChar", "max_length": 64}
  ]
}
```