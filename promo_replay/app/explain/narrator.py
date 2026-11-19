"""解释生成模块：把复算结果转为可读解释，并引用 KB 检索依据（REQ-1 复盘解释）。"""
from app.explain.kb import retrieve  # 知识库检索（仅作解释依据）

# 异常码 → 人读说明 + 检索关键词（脱敏口径，来源 kb/conclusions）
_ANOMALY_TEXT = {
    "HISTORICAL_NEGATIVE": ("历史原单应付为负（优惠超过商品金额），属真实资金损失风险单", ["负应付", "优惠超额"]),
    "DISCOUNT_EXCEED": ("复算检出优惠合计超过商品金额，复算应付已截断为 0", ["优惠超额", "负应付"]),
    "SUBSIDY_PAYER_MISSING": ("补贴承担方字段缺失，涉及补贴的毛利口径未计算，转人工修复", ["补贴承担方", "字段缺失"]),
    "PROMO_MISMATCH": ("原单满减优惠与规则版本定义不一致，需人工核对规则执行链路", ["门槛促销", "满减"]),
}


def explain_cart(cart: dict) -> dict:
    """为单购物车生成解释（判定依据 + KB 引用）。

    入参：cart——复算后的购物车记录（含 anomalies/recompute_note 等）。
    出参：{"summary": 一句话结论, "details": 逐条异常解释, "evidence": KB 依据引用}。
    失败行为：检索不到依据时 evidence 为空并在 summary 明示，绝不编造。
    """
    details = []                                   # 逐条异常解释
    terms: list[str] = [cart.get("cart_type", "")]  # 检索词：类别打底
    for ano in cart.get("anomalies", []):          # 逐个异常
        text, kw = _ANOMALY_TEXT.get(ano, (f"未识别异常: {ano}（待人工确认）", []))  # 未知异常不解释成结论
        details.append({"code": ano, "text": text})  # 记录解释
        terms.extend(kw)                           # 聚合检索词
    if cart.get("threshold_recalculated"):         # 触发了门槛重算
        details.append({"code": "THRESHOLD_RECALC", "text": cart.get("recompute_note", "")})  # 重算口径入解释
        terms.extend(["退款拆单", "门槛"])          # 追加检索词
    evidence = retrieve(terms)                     # 检索依据（仅作解释，不作放行依据）
    neg = cart.get("negative_flag", 0)             # 负应付/优惠超额标记
    summary = ("检出负应付/优惠超额异常，已转人工留痕" if neg
               else "复算通过，未检出异常")          # 一句话结论
    if not evidence:                               # 库中无依据
        summary += "（KB 无检索依据，仅复算数值，请人工核对）"  # 明示不足，不编造
    return {"summary": summary, "details": details, "evidence": evidence}  # 解释结构


def explain_activity(activity: dict) -> dict:
    """为单场活动生成逐单解释清单。

    入参：activity——{"activity_id", "carts": [复算后购物车]}。
    出参：{"activity_id", "explanations": [逐单解释]}；无失败分支。
    """
    return {                                       # 单场解释
        "activity_id": activity["activity_id"],    # 活动编号
        "explanations": [                          # 逐单解释
            {"cart_id": c["cart_id"], **explain_cart(c)} for c in activity.get("carts", [])
        ],                                         # 逐单解释列表
    }
