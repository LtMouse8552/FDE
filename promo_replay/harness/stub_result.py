"""M0 样例假数据：在 M1 真实快照接入前，用脱敏样例把断言框架跑绿（复算为 stub）。"""
from harness.carts_spec import cart_ids  # 复用 8 类清单作为覆盖基准


def build_stub_result() -> dict:
    """构造两场活动 × 8 类购物车的回放结果 stub。

    出参：{"activities": [{"activity_id", "carts": [...]}]}；
    其中每个 cart 含 cart_id / cart_type / payable_original /
    payable_recomputed / negative_flag。
    失败行为：无（纯构造）。
    """
    activities = []                                  # 结果容器
    for a_no in (1, 2):                              # 两场历史活动（验收硬线 A）
        carts = []                                   # 单场活动的购物车列表
        for i, cid in enumerate(cart_ids()):         # 8 类各一条，保证覆盖 100%
            original = 100.0 + i                     # 原单应付基线（正常为正数）
            if cid == "T8":                          # T8：零元/负金额脏样本
                original = -5.0                      # 历史原单负应付（复算必须检出并转人工）
            recomputed = max(original, 0.0)          # stub 复算：修正为 >=0（M2 换真实引擎）
            carts.append({                           # 单条回放记录
                "cart_id": f"A{a_no}-C{i + 1:02d}",  # 业务编号（活动内唯一）
                "cart_type": cid,                    # 类别 id（T1..T8）
                "payable_original": original,        # 原单应付
                "payable_recomputed": recomputed,    # 复算应付
                "negative_flag": 1 if original < 0 else 0,  # 历史负应付被检出标记
            })
        activities.append({"activity_id": f"ACT-{a_no:02d}", "carts": carts})  # 单场活动
    return {"activities": activities}                # 组装总结果
