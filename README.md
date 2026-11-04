# Olist 电商商业数据分析与可视化

基于巴西 Olist 电商平台公开数据集，完成从数据加载、清洗治理、商业建模到可视化复现的全流程分析项目。采用纯 Python 实现（pandas + matplotlib/seaborn + statsmodels + streamlit），复现《Excel 数据可视化——从图表到数据大屏》教材中 10 种图表模板，并构建 6 张核心业务模型图与交互式大屏。

## 项目结构

```
olist-commercial-data-analysis/
├── run_all.py                    # 一键复现全流程入口
├── requirements.txt              # 依赖列表
├── scripts/                       # 五段式分析流水线
│   ├── 01_load.py                 # 数据加载
│   ├── 02_clean.py                # 数据清洗与多表关联
│   ├── 03_analysis.py             # 商业模型计算 (RFM/同期群/SARIMA/帕累托/漏斗)
│   ├── 04_visuals.py              # 可视化: 10张模板复现 + 6张业务图
│   └── 05_dashboard.py            # Streamlit 交互式大屏
├── data/
│   ├── raw/                       # 原始数据 (11个CSV)
│   └── clean/                     # 清洗产物 (order_master.csv, reviews_clean.csv, olist_analysis.db)
└── outputs/
    ├── figures/                   # 16张图表 PNG
    └── tables/                    # 7个分析结果 CSV
```

## 数据来源

- **数据集**: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Kaggle)
- **许可证**: CC BY-NC-SA 4.0
- **时间范围**: 2016年9月 – 2018年10月（有效数据集中于 2017–2018 年）
- **规模**: 99,441 笔订单，9 张原始数据表（客户、订单、商品、支付、评价、卖家、地理、类目翻译、营销线索）

> **注意**: 原始数据集 olist_geolocation_dataset.csv (59MB) 等因超出 GitHub 单文件 25MB 限制未上传。本项目已提供清洗后的 data/clean/order_master.csv，可直接用于模型分析。如需原始数据，请从 Kaggle 下载后放入 data/raw/ 目录。

### 原始数据表说明

| 文件 | 说明 |
|------|------|
| `olist_orders_dataset.csv` | 订单主表（状态、时间戳） |
| `olist_order_items_dataset.csv` | 订单商品明细 |
| `olist_order_payments_dataset.csv` | 支付方式与分期 |
| `olist_order_reviews_dataset.csv` | 客户评价与评分 |
| `olist_customers_dataset.csv` | 客户信息 |
| `olist_products_dataset.csv` | 商品与类目 |
| `olist_sellers_dataset.csv` | 卖家信息 |
| `olist_geolocation_dataset.csv` | 地理位置坐标 |
| `product_category_name_translation.csv` | 葡语类目名英译 |
| `olist_marketing_qualified_leads_dataset.csv` | 营销线索 |
| `olist_closed_deals_dataset.csv` | 成交商机 |

## 环境配置与一键复现

### 环境要求

- Python 3.9+
- 依赖安装: `pip install -r requirements.txt`
- 获取原始数据：
  - 本项目使用 Olist 全量数据（99,441条订单），因文件过大未上传至 GitHub。
  - 请从 [Kaggle Olist Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) 下载 ZIP 包。
  - 解压后将所有 `.csv` 文件放入 `data/raw/` 目录。

### 一键复现（推荐）

克隆仓库并将原始 CSV 放入 `data/raw/` 后，只需执行一条命令即可自动完成从数据加载、清洗、商业建模到图表生成的全流程：

```bash
python run_all.py
```

该命令会依次执行 `01_load → 02_clean → 03_analysis → 04_visuals`，每步打印耗时，完成后自动校验产出文件。全流程约 65 秒。

常用参数：

```bash
python run_all.py --check       # 仅检查环境与依赖，不执行
python run_all.py --from 3      # 从第3步开始执行
python run_all.py --only 4      # 仅执行第4步（可视化）
python run_all.py --dashboard   # 全流程完成后启动 Streamlit 大屏
```

### 分步执行（备选）

如需单独调试某一步，可按顺序运行各脚本：

```bash
# 1. 数据加载: 读取 data/raw/ 下原始CSV → 内存DataFrame
python scripts/01_load.py

# 2. 数据清洗: 缺失/异常/重复处理, 多表关联 → data/clean/
python scripts/02_clean.py

# 3. 商业建模: RFM/同期群/SARIMA/帕累托/漏斗 → outputs/tables/
python scripts/03_analysis.py

# 4. 可视化: 10张模板复现 + 6张业务图 → outputs/figures/
python scripts/04_visuals.py

# 5. 交互大屏 (可选)
streamlit run scripts/05_dashboard.py
```

