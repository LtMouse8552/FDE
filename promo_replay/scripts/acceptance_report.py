"""首期验收报告：跑全量回放 + 三条验收断言 + 红线自检，输出可追溯报告。

用法：python scripts/acceptance_report.py；任一断言失败时退出码 1。
"""
import sys                                        # 退出码
from pathlib import Path                          # 项目根定位

ROOT = Path(__file__).resolve().parents[1]        # 项目根（promo_replay/）
sys.path.insert(0, str(ROOT))                     # 保证可 import app/harness 包
import sqlite3                                    # 读取留痕/队列统计
from app.core.config import load_config           # 库路径来自配置
from app.core.db import init_db                   # 幂等建表
from app.replay.orchestrator import run_replay    # 回放编排（含复算）
from harness.assertions import assert_a, assert_b, assert_c  # 三条验收硬线


def main() -> None:
    """执行首期验收报告。

    出参：打印报告；断言失败时以退出码 1 结束。
    失败行为：数据/规则缺失异常上抛（报告前必须先修数据，不降级）。
    """
    data_dir = load_config().get("data", {}).get("sample_dir", "data/sample")  # 数据目录
    result = run_replay(data_dir)                  # 全量回放（含真实复算）
    carts = [c for a in result["activities"] for c in a["carts"]]  # 拍平统计
    checks = [                                     # 断言清单（名称, 断言函数）
        ("A 两场历史活动离线回放", assert_a),
        ("B 极端购物车覆盖 100%", assert_b),
        ("C 负应付金额为零（合并口径）", assert_c),
    ]
    all_ok = True                                  # 汇总标志
    print("=" * 60)                                # 报告头
    print("首期验收报告（REQ-1 + REQ-2，离线只读回放）")
    print("=" * 60)                                # 分隔
    for name, fn in checks:                        # 逐条执行断言
        passed, detail = fn(result)                # 执行
        all_ok = all_ok and passed                 # 累计
        print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")  # 逐条打印
    manual = [c["cart_id"] for c in carts if c.get("manual_required")]  # 强制转人工单
    print(f"回放统计: 活动={len(result['activities'])} 单量={len(carts)} "
          f"负应付检出={sum(1 for c in carts if c['negative_flag'])} "
          f"门槛重算={sum(1 for c in carts if c['threshold_recalculated'])} "
          f"强制转人工={len(manual)}")              # 统计行
    db_path = load_config().get("app", {}).get("db_path", "data/replay.db")  # 自有库
    init_db(db_path)                               # 幂等建表
    conn = sqlite3.connect(db_path)                # 读留痕与队列
    try:                                           # 确保关闭
        audit_n = conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]   # 留痕数（f45）
        repair_n = conn.execute("SELECT COUNT(*) FROM repair_queue").fetchone()[0]  # 修复队列数（f33）
    finally:                                       # 释放连接
        conn.close()
    print(f"留痕六要素记录: {audit_n} 条；人工修复队列: {repair_n} 条")  # 红线自检统计
    print("验收硬线全部通过" if all_ok else "存在未通过项，禁止进入验收")    # 汇总结论
    sys.exit(0 if all_ok else 1)                   # 退出码供外部判断


if __name__ == "__main__":  # 直接运行入口
    main()                  # 执行
