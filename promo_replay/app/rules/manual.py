"""强制转人工判定（f44）：四类触发必须转人工并标注原因/接手人/确认时间，不得静默自动通过。"""

# 异常码 → 四类强制转人工触发原因（f44 口径）
FORCED_TRIGGERS = {
    "RECOMPUTE_ERROR": "① 拆单重算口径不清/复算失败",          # 第一类：重算不清
    "PROMO_MISMATCH": "② 资料缺依据：优惠与规则版本不一致",     # 第二类：资料缺依据
    "SUBSIDY_PAYER_MISSING": "② 资料缺依据：补贴承担方字段缺失",  # 第二类：资料缺依据（f50）
    "HISTORICAL_NEGATIVE": "① 负应付风险单：须审计签核",         # 负应付须傅景签核（f40）
    "DISCOUNT_EXCEED": "① 负应付/优惠超额：复算已截断，须审计确认",  # 负应付须审计确认
    "RULE_VERSION_CONFLICT": "③ 两版本规则冲突",                # 第三类：版本冲突
    "DATA_UNAVAILABLE": "④ 关键系统不可用：快照/规则缺失",       # 第四类：系统不可用（f35）
}


def classify_manual(cart: dict) -> list[str]:
    """判定单购物车是否命中四类强制转人工触发。

    入参：cart——复算后的购物车记录（含 anomalies）。
    出参：命中的触发原因列表；未命中返回空列表。
    失败行为：无（纯判定）。
    """
    triggers = []                                  # 触发原因容器
    for ano in cart.get("anomalies", []):          # 逐个异常
        if ano in FORCED_TRIGGERS:                 # 命中四类口径之一
            triggers.append(FORCED_TRIGGERS[ano])  # 记录触发原因
    return triggers                                # 交由编排层留痕转人工
