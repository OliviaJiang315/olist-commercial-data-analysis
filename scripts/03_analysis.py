# -*- coding: utf-8 -*-
"""
03_analysis.py - 商业分析模型计算
对应论文 4. 节：RFM、同期群、SARIMA预测、漏斗与帕累托
合规声明：所有模型均基于本地清洗后的合规数据计算，参数设定有明确业务依据。
"""
import pandas as pd
import numpy as np
import warnings
from pathlib import Path
import statsmodels.api as sm
import sys

warnings.filterwarnings('ignore')

BASE_DIR = Path(__file__).resolve().parents[1]
CLEAN_DIR = BASE_DIR / 'data' / 'clean'
TABLES_DIR = BASE_DIR / 'outputs' / 'tables'
TABLES_DIR.mkdir(parents=True, exist_ok=True)

def run_rfm_model(master):
    """模型1: RFM 客户价值分析 (八分类)"""
    print("\n📈 [模型1] 运行 RFM 客户价值分析...")
    
    # 业务依据: 快照时间设为数据中最大购买时间 + 1天
    snapshot_date = master['order_purchase_timestamp'].max() + pd.Timedelta(days=1)
    
    rfm = master.groupby('customer_unique_id').agg(
        Recency=('order_purchase_timestamp', lambda x: (snapshot_date - x.max()).days),
        Frequency=('order_id', 'nunique'),
        Monetary=('payment_value', 'sum')
    ).reset_index()
    
    # ★ 参数设定依据 (论文重点):
    # R, M 使用中位数切分。
    # F 因该平台复购率极低(中位数=1), 使用中位数切分会导致High组过小, 
    # 故改为 F>=2 即为 High (业务含义: 发生复购即为高忠诚)
    r_median = rfm['Recency'].median()
    m_median = rfm['Monetary'].median()
    
    rfm['R_Score'] = np.where(rfm['Recency'] <= r_median, 'High', 'Low') # R越小越好
    rfm['F_Score'] = np.where(rfm['Frequency'] >= 2, 'High', 'Low')     # F>=2 为 High
    rfm['M_Score'] = np.where(rfm['Monetary'] > m_median, 'High', 'Low')
    
    # 八分类映射函数
    def get_segment(row):
        if row['R_Score'] == 'High' and row['F_Score'] == 'High' and row['M_Score'] == 'High': return '重要价值客户'
        if row['R_Score'] == 'High' and row['F_Score'] == 'High' and row['M_Score'] == 'Low': return '重要发展客户'
        if row['R_Score'] == 'High' and row['F_Score'] == 'Low' and row['M_Score'] == 'High': return '重要保持客户'
        if row['R_Score'] == 'High' and row['F_Score'] == 'Low' and row['M_Score'] == 'Low': return '重要挽留客户'
        if row['R_Score'] == 'Low' and row['F_Score'] == 'High' and row['M_Score'] == 'High': return '一般价值客户'
        if row['R_Score'] == 'Low' and row['F_Score'] == 'High' and row['M_Score'] == 'Low': return '一般发展客户'
        if row['R_Score'] == 'Low' and row['F_Score'] == 'Low' and row['M_Score'] == 'High': return '一般保持客户'
        return '一般挽留客户'
        
    rfm['Segment'] = rfm.apply(get_segment, axis=1)
    rfm.to_csv(TABLES_DIR / 'rfm_results.csv', index=False)
    
    print(f"  - RFM 阈值: R中位数={r_median:.0f}天, M中位数={m_median:.2f}, F高阈值=2单")
    print(rfm['Segment'].value_counts())
    return rfm

def run_cohort_model(master):
    """模型2: 同期群留存分析"""
    print("\n📈 [模型2] 运行同期群留存分析...")
    
    # 获取每个客户的首次购买月份作为 Cohort
    master['cohort_month'] = master.groupby('customer_unique_id')['purchase_month'].transform('min')
    
    # 计算周期差 (月)
    master['period'] = (master['purchase_month'] - master['cohort_month']).apply(lambda x: x.n)
    
    # 构建留存矩阵
    cohort_data = master.groupby(['cohort_month', 'period'])['customer_unique_id'].nunique().reset_index()
    cohort_pivot = cohort_data.pivot(index='cohort_month', columns='period', values='customer_unique_id')
    
    # 计算留存率 (除以第0期的用户数)
    cohort_size = cohort_pivot[0]
    retention = cohort_pivot.divide(cohort_size, axis=0)
    
    # 只保留前8期用于展示
    retention = retention.iloc[:, :8]
    retention.to_csv(TABLES_DIR / 'cohort_retention.csv')
    
    avg_retention_m1 = retention[1].mean() * 100 if 1 in retention.columns else 0
    print(f"  - 同期群首月(M1)平均留存率: {avg_retention_m1:.2f}%")
    return retention

