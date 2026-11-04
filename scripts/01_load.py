# -*- coding: utf-8 -*-
"""
01_load.py - 数据获取与加载
对应论文 2.1 节：数据源介绍与合规获取
合规声明：数据源自Kaggle Olist官方公开数据集(CC BY-NC-SA 4.0)，官网ZIP下载获取，无爬虫。
"""
import pandas as pd
from pathlib import Path
import sys

# ★ 核心：基于当前脚本位置，向上两级定位到仓库根目录
# 这样无论谁克隆仓库，都能正确找到 data/raw/
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / 'data' / 'raw'

def load_all_data():
    """从仓库内 data/raw/ 加载所有CSV，打印校验信息"""
    
    # 1. 检查数据目录是否存在
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f" 找不到数据目录: {RAW_DIR}\n"
            "请将CSV文件放入仓库的 data/raw/ 文件夹中。\n"
            "参考结构: repo/data/raw/olist_orders_dataset.csv"
        )
    
    # 2. 检查是否有CSV文件
    csv_files = list(RAW_DIR.glob('*.csv'))
    if len(csv_files) == 0:
        raise FileNotFoundError(f" data/raw/ 目录下没有找到CSV文件: {RAW_DIR}")
    
    print(f" 数据源路径: {RAW_DIR}")
    print(f" 检测到 {len(csv_files)} 个CSV文件")
    print("-" * 60)
    
    # 3. 定义期望的文件名映射 (主表 + 辅助表)
    expected_files = {
        'orders': 'olist_orders_dataset.csv',
        'items': 'olist_order_items_dataset.csv',
        'payments': 'olist_order_payments_dataset.csv',
        'reviews': 'olist_order_reviews_dataset.csv',
        'customers': 'olist_customers_dataset.csv',
        'geolocation': 'olist_geolocation_dataset.csv',
        'products': 'olist_products_dataset.csv',
        'sellers': 'olist_sellers_dataset.csv',
        'translation': 'product_category_name_translation.csv',
        # 辅助数据源（可选）
        'mql': 'olist_marketing_qualified_leads_dataset.csv',
        'deals': 'olist_closed_deals_dataset.csv'
    }
    
    data = {}
    missing_main = []
    missing_aux = []
    
    # 4. 逐个加载并校验
    for key, filename in expected_files.items():
        filepath = RAW_DIR / filename
        if filepath.exists():
            try:
                df = pd.read_csv(filepath)
                data[key] = df
                print(f"   {filename:<45s} | {df.shape[0]:>9,} 行 × {df.shape[1]} 列")
            except Exception as e:
                print(f"   {filename} 读取失败: {e}")
        else:
            # 区分主表和辅助表缺失
            if key in ['mql', 'deals']:
                missing_aux.append(filename)
            else:
                missing_main.append(filename)
                
    # 5. 警告缺失文件
    if missing_main:
        print(f"\n   缺少关键主数据文件: {missing_main}")
        print("   请确保9个主表CSV都在 data/raw/ 中")
        
    if missing_aux:
        print(f"\n   缺少辅助数据文件(非必需): {missing_aux}")
            
    # 6. ★ 评分点校验：主表记录数 ≥ 500
    if 'orders' in data:
        n = data['orders'].shape[0]
        assert n >= 500, f" 主表仅{n}条记录，不满足≥500条要求！"
        print(f"\n 主表规模校验通过: {n:,} 条记录 (要求 ≥ 500)")
    else:
        print("\n 未找到订单主表(olist_orders_dataset.csv)，无法继续！")
        sys.exit(1)
        
    return data

if __name__ == '__main__':
    print("=" * 60)
    print("开始执行: 01_load.py - 数据加载与合规校验")
    print("=" * 60)
    try:
        dfs = load_all_data()
        print(f"\n 成功加载 {len(dfs)} 个数据表")
        print(" 下一步请运行: python scripts/02_clean.py")
    except Exception as e:
        print(f"\n 加载失败: {e}")
        sys.exit(1)