"""一键验证脚本：初始化数据库 + 跑全部验收断言。用法：python scripts/verify_mvp.py"""
import sys                                        # 退出码与路径调整
from pathlib import Path                          # 项目根定位

ROOT = Path(__file__).resolve().parents[1]        # 项目根（promo_replay/）
sys.path.insert(0, str(ROOT))                     # 保证可 import app / harness 包
from app.core.db import init_db                   # 数据层初始化
from harness.runner import run_all                # 断言运行器


def main() -> None:
    """执行 M0 自测：建三张表 → 跑断言 A/B/C。

    出参：无（打印报告）。
    失败行为：任一断言失败时以退出码 1 结束，供外部脚本判断。
    """
    db = init_db(str(ROOT / "data" / "replay.db"))  # 初始化自有库（幂等，可重复执行）
    print(f"[OK] 数据库就绪: {db}")                 # 打印库路径
    passed = run_all()                              # 跑全部断言
    print("[OK] MVP 自测全部通过" if passed else "[FAIL] MVP 自测存在失败项")  # 汇总结论
    sys.exit(0 if passed else 1)                    # 退出码供 CI/人工判断


if __name__ == "__main__":  # 直接运行入口
    main()                  # 执行
