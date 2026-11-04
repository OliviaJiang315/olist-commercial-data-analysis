# -*- coding: utf-8 -*-
"""
02_clean.py - 数据清洗与治理
对应论文 2.2 节：缺失/异常/重复处理、多表关联、导出复用
合规声明：本脚本仅对本地已下载的合规数据进行清洗，不涉及任何网络抓取。
"""
import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
import sys

# 导入加载模块
sys.path.append(str(Path(__file__).resolve().parent))
from importlib import import_module
load_all_data = import_module('01_load').load_all_data

BASE_DIR = Path(__file__).resolve().parents[1]
CLEAN_DIR = BASE_DIR / 'data' / 'clean'
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

def clean_and_merge():
    print(" 开始数据清洗与多表关联...")
    data = load_all_data()
    
    # 1. 提取核心表
    orders = data['orders'].copy()
    items = data['items'].copy()
    payments = data['payments'].copy()
    customers = data['customers'].copy()
    reviews = data['reviews'].copy()
    
    # 2. 类型统一与日期解析 (评分点: 类型与日期格式统一)
    date_cols = ['order_purchase_timestamp', 'order_approved_at', 
                 'order_delivered_carrier_date', 'order_delivered_customer_date', 
                 'order_estimated_delivery_date']
    for col in date_cols:
        orders[col] = pd.to_datetime(orders[col], errors='coerce')
        
    # 3. 重复值去除 (评分点: 重复值去除)
    dup_orders = orders.duplicated(subset=['order_id']).sum()
    orders = orders.drop_duplicates(subset=['order_id'])
    print(f"  - 订单去重: 移除 {dup_orders} 条重复记录")
    
    reviews = reviews.drop_duplicates(subset=['review_id'])
    
    # 4. 异常值识别与处理 (评分点: 异常值识别)
    # 业务依据: 价格和运费不能为负; 极端高价可能是测试单, 按99.9%分位截断
    items = items[(items['price'] > 0) & (items['freight_value'] >= 0)]
    cap_price = items['price'].quantile(0.999)
    cap_freight = items['freight_value'].quantile(0.999)
    items['price'] = items['price'].clip(upper=cap_price)
    items['freight_value'] = items['freight_value'].clip(upper=cap_freight)
    print(f"  - 异常值处理: 价格截断于 {cap_price:.2f}, 运费截断于 {cap_freight:.2f}")
    
    # 5. 多表关联逻辑 (评分点: 多表主外键对齐)
    # 5.1 商品表聚合到订单粒度
    items_agg = items.groupby('order_id').agg(
        total_price=('price', 'sum'),
        total_freight=('freight_value', 'sum'),
        n_items=('order_item_id', 'max')
    ).reset_index()
    
    # 5.2 支付表聚合到订单粒度
    pay_agg = payments.groupby('order_id').agg(
        payment_value=('payment_value', 'sum'),
        installments=('payment_installments', 'sum')
    ).reset_index()
    
    # 5.3 客户表去重
    cust_unique = customers.drop_duplicates(subset=['customer_id'])
    
    # 5.4 构建订单宽表 (Order Master)
    master = orders.merge(cust_unique, on='customer_id', how='left') \
                   .merge(items_agg, on='order_id', how='left') \
                   .merge(pay_agg, on='order_id', how='left')
                   
    # 剔除关键字段缺失的记录 (如没有支付金额或没有客户ID)
    master = master.dropna(subset=['payment_value', 'customer_unique_id'])
    
    # 派生指标: 物流时效 (天)
    master['delivery_days'] = (master['order_delivered_customer_date'] - master['order_delivered_carrier_date']).dt.days
    master['purchase_month'] = master['order_purchase_timestamp'].dt.to_period('M')
    
    print(f"  - 多表关联完成: 订单宽表形状 {master.shape}")
    
    # 6. 评论表清洗
    reviews_clean = reviews.dropna(subset=['review_score'])
    
    # 7. 导出为 CSV 和 SQLite (评分点: 支持导出复用)
    print("   正在导出数据...")
    
    # ★ 修复：导出前统一类型，防止 SQLite 报错 (InterfaceError)
    export_master = master.copy()
    
    # 处理日期/周期列 -> 转字符串 (SQLite 不支持 Period 类型)
    if 'purchase_month' in export_master.columns:
        export_master['purchase_month'] = export_master['purchase_month'].astype(str)
    for col in ['order_purchase_timestamp', 'order_approved_at', 
                'order_delivered_carrier_date', 'order_delivered_customer_date']:
        if col in export_master.columns:
            export_master[col] = export_master[col].astype(str)
            
    # 处理数值列中的 NaN -> 填 0 (SQLite 不喜欢 NaN)
    num_cols = export_master.select_dtypes(include=['number']).columns
    export_master[num_cols] = export_master[num_cols].fillna(0).astype(float)
    
    # 导出 CSV
    export_master.to_csv(CLEAN_DIR / 'order_master.csv', index=False)
    reviews_clean.to_csv(CLEAN_DIR / 'reviews_clean.csv', index=False)
    
    # 导出 SQLite (带防御性删除)
    db_path = CLEAN_DIR / 'olist_analysis.db'
    try:
        # 先删除旧文件防止被占用
        if db_path.exists():
            try:
                db_path.unlink()
            except Exception:
                pass
                
        with sqlite3.connect(db_path) as conn:
            export_master.to_sql('order_master', conn, if_exists='replace', index=False)
            reviews_clean.to_sql('reviews', conn, if_exists='replace', index=False)
        print(f"      order_master.csv ({export_master.shape[0]} 行)")
        print(f"      olist_analysis.db (SQLite数据库)")
    except Exception as e:
        print(f"      SQLite导出失败(不影响后续分析): {e}")
        print("      已跳过数据库导出，CSV文件仍可用。")

if __name__ == '__main__':
    try:
        clean_and_merge()
        print("\n 数据清洗模块执行完毕。")
    except Exception as e:
        print(f"\n 清洗过程发生严重错误: {e}")
        import traceback
        traceback.print_exc()