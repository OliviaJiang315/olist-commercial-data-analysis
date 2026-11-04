# Olist 数据字典与模式文档（Schema）

> 本文档描述 Olist 巴西电商数据集的表结构、字段含义、主外键关系与业务语义，供评审与复现者参考。
>
> - **数据来源**：Kaggle Olist 官方公开数据集（CC BY-NC-SA 4.0）
> - **时间范围**：2016-09 ~ 2018-08（有效数据主要集中在 2017-2018）
> - **原始表**：11 张 CSV（`data/raw/`）
> - **清洗后表**：2 张 CSV + 1 个 SQLite（`data/clean/`）

---

## 一、表关系总览（ER 图）

```
                    ┌─────────────────────┐
                    │  customers (99,441) │
                    │  PK: customer_id    │
                    └─────────┬───────────┘
                              │ customer_id
                              ▼
┌──────────────┐   order_id   ┌─────────────────────┐    order_id    ┌──────────────────┐
│ order_items  │─────────────▶│   orders (99,441)   │◀──────────────│ order_payments   │
│  (112,650)   │              │   PK: order_id       │               │   (103,886)      │
└──────┬───────┘              └─────────┬───────────┘               └──────────────────┘
       │ product_id                     │ order_id
       │ seller_id                      ▼
       │                    ┌─────────────────────┐
       │                    │  order_reviews      │
       │                    │  (99,224)           │
       │                    └─────────────────────┘
       ▼
┌──────────────┐              ┌─────────────────────┐
│  products    │──category────▶│ category_translation│
│  (32,951)    │              │  (71)               │
└──────────────┘              └─────────────────────┘

┌──────────────┐  zip_code    ┌─────────────────────┐
│  sellers     │─────────────▶│  geolocation        │
│  (3,095)     │              │  (1,000,163)        │
└──────────────┘              └─────────────────────┘
       ▲                              ▲
       │ seller_id                    │ zip_code
       │                              │
┌──────────────┐  mql_id     ┌─────────────────────┐
│ closed_deals │────────────▶│   mql (8,000)       │
│  (842)       │              │   PK: mql_id        │
└──────────────┘              └─────────────────────┘
```

**核心关联路径**：
`orders.customer_id → customers.customer_id`
`orders.order_id → order_items.order_id → products.product_id / sellers.seller_id`
`orders.order_id → order_payments.order_id`
`orders.order_id → order_reviews.order_id`
`customers.customer_zip_code_prefix → geolocation.geolocation_zip_code_prefix`

---

## 二、原始表字段说明（data/raw/）

### 2.1 olist_orders_dataset.csv（订单主表）

| 字段 | 类型 | 键 | 业务含义 | 示例 |
|------|------|----|----------|------|
| order_id | str(32) | PK | 订单唯一标识 | `e481f51cbdc54678b7cc...` |
| customer_id | str(32) | FK→customers | 该订单对应的客户标识（每单唯一） | `9ef432eb6251297304e7...` |
| order_status | str | — | 订单状态：delivered/shipped/canceled/invoiced/processing/approved/unavailable | `delivered` |
| order_purchase_timestamp | datetime | — | 客户下单时间 | `2017-10-02 10:56:33` |
| order_approved_at | datetime | — | 支付批准时间 | `2017-10-02 11:07:15` |
| order_delivered_carrier_date | datetime | — | 交付物流商时间 | `2017-10-04 19:55:00` |
| order_delivered_customer_date | datetime | — | 实际送达客户时间 | `2017-10-10 21:25:13` |
| order_estimated_delivery_date | datetime | — | 系统预计送达时间 | `2017-10-18 00:00:00` |

- **规模**：99,441 行 × 8 列
- **说明**：`customer_id` 是每单生成的临时标识；要识别同一客户的多次下单需用 `customers.customer_unique_id`。

---

### 2.2 olist_customers_dataset.csv（客户表）

| 字段 | 类型 | 键 | 业务含义 | 示例 |
|------|------|----|----------|------|
| customer_id | str(32) | PK | 订单级客户标识（每单唯一） | `06b8999e2fba1a1fbc88...` |
| customer_unique_id | str(32) | — | 客户真实唯一标识（跨订单） | `861eff4711a542e4b938...` |
| customer_zip_code_prefix | int | FK→geolocation | 客户邮编前缀（5位） | `14409` |
| customer_city | str | — | 客户所在城市（葡语小写） | `sao paulo` |
| customer_state | str(2) | — | 客户所在州缩写 | `SP` |