def run_sarima_model(master):
    """模型3: SARIMA 时间序列预测 (含AIC选参+95%CI+回测)"""
    print("\n📈 [模型3] 运行 SARIMA 销售预测...")
    
    # 按月汇总销售额
    ts_monthly = master.groupby('purchase_month')['payment_value'].sum().asfreq('M')
    
    # 剔除最后一个不完整月 (如果存在)
    if ts_monthly.index[-1] == master['purchase_month'].max():
        ts_monthly = ts_monthly[:-1]
        
    # 划分训练集和测试集 (最后3个月作为测试集回测)
    train, test = ts_monthly[:-3], ts_monthly[-3:]
    
    # ★ AIC 网格选参 (业务依据: 电商具有年度季节性 s=12, 但数据仅约25个月, 需稳健选参)
    best_aic = np.inf
    best_order = (1, 1, 1)
    best_seasonal = (0, 1, 1, 12)
    best_res = None
    
    candidates_order = [(1, 1, 1), (0, 1, 1), (1, 1, 0)]
    candidates_seasonal = [(0, 1, 1, 12), (1, 1, 0, 12), (0, 0, 0, 0)]
    
    print("  - 正在进行 AIC 网格搜索选参...")
    for order in candidates_order:
        for seasonal in candidates_seasonal:
            try:
                model = sm.tsa.SARIMAX(train, order=order, seasonal_order=seasonal, 
                                     enforce_stationarity=False, enforce_invertibility=False)
                res = model.fit(disp=False)
                if res.aic < best_aic:
                    best_aic = res.aic
                    best_order = order
                    best_seasonal = seasonal
                    best_res = res
            except Exception:
                continue
                
    # 回测误差计算
    forecast_test = best_res.get_forecast(steps=3)
    pred_mean = forecast_test.predicted_mean
    mape = np.mean(np.abs((test.values - pred_mean.values) / test.values)) * 100
    rmse = np.sqrt(np.mean((test.values - pred_mean.values)**2))
    
    # 全量数据拟合进行未来预测 (含95%置信区间)
    full_model = sm.tsa.SARIMAX(ts_monthly, order=best_order, seasonal_order=best_seasonal,
                              enforce_stationarity=False, enforce_invertibility=False)
    full_res = full_model.fit(disp=False)
    future_forecast = full_res.get_forecast(steps=3)
    future_mean = future_forecast.predicted_mean
    future_ci = future_forecast.conf_int(alpha=0.05)
    
    # 保存结果
    forecast_df = pd.DataFrame({
        'point_forecast': future_mean.values,
        'lower_95_ci': future_ci.iloc[:, 0].values,
        'upper_95_ci': future_ci.iloc[:, 1].values
    }, index=future_mean.index.astype(str))
    forecast_df.to_csv(TABLES_DIR / 'sarima_forecast.csv')
    
    metrics_df = pd.DataFrame({
        'order': [str(best_order)], 
        'seasonal': [str(best_seasonal)], 
        'AIC': [best_aic], 
        'MAPE': [mape], 
        'RMSE': [rmse]
    })
    metrics_df.to_csv(TABLES_DIR / 'sarima_metrics.csv', index=False)
    
    print(f"  - 最优参数: order={best_order}, seasonal={best_seasonal}")
    print(f"  - 回测误差: MAPE={mape:.2f}%, RMSE={rmse:.2f}")
    
    return ts_monthly, forecast_df, metrics_df

