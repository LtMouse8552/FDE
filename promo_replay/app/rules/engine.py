"""复算引擎入口：单购物车复算（M2 真实实现，M0/M1 的 stub 已替换）。"""
from app.rules.checks import check_cart  # 复算与异常判定


def recompute_cart(cart: dict, rules: dict) -> dict:
    """复算单购物车并合并复算结果。

    入参：cart——归一化购物车记录；rules——脱敏规则版本。
    出参：合并后的购物车记录（原始字段 + 复算字段）。
    失败行为：单点复算异常不中断整场回放，转为 RECOMPUTE_ERROR 异常项交人工（f44）。
    """
    try:                                           # 隔离单点故障
        out = check_cart(cart, rules)              # 复算
        out["anomalies"] = out["anomalies"] or []  # 保证清单类型稳定
    except Exception as e:                         # 任何复算异常
        out = {                                    # 降级输出：绝不臆造金额
            "payable_recomputed": None,            # None = 未能复算，必须转人工
            "negative_flag": 0,                    # 未检出（因为没能算）
            "threshold_recalculated": False,       # 未触发重算
            "recompute_note": "",                  # 无说明
            "anomalies": [f"RECOMPUTE_ERROR: {e}"],  # 异常清单记录原因
            "discount_clamped": False,             # 未截断
        }
    return {**cart, **out}                         # 合并原始与复算字段