- **规模**：99,441 行 × 5 列

---

### 2.3 olist_order_items_dataset.csv（订单商品明细表）

| 字段 | 类型 | 键 | 业务含义 | 示例 |
|------|------|----|----------|------|
| order_id | str(32) | FK→orders | 订单ID | `00010242fe8c5a6d1ba2...` |
| order_item_id | int | — | 同一订单内商品序号（从1起） | `1` |
| product_id | str(32) | FK→products | 商品ID | `4244733e06e7ecb4970a...` |
| seller_id | str(32) | FK→sellers | 卖家ID | `48436dade18ac8b2bce0...` |
| shipping_limit_date | datetime | — | 卖家发货截止时间 | `2017-09-19 09:45:35` |
| price | float | — | 商品单价（雷亚尔 R$，不含运费） | `58.90` |
| freight_value | float | — | 单件分摊运费（R$） | `13.29` |

- **规模**：112,650 行 × 7 列
- **复合主键**：`(order_id, order_item_id)`
- **说明**：一个订单可含多件商品，每件可来自不同卖家；`price` 不含运费。

---

### 2.4 olist_order_payments_dataset.csv（订单支付表）

| 字段 | 类型 | 键 | 业务含义 | 示例 |
|------|------|----|----------|------|
| order_id | str(32) | FK→orders | 订单ID | `b81ef226f3fe1789b1e8...` |
| payment_sequential | int | — | 支付顺序号（一笔订单多种支付方式时递增） | `1` |
| payment_type | str | — | 支付方式：credit_card/boleto/voucher/debit_card/not_defined | `credit_card` |
| payment_installments | int | — | 分期期数（1表示一次性） | `8` |
| payment_value | float | — | 该次支付金额（R$） | `99.33` |

- **规模**：103,886 行 × 5 列
- **说明**：`boleto` 是巴西常用银行票据支付方式；订单总支付 = Σ `payment_value`。

---

### 2.5 olist_order_reviews_dataset.csv（订单评价表）

| 字段 | 类型 | 键 | 业务含义 | 示例 |
|------|------|----|----------|------|
| review_id | str(32) | PK | 评价唯一标识 | `7bc2406110b926393aa5...` |
| order_id | str(32) | FK→orders | 被评价的订单ID | `73fc7af87114b39712e6...` |
| review_score | int(1-5) | — | 客户评分（1最差，5最好） | `4` |
| review_comment_title | str | — | 评价标题（可空） | `NaN` |
| review_comment_message | str | — | 评价正文（可空） | `NaN` |
| review_creation_date | datetime | — | 评价提交时间 | `2018-01-18 00:00:00` |
| review_answer_timestamp | datetime | — | 卖家回复时间 | `2018-01-18 21:46:59` |

- **规模**：99,224 行 × 7 列
- **说明**：同一订单可能有多条评价记录，清洗时去重保留最新一条。

---

### 2.6 olist_products_dataset.csv（商品表）

| 字段 | 类型 | 键 | 业务含义 | 示例 |
|------|------|----|----------|------|
| product_id | str(32) | PK | 商品唯一标识 | `1e9e8ef04dbcff4541ed...` |
| product_category_name | str | FK→translation | 商品类目名（葡语） | `perfumaria` |
| product_name_lenght | float | — | 商品名长度（字符数） | `40` |
| product_description_lenght | float | — | 商品描述长度 | `287` |
| product_photos_qty | float | — | 商品照片数量 | `1` |
| product_weight_g | float | — | 商品重量（克） | `225` |
| product_length_cm | float | — | 包装长度（cm） | `16` |
| product_height_cm | float | — | 包装高度（cm） | `10` |
| product_width_cm | float | — | 包装宽度（cm） | `14` |

- **规模**：32,951 行 × 9 列
- **说明**：体积 = length × height × width，用于估算物流成本。

---

### 2.7 olist_sellers_dataset.csv（卖家表）

| 字段 | 类型 | 键 | 业务含义 | 示例 |
|------|------|----|----------|------|
| seller_id | str(32) | PK | 卖家唯一标识 | `3442f8959a84dea7ee19...` |
| seller_zip_code_prefix | int | FK→geolocation | 卖家邮编前缀 | `13023` |
| seller_city | str | — | 卖家所在城市 | `campinas` |
| seller_state | str(2) | — | 卖家所在州缩写 | `SP` |

- **规模**：3,095 行 × 4 列

---

### 2.8 olist_geolocation_dataset.csv（地理位置表）

