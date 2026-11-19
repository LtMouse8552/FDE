"""异常判定：负应付 / 优惠超额 / 字段缺失 / 规则偏差（红线：缺字段不强算、显式标注交人工，f50）。"""
from app.rules.refund import recompute_after_refund, find_promo  # REQ-2 门槛重算与规则查询


def _check_promo_mismatch(cart: dict, rules: dict) -> bool:
    """规则检查（REQ-1）：原单满减优惠金额是否与规则版本定义一致。

    入参：cart——购物车记录；rules——脱敏规则版本。
    出参：True 表示存在偏差（需要人工核对）；无门槛促销返回 False。
    失败行为：规则定义缺失时返回 False（缺规则不判错，交规则版本管理流程，不臆造）。
    """
    promo_id = cart.get("promo_id")                # 原单使用的门槛促销
    if not promo_id:                               # 无门槛促销不参与校验
        return False                               # 直接通过
    rule = find_promo(rules, promo_id)             # 查规则定义
    if rule is None:                               # 规则版本缺位
        return False                               # 缺规则不判错，不臆造口径
    original = float(cart.get("promo_discount", 0.0))  # 原单执行的满减金额
    return abs(original - float(rule["discount"])) > 0.001  # 与规则定义比对（浮点容差）


def check_cart(cart: dict, rules: dict) -> dict:
    """单购物车复算与异常判定（断言 C 的数据来源）。

    入参：cart——归一化购物车记录；rules——脱敏规则版本。
    出参：复算字段字典（payable_recomputed / negative_flag / anomalies 等）。
    失败行为：字段缺失不抛异常，转为异常清单项显式标注（不臆造数据）。
    """
    goods = float(cart.get("goods_total", 0.0))    # 商品金额合计
    coupon = float(cart.get("coupon_discount", 0.0))  # 券优惠
    subsidy = float(cart.get("subsidy", 0.0))      # 补贴
    refund = float(cart.get("refund_amount", 0.0))  # 已退款（拆单）
    r = recompute_after_refund(cart, rules)        # 门槛重算（REQ-2）
    promo = float(r["promo_discount"])             # 重算后的满减优惠
    anomalies: list[str] = []                      # 异常清单
    if _check_promo_mismatch(cart, rules):         # 规则检查（REQ-1）：优惠与规则版本不一致
        anomalies.append("PROMO_MISMATCH")         # 检出规则执行偏差，转人工核对
    if subsidy and "subsidy_payer" not in cart:    # 有补贴但缺承担方字段
        anomalies.append("SUBSIDY_PAYER_MISSING")  # f50：显式标注并交人工，不强算
    eligible = round(goods - refund, 2)            # 退款后商品金额
    total_disc = round(promo + coupon + subsidy, 2)  # 优惠合计（重算口径）
    payable = round(eligible - total_disc, 2)      # 复算应付
    clamped = False                                # 是否发生优惠超额截断
    if payable < 0:                                # 优惠超过商品金额 → 负应付风险
        anomalies.append("DISCOUNT_EXCEED")        # 检出优惠超额
        payable = 0.0                              # 复算截断：输出永不产生负应付（合并口径前半）
        clamped = True                             # 标记截断
    if float(cart.get("payable_original", 0.0)) < 0:  # 历史原单应付为负
        anomalies.append("HISTORICAL_NEGATIVE")    # 合并口径后半：历史负应付 100% 检出
    negative_flag = 1 if ("HISTORICAL_NEGATIVE" in anomalies or clamped) else 0  # 检出标记
    return {                                       # 复算输出（由调用方合并进购物车记录）
        "payable_recomputed": payable,             # 复算应付（恒 >=0）
        "negative_flag": negative_flag,            # 负应付/优惠超额检出标记
        "threshold_recalculated": r["recalculated"],  # 是否触发门槛重算
        "recompute_note": r["note"],               # 重算说明（M3 解释依据）
        "anomalies": anomalies,                    # 异常清单
        "discount_clamped": clamped,               # 优惠超额截断标记
    }