def run_funnel_and_pareto(master, data_raw):
    """辅助分析: 漏斗转化 & 帕累托ABC"""
    print("\n📈 [辅助分析] 运行漏斗转化 & 帕累托ABC...")
    
    # 漏斗: 订单状态流转
    funnel = pd.DataFrame({
        'Stage': ['下单(Placed)', '审批(Approved)', '发货(Shipped)', '妥投(Delivered)'],
        'Count': [
            len(master),
            master['order_approved_at'].notna().sum(),
            master['order_delivered_carrier_date'].notna().sum(),
            master['order_delivered_customer_date'].notna().sum()
        ]
    })
    funnel['Conversion_Rate'] = funnel['Count'] / funnel['Count'].iloc[0]
    funnel.to_csv(TABLES_DIR / 'funnel_conversion.csv', index=False)
    print(funnel)
    
    # 帕累托: 类目ABC分类
    items = data_raw['items']
    products = data_raw['products']
    trans = data_raw['translation']
    
    # 关联类目英文名
    cat_sales = items.merge(products, on='product_id').merge(trans, on='product_category_name')
    cat_rev = cat_sales.groupby('product_category_name_english')['price'].sum().sort_values(ascending=False)
    
    pareto = pd.DataFrame({'Revenue': cat_rev})
    pareto['Cumulative_Share'] = pareto['Revenue'].cumsum() / pareto['Revenue'].sum()
    pareto['ABC_Class'] = np.where(pareto['Cumulative_Share'] <= 0.8, 'A', 
                          np.where(pareto['Cumulative_Share'] <= 0.95, 'B', 'C'))
    pareto.to_csv(TABLES_DIR / 'pareto_abc.csv')
    
    a_count = (pareto['ABC_Class'] == 'A').sum()
    print(f"  - 帕累托分析: A类核心类目数量 = {a_count}")
    
    return funnel, pareto
# ... (前面的 import 和 run_rfm_model, run_cohort_model, run_sarima_model, run_funnel_and_pareto 函数保持不变) ...

# ★ 新增：地理聚合函数 (修复报错的关键)
def run_geo_aggregation(master, data_raw):
    """将订单与客户地理位置关联，聚合到城市/区域级别"""
    print("\n📈 [辅助分析] 运行地理聚合...")
    
    geo = data_raw['geolocation']
    customers = data_raw['customers']
    
    # 1. 按邮编前缀聚合经纬度 (取均值作为城市/区域中心)
    # 注意：geolocation表很大，这里只取必要列加速
    geo_center = geo.groupby('geolocation_zip_code_prefix')[['geolocation_lat', 'geolocation_lng']].mean().reset_index()
    
    # 2. 关联客户表
    cust_geo = customers.merge(geo_center, left_on='customer_zip_code_prefix', right_on='geolocation_zip_code_prefix', how='left')
    
    # 3. 关联订单主表
    order_geo = master.merge(cust_geo[['customer_id', 'geolocation_lat', 'geolocation_lng']], on='customer_id', how='inner')
    
    # 4. 按城市聚合订单量
    city_agg = order_geo.groupby(['customer_city', 'customer_state', 'geolocation_lat', 'geolocation_lng']).size().reset_index(name='order_count')
    
    # 5. 导出
    city_agg.to_csv(TABLES_DIR / 'geo_city_agg.csv', index=False)
    print(f"  - 地理聚合完成: {len(city_agg)} 个城市/区域节点已保存至 geo_city_agg.csv")
    return city_agg

if __name__ == '__main__':
    print("=" * 60)
    print("开始执行: 03_analysis.py - 商业模型计算")
    print("=" * 60)
    
    try:
        # 加载清洗后的主表
        master = pd.read_csv(CLEAN_DIR / 'order_master.csv', parse_dates=['order_purchase_timestamp'])
        master['purchase_month'] = master['order_purchase_timestamp'].dt.to_period('M')
        
        # 加载原始数据用于帕累托和地理分析
        sys.path.append(str(Path(__file__).resolve().parent))
        from importlib import import_module
        load_all_data = import_module('01_load').load_all_data
        data_raw = load_all_data()
        
        # 执行模型
        rfm = run_rfm_model(master)
        cohort = run_cohort_model(master)
        ts, forecast, metrics = run_sarima_model(master)
        funnel, pareto = run_funnel_and_pareto(master, data_raw)
        
        # ★ 新增：执行地理聚合
        geo = run_geo_aggregation(master, data_raw)
        
        print("\n 所有商业模型计算完毕，结果已保存至 outputs/tables/")
        
    except Exception as e:
        print(f"\n 模型计算失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)