| 字段 | 类型 | 键 | 业务含义 | 示例 |
|------|------|----|----------|------|
| geolocation_zip_code_prefix | int | PK* | 邮编前缀（同一邮编有多条坐标） | `1037` |
| geolocation_lat | float | — | 纬度 | `-23.545621` |
| geolocation_lng | float | — | 经度 | `-46.639292` |
| geolocation_city | str | — | 城市 | `sao paulo` |
| geolocation_state | str(2) | — | 州缩写 | `SP` |

- **规模**：1,000,163 行 × 5 列
- **说明**：同一邮编前缀对应多个坐标点（邮编区域内多点采样），使用时通常按邮编聚合取均值。

---

### 2.9 product_category_name_translation.csv（类目名翻译表）

| 字段 | 类型 | 键 | 业务含义 | 示例 |
|------|------|----|----------|------|
| product_category_name | str | PK | 葡语类目名 | `beleza_saude` |
| product_category_name_english | str | — | 英文类目名 | `health_beauty` |

- **规模**：71 行 × 2 列

---

### 2.10 olist_marketing_qualified_leads_dataset.csv（营销线索表 MQL）

| 字段 | 类型 | 键 | 业务含义 | 示例 |
|------|------|----|----------|------|
| mql_id | str(32) | PK | 营销线索唯一标识 | `dac32acd4db4c29c2305...` |
| first_contact_date | date | — | 首次接触日期 | `2018-02-01` |
| landing_page_id | str(32) | — | 落地页标识 | `88740e65d5d6b056e0cd...` |
| origin | str | — | 流量来源：social/paid_search/organic_search/email/other/unknown | `social` |

- **规模**：8,000 行 × 4 列

---

### 2.11 olist_closed_deals_dataset.csv（成交线索表）

| 字段 | 类型 | 键 | 业务含义 | 示例 |
|------|------|----|----------|------|
| mql_id | str(32) | FK→mql | 对应的营销线索ID | `5420aad7fec3549a8587...` |
| seller_id | str(32) | FK→sellers | 成交后生成的卖家ID | `2c43fb513632d29b3b58...` |
| sdr_id | str(32) | — | 销售开发代表（SDR）ID | `a8387c01a09e99ce0141...` |
| sr_id | str(32) | — | 销售代表（SR）ID | `4ef15afb4b2723d8f3d8...` |
| won_date | datetime | — | 成交日期 | `2018-02-26 19:58:54` |
| business_segment | str | — | 业务细分（如 pet/car_accessories） | `pet` |
| lead_type | str | — | 线索类型：online_medium/industry/online_big/... | `online_medium` |
| lead_behaviour_profile | str | — | 线索行为画像：cat/eagle/wolf/... | `cat` |
| has_company | str | — | 是否有公司（True/NaN） | `NaN` |
| has_gtin | str | — | 是否有商品条码（GTIN） | `NaN` |
| average_stock | str | — | 平均库存规模声明 | `NaN` |
| business_type | str | — | 业务类型：reseller/manufacturer/... | `reseller` |
| declared_product_catalog_size | float | — | 声明的商品目录规模 | `NaN` |
| declared_monthly_revenue | float | — | 声明的月度收入（R$） | `0.0` |

- **规模**：842 行 × 14 列
- **说明**：MQL → 成交 → 卖家入驻的漏斗数据，用于卖家增长分析。

---

## 三、清洗后表字段说明（data/clean/）

### 3.1 order_master.csv（订单主宽表）

由 `02_clean.py` 将 orders + customers + order_items 聚合 + order_payments 聚合合并生成，作为后续分析与可视化的主数据源。

