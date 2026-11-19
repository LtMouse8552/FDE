"""验收断言：A 两场回放 / B 极端购物车覆盖 100% / C 负应付为零（合并口径，已拍板）。"""
from harness.carts_spec import cart_ids  # 8 类基准清单


def assert_a(result: dict) -> tuple[bool, str]:
    """断言 A：两场历史活动均完成离线回放。

    入参：result——回放结果（结构见 stub_result.build_stub_result）。
    出参：(是否通过, 说明文本)；失败不抛异常，由 runner 汇总。
    """
    acts = result.get("activities", [])              # 取活动列表
    passed = len(acts) >= 2 and all(a.get("carts") for a in acts[:2])  # 两场且场场有回放明细
    return passed, f"回放活动数={len(acts)}（要求>=2 且均有明细）"  # 说明文本


def assert_b(result: dict) -> tuple[bool, str]:
    """断言 B：8 类极端购物车全部出现且全部执行（覆盖 100%）。

    入参/出参：同 assert_a。
    """
    seen: set = set()                                # 已出现的类别集合
    for a in result.get("activities", []):           # 遍历各场
        for c in a.get("carts", []):                 # 遍历各购物车
            seen.add(c.get("cart_type"))             # 收集类别 id
    missing = [x for x in cart_ids() if x not in seen]  # 与基准清单比对得缺失项
    return not missing, f"缺失类别={missing if missing else '无'}"  # 全覆盖才通过


def assert_c(result: dict) -> tuple[bool, str]:
    """断言 C（合并口径）：复算应付均 >=0，且历史负应付单 100% 检出。

    入参/出参：同 assert_a。
    """
    carts = [c for a in result.get("activities", []) for c in a.get("carts", [])]  # 拍平所有购物车
    bad_recomp = [c["cart_id"] for c in carts      # 复算仍为负或缺失（None=未能复算，必须转人工）
                  if c.get("payable_recomputed") is None or c["payable_recomputed"] < 0]
    unflagged = [c["cart_id"] for c in carts                      # 历史负应付但未检出的编号
                 if c["payable_original"] < 0 and not c["negative_flag"]]
    passed = not bad_recomp and not unflagged         # 两条同时成立才通过
    return passed, f"复算负应付={bad_recomp if bad_recomp else '无'}; 历史负应付漏检={unflagged if unflagged else '无'}"  # 说明文本
