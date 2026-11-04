# -*- coding: utf-8 -*-
"""
04_visuals.py - 数据可视化与模板复现 (教材30种模板严格复刻版)
对应论文 5. 节：10种模板复现 + 6张业务模型图
全 Python 实现 (Matplotlib/Seaborn)，严禁 BI 软件。
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from wordcloud import WordCloud
import sys

# 路径配置
BASE_DIR = Path(__file__).resolve().parents[1]
CLEAN_DIR = BASE_DIR / 'data' / 'clean'
TABLES_DIR = BASE_DIR / 'outputs' / 'tables'
FIG_DIR = BASE_DIR / 'outputs' / 'figures'
FIG_DIR.mkdir(parents=True, exist_ok=True)

# ★ 全局样式配置 (彻底解决中文乱码 + 教材配色)
sns.set_style("whitegrid")
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False
# 教材推荐商务配色
PALETTE = ['#4C72B0', '#DD8452', '#55A868', '#C44E52', '#8172B3', '#937860', '#DA8BC3', '#8C8C8C']
DPI = 200

def save_fig(fig, name):
    path = FIG_DIR / name
    fig.savefig(path, dpi=DPI, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  🖼️ 已生成: {name}")

def generate_template_charts(master, reviews, data_raw):
    """
    生成 10 种《Excel数据可视化》教材经典模板复现图
    严格对照教材前15/后15种模板: 深蓝背景 #1A1E43 + 亮色系列 + 白色文字
    """
    try:
        from scipy.interpolate import PchipInterpolator
    except ImportError:
        PchipInterpolator = None
    print("\n🎨 开始生成 10 种教材模板复现图...")

    # 教材模板配色 (深蓝背景 + 亮色系列, 取自 Excel chart*.xml)
    BG       = '#1A1E43'   # 深蓝背景
    GRID     = '#2A2E5A'   # 网格线
    SPINE    = '#3A3E6A'   # 边框
    C_BLUE   = '#0070C0'   # 亮蓝 (主色)
    C_BLUE_L = '#00B0F0'   # 浅亮蓝
    C_BLUE_P = '#82ADD7'   # 淡蓝
    C_GOLD   = '#FFC000'   # 金黄
    C_RED    = '#E74E69'   # 玫红
    C_PURPLE = '#7030A0'   # 紫
    C_TEAL   = '#49A098'   # 青绿
    C_ORG    = '#E66B4C'   # 橙

    def smooth_xy(x, y, n=300):
        x = np.asarray(x, float)
        y = np.asarray(y, float)
        mask = np.isfinite(y)
        x, y = x[mask], y[mask]
        if PchipInterpolator is not None and len(x) >= 2:
            xs = np.linspace(x.min(), x.max(), n)
            return xs, PchipInterpolator(x, y)(xs)
        return x, y

    def left_title(ax, text):
        ax.set_title(text, fontsize=14, fontweight='bold', loc='left', pad=12, color='white')

    def dark_style(fig, ax, polar=False):
        fig.patch.set_facecolor(BG)
        ax.set_facecolor(BG)
        ax.tick_params(colors='white', labelsize=9)
        for spine in ax.spines.values():
            spine.set_color(SPINE)
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        if not polar:
            ax.grid(False, axis='x')
            ax.grid(True, axis='y', color=GRID, linewidth=0.7, alpha=0.9,
                    linestyle=(0, (10, 5)))
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

    def dark_legend(ax, **kw):
        leg = ax.legend(frameon=False, labelcolor='white', **kw)
        return leg

    # --- 模板1: 渐变柱形图 (对应教材 No.1, chart1: 柱内垂直渐变 0070C0→00B0F0) ---
    from matplotlib.colors import LinearSegmentedColormap
    state_rev = master.groupby('customer_state')['payment_value'].sum().sort_values(ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(10, 6))
    xpos = np.arange(len(state_rev))
    vals = state_rev.values
    w = 0.38
    # 柱内垂直渐变: 底深蓝 -> 顶浅亮蓝 (与教材 gradFill ang=90° 一致)
    cmap_grad = LinearSegmentedColormap.from_list('g', [C_BLUE, C_BLUE_L])
    grad = np.linspace(1, 0, 256).reshape(-1, 1)  # 顶行=0→浅蓝, 底行=1→深蓝
    for xi, yi in zip(xpos, vals):
        ax.imshow(grad, extent=[xi-w/2, xi+w/2, 0, yi], aspect='auto',
                  cmap=cmap_grad, zorder=2, interpolation='bicubic')
    ax.bar(xpos, vals, width=w, color='none', edgecolor=C_BLUE_L, linewidth=0.8, zorder=3)
    # 柱顶数值标签 (教材 showVal=1, outEnd, 白色 9pt)
    ymax = vals.max()
    for xi, yi in zip(xpos, vals):
        ax.text(xi, yi + ymax*0.012, f'{yi:,.0f}', ha='center', va='bottom',
                fontsize=9, color='white', fontweight='bold')
    ax.set_xticks(xpos)
    ax.set_xticklabels(state_rev.index, rotation=0)
    left_title(ax, '各州销售额 TOP10 (渐变柱形图)')
    ax.set_ylabel('销售额 (BRL)')
    ax.set_ylim(0, ymax * 1.12)
    ax.set_xlim(-0.6, len(xpos) - 0.4)
    dark_style(fig, ax)
    fig.subplots_adjust(bottom=0.18)
    save_fig(fig, 'fig01_模板1_渐变柱形图.png')

    # --- 模板2: 带均值柱形图 (对应教材 No.2, chart2: 0070C0 + FFC000均值线) ---
    monthly_orders = master.groupby('purchase_month').size()
    mean_val = monthly_orders.mean()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(range(len(monthly_orders)), monthly_orders.values,
           color=C_BLUE, edgecolor=C_BLUE, width=0.62, label='月度订单量')
    ax.axhline(y=mean_val, color=C_GOLD, linestyle='--', linewidth=1.8,
               label=f'均值 ({mean_val:.0f})')
    ax.set_xticks(range(len(monthly_orders)))
    ax.set_xticklabels([str(m) for m in monthly_orders.index], rotation=45, ha='right', fontsize=8)
    left_title(ax, '月度订单量与平均水平对比 (带均值柱形图)')
    ax.set_ylabel('订单量')
    dark_legend(ax, loc='upper left')
    dark_style(fig, ax)
    fig.subplots_adjust(bottom=0.20)
    save_fig(fig, 'fig02_模板2_带均值柱形图.png')

    # --- 模板3: 标注柱形图 (对应教材 No.4, chart4: 单系列每柱独立色 + 柱顶标签) ---
    items = data_raw['items']; products = data_raw['products']; trans = data_raw['translation']
    cat_data = items.merge(products, on='product_id').merge(trans, on='product_category_name')
    cat_sales = cat_data.groupby('product_category_name_english')['price'].sum().sort_values(ascending=False).head(8)

    fig, ax = plt.subplots(figsize=(11, 6.8))
    # 教材 chart4 每柱真实配色 (dPt0-6 + 系列默认色)
    bar_colors = ['#49A098', '#E66B4C', '#FFC000', '#0097E0', '#0070C0', '#4A5BD1', '#464CAC', '#7BBDD5']
    xpos = np.arange(len(cat_sales))
    vals = cat_sales.values
    bars = ax.bar(xpos, vals, color=bar_colors[:len(vals)],
                  edgecolor='none', width=0.38)
    # 柱顶数值标签 (教材 showVal=1, outEnd) — 与柱同色的对话气泡(圆角矩形+下方小尖角)
    from matplotlib.patches import Polygon
    ymax = vals.max()
    for xi, yi, col in zip(xpos, vals, bar_colors[:len(vals)]):
        # 圆角气泡主体
        ax.text(xi, yi + ymax*0.05, f'{yi:,.0f}', ha='center', va='center',
                fontsize=9, color=BG, fontweight='bold', zorder=6,
                bbox=dict(boxstyle='round,pad=0.35', facecolor=col,
                          edgecolor=col, linewidth=0.8, mutation_aspect=0.7))
        # 下方小三角尖角指向柱顶
        tri = Polygon([(xi-0.08, yi + ymax*0.028), (xi+0.08, yi + ymax*0.028),
                       (xi, yi + ymax*0.005)],
                      facecolor=col, edgecolor=col, linewidth=0.8, zorder=5)
        ax.add_patch(tri)
    ax.set_xticks(xpos)
    ax.set_xticklabels(cat_sales.index, rotation=35, ha='right', fontsize=9)
    left_title(ax, 'TOP8 类目销售额 (标注柱形图)')
    ax.set_ylabel('销售额 (BRL)')
    ax.set_ylim(0, ymax * 1.15)
    dark_style(fig, ax)
    fig.subplots_adjust(bottom=0.10, left=0.13, right=0.97, top=0.90)
    save_fig(fig, 'fig03_模板3_标注柱形图.png')

    # --- 模板4: 层叠柱形图 (对应教材 No.5, chart5: clustered+overlap30, 0070C0 + E74E69) ---
    master['quarter'] = master['order_purchase_timestamp'].dt.to_period('Q')
    quarterly = master.groupby('quarter').agg(rev=('total_price', 'sum'),
                                               freight=('total_freight', 'sum'))
    quarterly = quarterly[quarterly['rev'] > quarterly['rev'].max() * 0.01].tail(6)
    fig, ax = plt.subplots(figsize=(10, 6))
    xpos = np.arange(len(quarterly))
    w = 0.36
    off = 0.12   # 两柱中心偏移, 红柱盖住蓝柱一部分 (overlap≈30%)
    ax.bar(xpos - off, quarterly['rev'], width=w, color=C_BLUE,
           edgecolor=BG, linewidth=0.6, label='销售额')
    ax.bar(xpos + off, quarterly['freight'], width=w, color=C_RED,
           edgecolor=BG, linewidth=0.6, label='运费')
    # 柱顶数值标签
    ymax = max(quarterly['rev'].max(), quarterly['freight'].max())
    for xi, v in zip(xpos, quarterly['rev']):
        ax.text(xi - off, v + ymax*0.012, f'{v:,.0f}', ha='center', va='bottom',
                fontsize=8, color='white', fontweight='bold')
    for xi, v in zip(xpos, quarterly['freight']):
        ax.text(xi + off, v + ymax*0.012, f'{v:,.0f}', ha='center', va='bottom',
                fontsize=8, color='white', fontweight='bold')
    ax.set_ylim(0, ymax * 1.12)
    ax.set_xticks(xpos)
    ax.set_xticklabels([str(q) for q in quarterly.index], rotation=0)
    left_title(ax, '季度销售额与运费对比 (层叠柱形图)')
    ax.set_ylabel('金额 (BRL)')
    dark_legend(ax, loc='upper left')
    dark_style(fig, ax)
    fig.subplots_adjust(bottom=0.18)
    save_fig(fig, 'fig04_模板4_层叠柱形图.png')

    # --- 模板5: 蝴蝶图 (对应教材 No.6, chart6: 0070C0 + E74E69) ---
    master['year'] = master['order_purchase_timestamp'].dt.year
    ym = master.groupby(['year', 'purchase_month']).size().unstack(fill_value=0)
    if 2017 in ym.index and 2018 in ym.index:
        cols_17 = [m for m in ym.columns if str(m)[:4] == '2017'][:6]
        cols_18 = [m for m in ym.columns if str(m)[:4] == '2018'][:6]
        n = min(len(cols_17), len(cols_18))
        cols_17, cols_18 = cols_17[:n], cols_18[:n]
        y17 = [ym.loc[2017, c] for c in cols_17]
        y18 = [ym.loc[2018, c] for c in cols_18]
        labels = [str(c)[5:] for c in cols_18]
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), sharey=True)
        h = 0.55
        # 左半: 2017红柱向左, 右半: 2018蓝柱向右, 中间y轴=月份标签
        ax1.barh(range(n), [-v for v in y17], color=C_RED, edgecolor=BG, height=h)
        ax1.tick_params(left=False, labelleft=False)  # ax1隐藏y轴
        ax2.barh(range(n), y18, color=C_BLUE, edgecolor=BG, height=h)
        ax2.tick_params(left=False, labelleft=False)  # ax2隐藏y轴
        # ax1 x刻度显示绝对值
        fig.canvas.draw()
        ax1.set_xticklabels([str(abs(int(t))) for t in ax1.get_xticks()])
        # 隐藏x轴刻度数字
        ax1.tick_params(axis='x', labelbottom=False, labeltop=False)
        ax2.tick_params(axis='x', labelbottom=False, labeltop=False)
        # 柱端数值标签 (教材 showVal=1)
        xmax = max(max(y17), max(y18))
        for yi, v in zip(range(n), y17):
            ax1.text(-v - xmax*0.012, yi, f'{v:,}', ha='right', va='center',
                     color='white', fontsize=8, fontweight='bold')
        for yi, v in zip(range(n), y18):
            ax2.text(v + xmax*0.012, yi, f'{v:,}', ha='left', va='center',
                     color='white', fontsize=8, fontweight='bold')
        # 中间空隙画月份数字
        for yi, lb in zip(range(n), labels):
            ax2.text(-xmax*0.06, yi, lb, ha='center', va='center',
                     color='white', fontsize=11, fontweight='bold', clip_on=False)
        ax1.set_title('2017年订单量', fontsize=14, fontweight='bold', loc='right', pad=12, color='white')
        left_title(ax2, '2018年订单量')
        dark_style(fig, ax1); dark_style(fig, ax2)
        ax1.grid(False); ax2.grid(False)  # 蝴蝶图无背景线
        for sp in list(ax1.spines.values()) + list(ax2.spines.values()):
            sp.set_visible(False)  # 删除所有边框竖线
        ax1.tick_params(colors='white', labelsize=8)
        ax2.tick_params(colors='white', labelsize=8)
        fig.suptitle('2017-2018年月度订单量对比 (蝴蝶图)',
                     fontsize=14, fontweight='bold', x=0.05, ha='left', color='white')
        fig.subplots_adjust(left=0.04, right=0.96, bottom=0.10, top=0.82, wspace=0.18)
        save_fig(fig, 'fig05_模板5_蝴蝶图.png')
    else:
        status_counts = master['order_status'].value_counts()
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%',
               colors=[C_BLUE, C_GOLD, C_TEAL, C_ORG, C_BLUE_P], startangle=90,
               wedgeprops=dict(width=0.4, edgecolor=BG),
               textprops={'color': 'white'})
        left_title(ax, '订单状态结构占比 (环形饼图-替代)')
        fig.patch.set_facecolor(BG)
        ax.set_facecolor(BG)
        save_fig(fig, 'fig05_模板5_蝴蝶图.png')

    # --- 模板6: 平滑折线图 (对应教材 No.11, chart11: E74E69) ---
    monthly_sales = master.groupby('purchase_month')['payment_value'].sum().tail(12)
    x = np.arange(len(monthly_sales))
    vals = monthly_sales.values
    fig, ax = plt.subplots(figsize=(10, 6))
    # B-spline 五阶样条平滑 (比 PCHIP 更光滑, C2 连续)
    try:
        from scipy.interpolate import make_interp_spline
        xs = np.linspace(x.min(), x.max(), 500)
        bspl = make_interp_spline(x, vals, k=5)
        ys = bspl(xs)
    except Exception:
        xs, ys = smooth_xy(x, vals, n=500)
    ax.plot(xs, ys, linewidth=2.86, color=C_RED, zorder=3)
    # 最高点标注数值 + 垂直虚线
    imax = int(np.argmax(vals))
    ax.scatter([x[imax]], [vals[imax]], s=40, color=C_RED, zorder=5)
    ax.text(x[imax], vals[imax] + vals.max()*0.04, f'{vals[imax]:,.0f}',
            ha='center', va='bottom', color='white', fontsize=10, fontweight='bold')
    ax.plot([x[imax], x[imax]], [0, vals[imax]], linestyle='--',
            linewidth=1.2, color=C_RED, alpha=0.7, zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels([str(m)[5:] for m in monthly_sales.index], rotation=0, fontsize=9)
    # x 轴下方年份分组标注: 11-12月=2017(蓝底), 1-10月=2018(黄底)
    years = [str(m)[:4] for m in monthly_sales.index]
    yr0, yr1 = years[0], years[-1]
    split = max(i for i, y in enumerate(years) if y == yr0)
    boundary = split + 1.0   # 01正下方为分界线
    gap = 0.06  # 两长方形之间的空隙
    # 2017 蓝色长方形
    r0 = plt.Rectangle((-0.5, -0.20), boundary - (-0.5) - gap, 0.08,
                 transform=ax.get_xaxis_transform(), facecolor=C_BLUE,
                 edgecolor='none', zorder=5, clip_on=False)
    ax.add_patch(r0)
    ax.text((0 + split) / 2, -0.16, yr0, ha='center', va='center',
            color='white', fontsize=12, fontweight='bold',
            transform=ax.get_xaxis_transform(), zorder=6, clip_on=False)
    # 2018 黄色长方形
    r1 = plt.Rectangle((boundary + gap, -0.20), (len(x) - 0.5) - boundary - gap, 0.08,
                 transform=ax.get_xaxis_transform(), facecolor=C_GOLD,
                 edgecolor='none', zorder=5, clip_on=False)
    ax.add_patch(r1)
    ax.text((split + 1 + len(x) - 1) / 2, -0.16, yr1, ha='center', va='center',
            color=BG, fontsize=12, fontweight='bold',
            transform=ax.get_xaxis_transform(), zorder=6, clip_on=False)
    left_title(ax, '月度销售额趋势 (平滑折线图)')
    ax.set_ylabel('销售额 (BRL)')
    ax.set_ylim(0, vals.max() * 1.15)
    dark_style(fig, ax)
    fig.subplots_adjust(bottom=0.28, left=0.10, right=0.96, top=0.94)
    save_fig(fig, 'fig06_模板6_平滑折线图.png')

    # --- 模板7: 对比折线图 (对应教材 No.13, chart12: E74E69 + 0070C0) ---
    # 2017 vs 2018 全年12个月对比 (9-10月2018数据不完整, 11-12月2018无数据填0)
    master['year'] = master['order_purchase_timestamp'].dt.year
    master['month'] = master['order_purchase_timestamp'].dt.month
    yoy = master.groupby(['year', 'month'])['payment_value'].sum().unstack('year')
    yoy = yoy.drop(columns=[2016])
    yoy = yoy.fillna(0)  # 2018年11/12月填0
    fig, ax = plt.subplots(figsize=(10, 6))
    x7 = np.arange(len(yoy))
    s2017 = yoy[2017].values / 1000  # 转为千元
    s2018 = yoy[2018].values / 1000
    ymax = max(s2017.max(), s2018.max())
    # 系列0: 2017 (玫红 E74E69), 系列1: 2018 (蓝 0070C0)
    ax.plot(x7, s2017, linewidth=1.5, color=C_RED, marker='o', markersize=6,
            markerfacecolor=C_RED, markeredgecolor=BG, markeredgewidth=0.8, label='2017年')
    ax.plot(x7, s2018, linewidth=1.5, color=C_BLUE, marker='o', markersize=6,
            markerfacecolor=C_BLUE, markeredgecolor=BG, markeredgewidth=0.8, label='2018年')
    # 数据标签
    for xi, yi in zip(x7, s2017):
        ax.text(xi, yi + ymax*0.03, f'{yi:.0f}', ha='center', va='bottom',
                color=C_RED, fontsize=8, fontweight='bold')
    for xi, yi in zip(x7, s2018):
        ax.text(xi, yi + ymax*0.03, f'{yi:.0f}', ha='center', va='bottom',
                color=C_BLUE, fontsize=8, fontweight='bold')
    ax.set_xticks(x7)
    ax.set_xticklabels([f'{m:02d}月' for m in yoy.index], fontsize=9)
    left_title(ax, '2017 vs 2018 月度销售额对比 (对比折线图)')
    ax.set_ylabel('销售额 (千元 BRL)')
    ax.set_ylim(0, ymax * 1.18)
    dark_legend(ax, loc='upper left')
    dark_style(fig, ax)
    fig.subplots_adjust(bottom=0.12, left=0.10, right=0.96, top=0.92)
    save_fig(fig, 'fig07_模板7_对比折线图.png')

    # --- 模板8: 单值圆环图 (对应教材 No.14, chart13: 7030A0→E74E69 渐变, holeSize=90) ---
    est = pd.to_datetime(master['order_estimated_delivery_date'])
    actual = pd.to_datetime(master['order_delivered_customer_date'])
    on_time_rate = (actual <= est).sum() / len(master)
    fig, ax = plt.subplots(figsize=(6, 6))
    # 渐变圆环: 将已完成部分分成多段, 紫→玫红渐变
    from matplotlib.colors import LinearSegmentedColormap
    n_seg = 120
    cmap = LinearSegmentedColormap.from_list('g', ['#7030A0', '#E74E69'])
    seg_vals = [on_time_rate / n_seg] * n_seg + [1 - on_time_rate]
    seg_colors = [cmap(i / (n_seg - 1)) for i in range(n_seg)] + ['#3A3E5A']
    wedges, _ = ax.pie(seg_vals, colors=seg_colors, startangle=150,
           counterclock=False, wedgeprops=dict(width=0.10, edgecolor='none'))
    ax.text(0, 0, f'{on_time_rate:.1%}', ha='center', va='center',
            fontsize=28, fontweight='bold', color='white')
    ax.text(0, -0.15, '准时送达率', ha='center', va='center',
            fontsize=12, color='#AAAAAA')
    left_title(ax, '订单准时送达率 (单值圆环图)')
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    fig.subplots_adjust(bottom=0.12, top=0.88)
    save_fig(fig, 'fig08_模板8_单值圆环图.png')

    # --- 模板9: 柱形折线图 (对应教材 No.23, chart8后15: bar=0070C0 + line=E74E69) ---
    master['year'] = master['order_purchase_timestamp'].dt.year
    master['month'] = master['order_purchase_timestamp'].dt.month
    monthly = master.groupby(['year', 'month']).size().unstack('year')
    monthly = monthly.loc[1:8]  # 取1-8月(两年都有完整数据)
    bar_vals = monthly[2018].values
    yoy_vals = (monthly[2018].values - monthly[2017].values) / monthly[2017].values
    x9 = np.arange(len(monthly))
    fig, ax1 = plt.subplots(figsize=(10, 6))
    # 柱形: 2018月度订单量 (蓝 0070C0)
    ax1.bar(x9, bar_vals, color=C_BLUE, edgecolor='none', width=0.45, zorder=2)
    for xi, yi in zip(x9, bar_vals):
        ax1.text(xi, yi + bar_vals.max()*0.02, f'{yi}', ha='center', va='bottom',
                 fontsize=9, color='white', fontweight='bold')
    ax1.set_xticks(x9)
    ax1.set_xticklabels([f'{m:02d}月' for m in monthly.index], fontsize=9)
    ax1.set_ylabel('')
    ax1.set_yticks([])
    ax1.set_ylim(0, bar_vals.max() * 2.2)
    # 折线: 同比增长率 (玫红 E74E69, 圆形标记, 不平滑)
    ax2 = ax1.twinx()
    ax2.plot(x9, yoy_vals, linewidth=1.5, color=C_RED, marker='o', markersize=6,
             markerfacecolor=C_RED, markeredgecolor=BG, markeredgewidth=0.8, zorder=4)
    for xi, yi in zip(x9, yoy_vals):
        ax2.text(xi, yi + (yoy_vals.max()-yoy_vals.min())*0.06, f'{yi:.0%}', ha='center',
                 va='bottom', fontsize=8, color=C_RED, fontweight='bold')
    ax2.set_ylabel('')
    # 精确控制: 折线在归一化坐标0.58~0.88区间(柱子顶部约在0.45)
    ymin, ymax = yoy_vals.min(), yoy_vals.max()
    lo = (ymin - 0.58/0.88 * ymax) / (1 - 0.58/0.88)
    hi = lo + (ymax - lo) / 0.88
    ax2.set_ylim(lo, hi)
    ax2.set_yticks([])
    ax2.tick_params(colors='white', labelsize=9)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.grid(False)
    left_title(ax1, '2018年月度订单量与同比增长率 (柱形折线图)')
    dark_style(fig, ax1)
    ax1.spines['left'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    ax2.spines['bottom'].set_visible(False)
    # 图例
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    leg_elems = [Patch(facecolor=C_BLUE, label='2018年订单量'),
                 Line2D([0],[0], color=C_RED, marker='o', markersize=5, label='同比增长率')]
    ax1.legend(handles=leg_elems, frameon=False, labelcolor='white', loc='upper right')
    fig.subplots_adjust(bottom=0.12, left=0.08, right=0.95, top=0.92)
    save_fig(fig, 'fig09_模板9_柱形折线图.png')

    # --- 模板10: 对比柱形图 (对应教材 No.9, chart8前15: 0070C0 + 82ADD7, gapWidth=219) ---
    cat_yearly = cat_data.merge(master[['order_id', 'order_purchase_timestamp']], on='order_id')
    cat_yearly['year'] = cat_yearly['order_purchase_timestamp'].dt.year
    cat_17 = cat_yearly[cat_yearly['year']==2017].groupby('product_category_name_english')['price'].sum()
    cat_18 = cat_yearly[cat_yearly['year']==2018].groupby('product_category_name_english')['price'].sum()
    cmp_df = pd.DataFrame({'y2017': cat_17, 'y2018': cat_18}).fillna(0)
    cmp_top = cmp_df.sort_values('y2018', ascending=False).head(5)
    fig, ax = plt.subplots(figsize=(10, 6))
    xpos = np.arange(len(cmp_top))
    w = 0.22
    gap_b = 0.025  # 每组两柱之间的小间隙
    bars1 = ax.bar(xpos - w/2 - gap_b, cmp_top['y2017'], w, color=C_BLUE, edgecolor='none', label='2017年')
    bars2 = ax.bar(xpos + w/2 + gap_b, cmp_top['y2018'], w, color='#82ADD7', edgecolor='none', label='2018年')
    # 数据标签: 高柱标签在柱外顶部, 矮柱标签在柱内顶部
    v17a = cmp_top['y2017'].values
    v18a = cmp_top['y2018'].values
    for i, bar in enumerate(bars1):
        if v17a[i] >= v18a[i]:
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+cmp_top.values.max()*0.02,
                    f'{bar.get_height()/1000:.0f}', ha='center', va='bottom', fontsize=9, color='white')
        else:
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()-cmp_top.values.max()*0.03,
                    f'{bar.get_height()/1000:.0f}', ha='center', va='top', fontsize=9, color='white', fontweight='bold')
    for i, bar in enumerate(bars2):
        if v18a[i] >= v17a[i]:
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+cmp_top.values.max()*0.02,
                    f'{bar.get_height()/1000:.0f}', ha='center', va='bottom', fontsize=9, color='white')
        else:
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()-cmp_top.values.max()*0.03,
                    f'{bar.get_height()/1000:.0f}', ha='center', va='top', fontsize=9, color='white', fontweight='bold')
    # 差值标注: 高柱顶向矮柱方向水平延伸线 + 矮柱顶向上箭头 + 差值文字
    v17a = cmp_top['y2017'].values
    v18a = cmp_top['y2018'].values
    for i in range(len(cmp_top)):
        xL = xpos[i] - w/2 - gap_b  # 2017柱中心
        xR = xpos[i] + w/2 + gap_b  # 2018柱中心
        hL, hR = v17a[i], v18a[i]
        if hL > hR:
            xh, xl = xL, xR  # 高=左(2017), 矮=右(2018)
            hh, lh = hL, hR
            line_color = C_BLUE
        else:
            xh, xl = xR, xL  # 高=右(2018), 矮=左(2017)
            hh, lh = hR, hL
            line_color = '#82ADD7'
        diff = hh - lh
        # 高柱顶部向矮柱方向水平延伸线 (与高柱同色)
        ax.plot([xh, xl], [hh, hh], color=line_color, linewidth=0.8, zorder=5)
        # 矮柱顶部向上箭头指向水平线
        ax.annotate('', xy=(xl, hh), xytext=(xl, lh),
                    arrowprops=dict(arrowstyle='->', color='white', lw=1.2))
        # 差值文字在箭头左边
        ax.text(xl - 0.06, (hh + lh) / 2, f'{diff/1000:.0f}', ha='right', va='center',
                fontsize=8, color='white', fontweight='bold')
    ax.set_xticks(xpos)
    ax.set_xticklabels(cmp_top.index, rotation=0, ha='center', fontsize=9)
    left_title(ax, 'TOP5 类目 2017 vs 2018 销售额对比 (对比柱形图)')
    ax.set_ylabel('')
    ax.set_yticks([])
    ax.set_ylim(0, cmp_top.values.max() * 1.15)
    dark_legend(ax, loc='upper right')
    dark_style(fig, ax)
    ax.spines['left'].set_visible(False)
    ax.grid(False)
    fig.subplots_adjust(bottom=0.15, left=0.10, right=0.96, top=0.92)
    save_fig(fig, 'fig10_模板10_对比柱形图.png')

def generate_business_charts(master, rfm, cohort, ts, forecast, metrics, pareto, funnel, geo):
    """生成 6 张核心业务模型图 (对应论文第4章模型)"""
    print("\n📊 开始生成 6 张业务模型图...")
    
    # 业务图 1: RFM 气泡散点图
    fig, ax = plt.subplots(figsize=(10, 7))
    segments = rfm['Segment'].unique()
    for i, seg in enumerate(segments):
        sub = rfm[rfm['Segment'] == seg]
        ax.scatter(sub['Recency'], sub['Monetary'], s=sub['Frequency']*20, alpha=0.6, label=seg, color=PALETTE[i%8], edgecolors='w')
    ax.set_title('RFM 客户价值分布 (气泡大小=频次)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Recency (天)')
    ax.set_ylabel('Monetary (BRL)')
    ax.legend(fontsize=9, loc='upper right')
    save_fig(fig, 'fig11_业务1_RFM气泡散点图.png')
    
    # 业务图 2: 同期群留存热力图
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(cohort.astype(float), annot=True, fmt='.1%', cmap='YlGnBu', ax=ax, cbar_kws={'label': '留存率'}, linewidths=0.5)
    ax.set_title('同期群留存热力图 (Cohort Retention)', fontsize=14, fontweight='bold')
    ax.set_xlabel('购买周期 (月)')
    ax.set_ylabel('获客月份 (Cohort)')
    save_fig(fig, 'fig12_业务2_同期群留存热力图.png')
    
    # 业务图 3: SARIMA 预测带 95% 置信区间
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot([str(i) for i in ts.index], ts.values, label='历史月度销售额', color=PALETTE[0], marker='o', markersize=4)
    xs_future = list(range(len(ts), len(ts)+3))
    ax.plot(xs_future, forecast['point_forecast'], 'o--', color=PALETTE[3], label='未来3月点预测', linewidth=2)
    ax.fill_between(xs_future, forecast['lower_95_ci'], forecast['upper_95_ci'], color=PALETTE[3], alpha=0.2, label='95% 置信区间')
    
    all_ticks = list(range(0, len(ts), 3)) + xs_future
    all_labels = [str(i) for i in ts.index][::3] + list(forecast.index)
    ax.set_xticks(all_ticks)
    ax.set_xticklabels(all_labels, rotation=45, fontsize=8)
    ax.set_title(f'SARIMA{metrics.order[0]}×{metrics.seasonal[0]} 销售预测 (回测MAPE={metrics.MAPE[0]:.2f}%)', fontsize=14, fontweight='bold')
    ax.set_ylabel('销售额 (BRL)')
    ax.legend()
    save_fig(fig, 'fig13_业务3_SARIMA预测置信区间图.png')
    
    # 业务图 4: 巴西点云地图
    fig, ax = plt.subplots(figsize=(10, 10))
    sc = ax.scatter(geo['geolocation_lng'], geo['geolocation_lat'], s=geo['order_count']*1.5, alpha=0.5, c=geo['order_count'], cmap='Reds', edgecolors='none')
    ax.set_title('巴西城市订单分布点云地图', fontsize=14, fontweight='bold')
    ax.axis('off')
    plt.colorbar(sc, label='订单量', shrink=0.6)
    save_fig(fig, 'fig14_业务4_巴西点云地图.png')
    
    # 业务图 5: 帕累托图 (ABC分类)
    par_top = pareto.head(15)
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.bar(range(len(par_top)), par_top['Revenue'], color=PALETTE[0], label='类目销售额')
    ax2 = ax1.twinx()
    ax2.plot(range(len(par_top)), par_top['Cumulative_Share']*100, color=PALETTE[3], marker='o', linewidth=2, label='累计占比')
    ax2.axhline(80, color='gray', linestyle='--', alpha=0.7)
    ax2.text(len(par_top)-1, 82, '80% (A类界限)', color='gray')
    ax1.set_xticks(range(len(par_top)))
    ax1.set_xticklabels(par_top.index, rotation=45, ha='right', fontsize=8)
    ax1.set_title('类目帕累托分析 (ABC分类)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('销售额 (BRL)')
    ax2.set_ylabel('累计占比 (%)')
    fig.legend(loc='upper right', bbox_to_anchor=(0.9, 0.9))
    save_fig(fig, 'fig15_业务5_帕累托图.png')
    
    # 业务图 6: 漏斗转化图
    fig, ax = plt.subplots(figsize=(8, 6))
    colors_funnel = [PALETTE[0], PALETTE[1], PALETTE[2], PALETTE[3]]
    bars = ax.barh(range(len(funnel))[::-1], funnel['Count'], color=colors_funnel, height=0.6)
    for i, (cnt, rate) in enumerate(zip(funnel['Count'], funnel['Conversion_Rate'])):
        ax.text(cnt, i, f'  {cnt:,} ({rate:.1%})', va='center', fontsize=11, fontweight='bold')
    ax.set_yticks(range(len(funnel))[::-1])
    ax.set_yticklabels(funnel['Stage'], fontsize=12)
    ax.set_title('订单履约转化漏斗', fontsize=14, fontweight='bold')
    ax.set_xlabel('订单数量')
    sns.despine()
    save_fig(fig, 'fig16_业务6_漏斗转化图.png')

if __name__ == '__main__':
    print("=" * 60)
    print("开始执行: 04_visuals.py - 可视化与模板复现")
    print("=" * 60)
    
    try:
        # 加载数据
        master = pd.read_csv(CLEAN_DIR / 'order_master.csv', parse_dates=['order_purchase_timestamp'])
        master['purchase_month'] = master['order_purchase_timestamp'].dt.to_period('M')
        reviews = pd.read_csv(CLEAN_DIR / 'reviews_clean.csv')
        
        rfm = pd.read_csv(TABLES_DIR / 'rfm_results.csv')
        cohort = pd.read_csv(TABLES_DIR / 'cohort_retention.csv', index_col=0)
        forecast = pd.read_csv(TABLES_DIR / 'sarima_forecast.csv', index_col=0)
        metrics = pd.read_csv(TABLES_DIR / 'sarima_metrics.csv')
        pareto = pd.read_csv(TABLES_DIR / 'pareto_abc.csv', index_col=0)
        funnel = pd.read_csv(TABLES_DIR / 'funnel_conversion.csv')
        geo = pd.read_csv(TABLES_DIR / 'geo_city_agg.csv')
        
        # 重建 ts 用于画图
        ts = master.groupby('purchase_month')['payment_value'].sum().asfreq('M')
        if ts.index[-1] == master['purchase_month'].max(): ts = ts[:-1]
        
        # 加载原始数据用于部分图表
        sys.path.append(str(Path(__file__).resolve().parent))
        from importlib import import_module
        load_all_data = import_module('01_load').load_all_data
        data_raw = load_all_data()
        
        generate_template_charts(master, reviews, data_raw)
        generate_business_charts(master, rfm, cohort, ts, forecast, metrics, pareto, funnel, geo)
        
        print("\n🎉 所有 16 张图表生成完毕！请查看 outputs/figures/ 目录。")
        
    except Exception as e:
        print(f"\n❌ 可视化生成失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
