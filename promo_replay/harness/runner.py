"""Harness 评测运行器：python -m harness.runner 一键跑全部验收断言（M0 起闭环自检）。"""
import sys                                        # 退出码
from pathlib import Path                          # 项目根定位
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # 保证可 import app/harness 包
from app.core.config import load_config           # 配置：样例数据目录
from app.replay.orchestrator import run_replay    # M1 起真实回放编排
from harness.assertions import assert_a, assert_b, assert_c  # 三条硬线断言


def run_all() -> bool:
    """顺序执行断言 A/B/C 并打印逐条结果。

    出参：全部通过返回 True。
    失败行为：样例数据缺失时回退 M0 stub；单条失败只记录不中断，最后汇总。
    """
    data_dir = Path(load_config().get("data", {}).get("sample_dir", "data/sample"))  # 样例目录
    if data_dir.exists():                          # 样例快照存在则走真实加载链路
        result = run_replay(str(data_dir))         # 真实回放（复算仍为 stub，M2 替换）
    else:                                          # 无样例数据时回退
        from harness.stub_result import build_stub_result  # M0 假数据
        result = build_stub_result()               # 兜底
    checks = [                                     # 断言清单（名称, 断言函数）
        ("A 两场活动回放", assert_a),
        ("B 极端购物车覆盖100%", assert_b),
        ("C 负应付为零", assert_c),
    ]
    all_ok = True                                  # 汇总标志
    for name, fn in checks:                        # 逐条执行
        passed, detail = fn(result)                # 执行断言
        all_ok = all_ok and passed                 # 累计结果
        print(f"[{'PASS' if passed else 'FAIL'}] 断言{name}: {detail}")  # 逐条打印
    return all_ok                                  # 交由调用方决定退出码


if __name__ == "__main__":                          # 命令行入口
    sys.exit(0 if run_all() else 1)                 # 有失败则退出码 1，供脚本/CI 判断
