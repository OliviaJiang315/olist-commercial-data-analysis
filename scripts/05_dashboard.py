# -*- coding: utf-8 -*-
"""
05_dashboard.py - 交互式商业智能大屏
对应论文 5.3 节：Streamlit 大屏，组件≥6，全联动。
运行方式: streamlit run scripts/05_dashboard.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# 路径配置
BASE_DIR = Path(__file__).resolve().parents[1]
CLEAN_DIR = BASE_DIR / 'data' / 'clean'
TABLES_DIR = BASE_DIR / 'outputs' / 'tables'

# 页面配置
st.set_page_config(page_title="Olist 商业智能大屏", layout="wide", page_icon="📊")

# 标题
st.title("🇧🇷 Olist 巴西电商商业智能分析大屏")
st.markdown("**全 Python 实现 (Streamlit + Plotly) | 数据源: Kaggle Olist | 实时联动分析**")

# 加载数据 (使用缓存加速)
@st.cache_data
def load_data():
    master = pd.read_csv(CLEAN_DIR / 'order_master.csv', parse_dates=['order_purchase_timestamp'])
    reviews = pd.read_csv(CLEAN_DIR / 'reviews_clean.csv')
    geo = pd.read_csv(TABLES_DIR / 'geo_city_agg.csv')
    return master, reviews, geo

try:
    master, reviews, geo = load_data()
except FileNotFoundError as e:
    st.error(f" 数据文件缺失: {e}\n请先运行 `python scripts/02_clean.py` 和 `python scripts/03_analysis.py` 生成数据。")
    st.stop()

# --- 侧边栏: 全局筛选器 (组件 1) ---
st.sidebar.header(" 全局筛选器 (联动所有组件)")

# 1. 年份筛选
years = sorted(master['order_purchase_timestamp'].dt.year.unique())
selected_year = st.sidebar.selectbox("选择年份", years, index=len(years)-1)

# 2. 州筛选 (多选)
states = sorted(master['customer_state'].dropna().unique())
selected_states = st.sidebar.multiselect("选择州 (可多选)", states, default=['SP', 'RJ'])

# 3. 类目筛选 (可选，为了性能这里简化为前10大类目)
# 注意：实际项目中可以关联 products 表获取类目，这里为了演示联动，仅做州和年份筛选
# 如果需要类目筛选，需要 merge products 表，会增加复杂度，目前版本已满足 >=6 组件要求

# --- 数据过滤逻辑 ---
filtered_master = master[master['order_purchase_timestamp'].dt.year == selected_year]
if selected_states:
    filtered_master = filtered_master[filtered_master['customer_state'].isin(selected_states)]
    
filtered_reviews = reviews.merge(filtered_master[['order_id']], on='order_id')
filtered_geo = geo[geo['customer_state'].isin(selected_states)] if selected_states else geo

# --- KPI 指标卡 (组件 2, 3, 4, 5) ---
col1, col2, col3, col4 = st.columns(4)

total_gmv = filtered_master['payment_value'].sum()
total_orders = len(filtered_master)
avg_order_val = filtered_master['payment_value'].mean() if total_orders > 0 else 0
avg_score = filtered_reviews['review_score'].mean() if len(filtered_reviews) > 0 else 0

col1.metric("💰 总销售额 (GMV)", f"R$ {total_gmv:,.0f}")
col2.metric("📦 总订单数", f"{total_orders:,}")
col3.metric("🛒 平均客单价", f"R$ {avg_order_val:,.1f}")
col4.metric("⭐ 平均评分", f"{avg_score:.2f}")

st.markdown("---")

# --- 图表区域 ---

# 组件 6: 月度销售趋势 (Plotly 交互折线)
st.subheader("📈 月度销售趋势 (悬停查看详情)")
if len(filtered_master) > 0:
    monthly_sales = filtered_master.groupby(filtered_master['order_purchase_timestamp'].dt.to_period('M'))['payment_value'].sum()
    fig_line = px.line(x=monthly_sales.index.astype(str), y=monthly_sales.values, 
                       labels={'x':'月份', 'y':'销售额 (BRL)'}, template='plotly_white')
    fig_line.update_traces(line_color='#4C72B0', line_width=3)
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("当前筛选条件下无数据")

col_left, col_right = st.columns(2)

with col_left:
    # 组件 7: 州销售额排行 (Plotly 柱状)
    st.subheader("🏆 各州销售额贡献")
    if len(filtered_master) > 0:
        state_sales = filtered_master.groupby('customer_state')['payment_value'].sum().reset_index()
        fig_bar = px.bar(state_sales, x='customer_state', y='payment_value', 
                         color='payment_value', color_continuous_scale='Blues', 
                         labels={'customer_state':'州', 'payment_value':'销售额'})
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("无数据")

with col_right:
    # 组件 8: 订单状态结构 (Plotly 饼图)
    st.subheader("🥧 订单状态结构")
    if len(filtered_master) > 0:
        status_counts = filtered_master['order_status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']
        fig_pie = px.pie(status_counts, names='status', values='count', hole=0.4, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("无数据")

# 组件 9: 地理分布地图 (Plotly 散点地图)
st.subheader("🗺️ 城市订单热力分布 (点大小=订单量)")
if len(filtered_geo) > 0:
    fig_map = px.scatter_mapbox(filtered_geo, lat="geolocation_lat", lon="geolocation_lng", 
                                size="order_count", color="order_count",
                                color_continuous_scale="Reds", size_max=15, zoom=3, 
                                mapbox_style="carto-positron",
                                hover_name="customer_city", 
                                labels={'order_count':'订单量'})
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=500)
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("当前筛选条件下无地理数据")

# 组件 10: 订单明细表 (支持下钻查看)
st.subheader("📋 高价值订单明细 (TOP 50)")
if len(filtered_master) > 0:
    top_orders = filtered_master.sort_values('payment_value', ascending=False).head(50)[['order_id', 'customer_state', 'payment_value', 'order_status', 'order_purchase_timestamp']]
    st.dataframe(top_orders, use_container_width=True, hide_index=True)
else:
    st.info("无数据")

st.sidebar.markdown("---")
st.sidebar.info("💡 提示: 调整左侧筛选器，所有图表与指标将实时联动刷新。")