## 图表索引

### 模板复现图 (fig01–fig10)

对照《Excel 数据可视化——从图表到数据大屏》教材模板，从 Excel 内嵌 `chart*.xml` 提取真实配色与样式后逐项还原。统一深蓝背景 `#1A1E43`，白色文字，标题左对齐。

| 编号 | 文件名 | 对应模板 | 图表类型 | 关键样式 |
|------|--------|----------|----------|----------|
| fig01 | `fig01_模板1_渐变柱形图.png` | 模板1 | 渐变柱形图 | 柱内垂直渐变 `#0070C0→#00B0F0`，柱顶数值标签 |
| fig02 | `fig02_模板2_带均值柱形图.png` | 模板2 | 带均值柱形图 | 蓝柱 + 金黄均值线 |
| fig03 | `fig03_模板3_标注柱形图.png` | 模板4 | 标注柱形图 | 每柱独立配色，对话气泡数值标签 |
| fig04 | `fig04_模板4_层叠柱形图.png` | 模板5 | 层叠柱形图 | 并排双系列部分重叠，柱顶标签 |
| fig05 | `fig05_模板5_蝴蝶图.png` | 模板6 | 蝴蝶图 | 红柱向左/蓝柱向右，中间月份数字 |
| fig06 | `fig06_模板6_平滑折线图.png` | 模板11 | 平滑折线图 | B-spline五阶平滑，最高点标注+垂直虚线，底部年份色块 |
| fig07 | `fig07_模板7_对比折线图.png` | 模板13 | 对比折线图 | 2017玫红+2018蓝双系列，圆形标记，数据标签 |
| fig08 | `fig08_模板8_单值圆环图.png` | 模板14 | 单值圆环图 | 紫→玫红渐变圆环，中心百分比，holeSize=90 |
| fig09 | `fig09_模板9_柱形折线图.png` | 模板23 | 柱形折线图 | 蓝柱+玫红折线双轴，折线位于柱子上方 |
| fig10 | `fig10_模板10_对比柱形图.png` | 模板9 | 对比柱形图 | 2017蓝+2018浅蓝双柱，差值箭头标注 |

### 业务模型图 (fig11–fig16)

| 编号 | 文件名 | 图表类型 | 说明 |
|------|--------|----------|------|
| fig11 | `fig11_业务1_RFM气泡散点图.png` | RFM 气泡散点图 | 客户价值分群 (R/F/M 三维) |
| fig12 | `fig12_业务2_同期群留存热力图.png` | 同期群留存热力图 | 按首购月份分组的留存率矩阵 |
| fig13 | `fig13_业务3_SARIMA预测置信区间图.png` | SARIMA 预测图 | 时间序列预测与置信区间 |
| fig14 | `fig14_业务4_巴西点云地图.png` | 地理散点图 | 客户地理分布点云 |
| fig15 | `fig15_业务5_帕累托图.png` | 帕累托图 | 类目销售额 ABC 分类 |
| fig16 | `fig16_业务6_漏斗转化图.png` | 漏斗转化图 | 订单流程各阶段转化率 |

### 分析结果表

| 文件 | 说明 |
|------|------|
| `rfm_results.csv` | RFM 客户分群结果 |
| `cohort_retention.csv` | 同期群留存率 |
| `sarima_forecast.csv` | SARIMA 预测值 |
| `sarima_metrics.csv` | 模型评估指标 (RMSE/MAE/AIC) |
| `pareto_abc.csv` | 帕累托 ABC 分类 |
| `funnel_conversion.csv` | 漏斗各阶段转化率 |
| `geo_city_agg.csv` | 城市级地理聚合统计 |

## 技术栈

| 库 | 用途 |
|----|------|
| pandas | 数据处理与多表关联 |
| numpy | 数值计算 |
| matplotlib / seaborn | 静态图表绘制 |
| plotly | 交互式图表 |
| statsmodels | SARIMA 时间序列预测 |
| scikit-learn | RFM 聚类 |
| streamlit | 交互式数据大屏 |
| wordcloud | 词云可视化 |

## 合规声明

- 数据源自 Kaggle Olist 官方公开数据集 (CC BY-NC-SA 4.0)，通过官网 ZIP 下载获取，不涉及网络爬虫
- 所有分析基于本地清洗后的合规数据，参数设定有明确业务依据
- 可视化全 Python 实现，未使用 BI 软件
