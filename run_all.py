# -*- coding: utf-8 -*-
"""
run_all.py - 一键复现全流程

克隆仓库后，只需执行一条命令即可自动完成：
    数据加载 → 数据清洗 → 商业模型计算 → 可视化生成

用法：
    python run_all.py              # 运行全流程（01→04）
    python run_all.py --dashboard  # 全流程完成后启动 Streamlit 大屏
    python run_all.py --from 3     # 从第3步开始执行
    python run_all.py --only 4     # 仅执行第4步
    python run_all.py --check      # 仅检查环境与依赖，不执行

环境要求：Python ≥ 3.8，依赖见 requirements.txt
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / 'scripts'
RAW_DIR = BASE_DIR / 'data' / 'raw'
CLEAN_DIR = BASE_DIR / 'data' / 'clean'
FIGURES_DIR = BASE_DIR / 'outputs' / 'figures'
TABLES_DIR = BASE_DIR / 'outputs' / 'tables'

STEPS = [
    ("01_load.py",      "数据加载与合规校验",   "data/raw/ CSV 读取 + 主表规模校验"),
    ("02_clean.py",     "数据清洗与合并",       "生成 order_master.csv / reviews_clean.csv / SQLite"),
    ("03_analysis.py",  "商业模型计算",         "RFM / 同期群 / SARIMA / 漏斗 / 帕累托 / 地理聚合"),
    ("04_visuals.py",   "可视化与模板复现",     "10张模板图 + 6张业务图 → outputs/figures/"),
]

REQUIRED_PACKAGES = {
    'pandas':     'pandas',
    'numpy':      'numpy',
    'matplotlib': 'matplotlib',
    'seaborn':    'seaborn',
    'scipy':      'scipy',
    'statsmodels':'statsmodels',
    'sklearn':    'scikit-learn',
}


def banner(text, char='=', width=60):
    line = char * width
    print(f"\n{line}\n{text}\n{line}")


def check_python_version():
    if sys.version_info < (3, 8):
        print(f"[X] 需要 Python >= 3.8，当前版本 {sys.version.split()[0]}")
        sys.exit(1)
    print(f"[OK] Python {sys.version.split()[0]}")


def check_dependencies():
    missing = []
    for module, package in REQUIRED_PACKAGES.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    if missing:
        print(f"[X] 缺少依赖包: {', '.join(missing)}")
        print(f"    请先安装: pip install -r requirements.txt")
        sys.exit(1)
    print(f"[OK] 依赖包齐全 ({len(REQUIRED_PACKAGES)} 个核心包)")


def check_raw_data():
    if not RAW_DIR.exists():
        print(f"[X] 找不到数据目录: {RAW_DIR}")
        print(f"    请将 Olist CSV 文件放入 data/raw/ 后重试")
        sys.exit(1)
    csvs = list(RAW_DIR.glob('*.csv'))
    if len(csvs) < 9:
        print(f"[X] data/raw/ 下仅 {len(csvs)} 个 CSV，至少需要 9 个主表")
        sys.exit(1)
    print(f"[OK] 原始数据就绪 ({len(csvs)} 个 CSV)")


def ensure_dirs():
    for d in (CLEAN_DIR, FIGURES_DIR, TABLES_DIR):
        d.mkdir(parents=True, exist_ok=True)


def run_step(idx, script, desc, detail):
    start = time.time()
    banner(f"[{idx}/{len(STEPS)}] {desc}\n    {detail}")
    cmd = [sys.executable, str(SCRIPTS_DIR / script)]
    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    elapsed = time.time() - start
    if result.returncode != 0:
        print(f"\n[X] {script} 执行失败 (返回码 {result.returncode})，耗时 {elapsed:.1f}s")
        print(f"    全流程中止。请修复上述错误后重新运行。")
        sys.exit(result.returncode)
    print(f"\n[OK] {script} 完成，耗时 {elapsed:.1f}s")


def verify_outputs():
    print("\n--- 产出校验 ---")
    checks = [
        (CLEAN_DIR / 'order_master.csv',  "清洗后主表"),
        (CLEAN_DIR / 'reviews_clean.csv', "清洗后评价表"),
        (TABLES_DIR / 'rfm_results.csv',  "RFM 结果"),
        (TABLES_DIR / 'cohort_retention.csv', "同期群留存"),
        (TABLES_DIR / 'sarima_forecast.csv',  "SARIMA 预测"),
        (TABLES_DIR / 'pareto_abc.csv',       "帕累托分类"),
        (TABLES_DIR / 'funnel_conversion.csv',"漏斗转化"),
        (TABLES_DIR / 'geo_city_agg.csv',     "地理聚合"),
    ]
    figs = sorted(FIGURES_DIR.glob('fig*.png'))
    all_ok = True
    for path, name in checks:
        ok = path.exists() and path.stat().st_size > 0
        tag = "[OK]" if ok else "[X]"
        if not ok:
            all_ok = False
        print(f"  {tag} {name:<14s} {path.relative_to(BASE_DIR)}")
    print(f"  {'[OK]' if len(figs) >= 16 else '[X]'} 图表文件        outputs/figures/ ({len(figs)} 张)")
    if len(figs) < 16:
        all_ok = False
    return all_ok


def launch_dashboard():
    banner("启动 Streamlit 交互大屏")
    cmd = [sys.executable, "-m", "streamlit", "run", str(SCRIPTS_DIR / '05_dashboard.py')]
    try:
        subprocess.run(cmd, cwd=str(BASE_DIR))
    except KeyboardInterrupt:
        print("\n大屏已停止。")


def main():
    parser = argparse.ArgumentParser(
        description="Olist 商业数据分析 - 一键复现全流程",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n  python run_all.py            # 全流程\n  python run_all.py --dashboard  # 全流程 + 大屏"
    )
    parser.add_argument('--from', type=int, metavar='N', dest='start_from',
                        help=f'从第 N 步开始执行 (1-{len(STEPS)})')
    parser.add_argument('--only', type=int, metavar='N',
                        help=f'仅执行第 N 步 (1-{len(STEPS)})')
    parser.add_argument('--dashboard', action='store_true',
                        help='全流程完成后启动 Streamlit 大屏')
    parser.add_argument('--check', action='store_true',
                        help='仅检查环境与依赖，不执行任何步骤')
    args = parser.parse_args()

    banner("Olist 巴西电商商业数据分析 - 一键复现", char='=')

    check_python_version()
    check_dependencies()
    check_raw_data()

    if args.check:
        print("\n[OK] 环境检查通过，未执行任何步骤。")
        return

    ensure_dirs()

    if args.only:
        if not 1 <= args.only <= len(STEPS):
            print(f"[X] --only 取值范围 1-{len(STEPS)}")
            sys.exit(1)
        steps_to_run = [(args.only, *STEPS[args.only - 1])]
    else:
        start = args.start_from or 1
        if not 1 <= start <= len(STEPS):
            print(f"[X] --from 取值范围 1-{len(STEPS)}")
            sys.exit(1)
        steps_to_run = [(i, *STEPS[i - 1]) for i in range(start, len(STEPS) + 1)]

    total_start = time.time()
    for idx, script, desc, detail in steps_to_run:
        run_step(idx, script, desc, detail)

    total = time.time() - total_start
    banner(f"全流程完成! 总耗时 {total:.1f}s")

    verify_outputs()

    print(f"\n产出目录：")
    print(f"  data/clean/       清洗后数据 (order_master.csv, reviews_clean.csv, olist_analysis.db)")
    print(f"  outputs/tables/   分析结果表 (7 个 CSV)")
    print(f"  outputs/figures/  可视化图表 (16 张 PNG)")

    if args.dashboard:
        launch_dashboard()
    else:
        print(f"\n如需启动交互大屏：")
        print(f"  streamlit run scripts/05_dashboard.py")
        print(f"  或: python run_all.py --dashboard")


if __name__ == '__main__':
    main()