| 字段 | 类型 | 来源 | 业务含义 | 示例 |
|------|------|------|----------|------|
| order_id | str | orders | 订单ID（PK） | `e481f51cbdc54678b7cc...` |
| customer_id | str | orders | 订单级客户ID | `9ef432eb6251297304e7...` |
| order_status | str | orders | 订单状态 | `delivered` |
| order_purchase_timestamp | datetime | orders | 下单时间 | `2017-10-02 10:56:33` |
| order_approved_at | datetime | orders | 支付批准时间 | `2017-10-02 11:07:15` |
| order_delivered_carrier_date | datetime | orders | 交付物流商时间 | `2017-10-04 19:55:00` |
| order_delivered_customer_date | datetime | orders | 送达客户时间 | `2017-10-10 21:25:13` |
| order_estimated_delivery_date | datetime | orders | 预计送达时间 | `2017-10-18` |
| customer_unique_id | str | customers | 客户真实唯一标识 | `7c396fd4830fd04220f7...` |
| customer_zip_code_prefix | float | customers | 客户邮编前缀 | `3149.0` |
| customer_city | str | customers | 客户城市 | `sao paulo` |
| customer_state | str | customers | 客户州 | `SP` |
| total_price | float | Σ items.price | 订单商品总价（**不含运费**，R$） | `29.99` |
| total_freight | float | Σ items.freight_value | 订单总运费（R$） | `8.72` |
| n_items | float | count(items) | 订单商品件数 | `1.0` |
| payment_value | float | Σ payments | 订单支付总额（**含运费**，R$） | `38.71` |
| installments | float | max(payments) | 最大分期期数 | `3.0` |
| delivery_days | float | 派送日期−下单日期 | 实际送达天数 | `6.0` |
| purchase_month | str | 下单时间截断到月 | 下单月份（用于月度聚合） | `2017-10` |

- **规模**：99,440 行 × 19 列
- **关键派生关系**：`payment_value ≈ total_price + total_freight`（受退款/优惠券影响可能不等）

---

### 3.2 reviews_clean.csv（清洗后评价表）

对 `olist_order_reviews_dataset` 按订单去重后保留最新评价。

| 字段 | 类型 | 业务含义 | 示例 |
|------|------|----------|------|
| review_id | str | 评价ID（PK） | `7bc2406110b926393aa5...` |
| order_id | str | 订单ID（FK→order_master） | `73fc7af87114b39712e6...` |
| review_score | int(1-5) | 评分 | `4` |
| review_comment_title | str | 评价标题 | `NaN` |
| review_comment_message | str | 评价正文 | `NaN` |
| review_creation_date | datetime | 评价提交时间 | `2018-01-18 00:00:00` |
| review_answer_timestamp | datetime | 卖家回复时间 | `2018-01-18 21:46:59` |

- **规模**：98,410 行 × 7 列

---

### 3.3 olist_analysis.db（SQLite 分析库）

`02_clean.py` 将上述清洗后表写入 SQLite，供 `03_analysis.py` 与 `05_dashboard.py` 使用。表结构与 CSV 一致。

---

## 四、主外键约束汇总

| 子表 | 外键字段 | 父表 | 父键字段 | 关系类型 |
|------|----------|------|----------|----------|
| orders | customer_id | customers | customer_id | N:1 |
| order_items | order_id | orders | order_id | N:1 |
| order_items | product_id | products | product_id | N:1 |
| order_items | seller_id | sellers | seller_id | N:1 |
| order_payments | order_id | orders | order_id | N:1 |
| order_reviews | order_id | orders | order_id | N:1 |
| customers | customer_zip_code_prefix | geolocation | geolocation_zip_code_prefix | N:1 |
| sellers | seller_zip_code_prefix | geolocation | geolocation_zip_code_prefix | N:1 |
| products | product_category_name | category_translation | product_category_name | N:1 |
| closed_deals | mql_id | mql | mql_id | N:1 |
| closed_deals | seller_id | sellers | seller_id | N:1 |

---

## 五、业务语义补充说明

1. **customer_id vs customer_unique_id**：Olist 为每笔订单生成新的 `customer_id`，要统计复购需用 `customer_unique_id` 聚合。全表 99,441 个 `customer_id` 对应约 96,096 个 `customer_unique_id`，复购率约 3%。

2. **金额口径**：
   - `order_items.price`：单件商品价格（不含运费）
   - `order_items.freight_value`：单件分摊运费
   - `order_payments.payment_value`：实际支付金额（含运费、含分期）
   - `order_master.total_price`：订单商品总价（不含运费）
   - `order_master.payment_value`：订单支付总额（含运费）

3. **订单状态流转**：`approved → invoiced → processing → shipped → delivered`，任一步可 `canceled`。本数据集清洗后仅保留 `delivered` 状态用于业务分析。

4. **时间范围**：2016 年仅 328 单（9-12月试点），2017-2018 为完整年度，2018Q4 仅 4 单（数据截止 2018-08-31），分析时需按完整月份过滤。

5. **地理坐标**：`geolocation` 表同一邮编前缀有多条坐标，使用时按 `zip_code_prefix` 聚合取 `lat/lng` 均值作为该区域代表点。

---

*文档生成日期：2026-11-04 · 对应代码版本：`scripts/01_load.py` + `scripts/02_clean.py`*
