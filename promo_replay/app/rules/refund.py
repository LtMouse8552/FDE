"""退款拆单门槛重算（REQ-2 核心）：退款后金额不再达门槛时按规则版本回退优惠。

口径说明：重算只依据脱敏规则版本（rules.json），口径歧义不臆造、
显式标注"待人工确认"（数据红线 f35/f44）。
"""


def find_promo(rules: dict, promo_id: str) -> dict | None:
    """按 promo_id 在规则版本中查找门槛促销定义。

    入参：rules——规则版本字典；promo_id——促销标识。
    出参：促销定义字典；找不到返回 None。
    失败行为：无（纯查询）。
    """
    for p in rules.get("threshold_promos", []):    # 遍历门槛促销
        if p["promo_id"] == promo_id:              # 命中
            return p                               # 返回定义
    return None                                    # 未命中


def recompute_after_refund(order: dict, rules: dict) -> dict:
    """退款拆单后的门槛重算：判定退款后是否仍达门槛，不达则回退满减优惠。

    入参：order——含 goods_total/refund_amount/promo_id/promo_discount 的订单；
          rules——脱敏规则版本。
    出参：{"promo_discount": 重算后满减, "recalculated": 是否触发重算, "note": 口径说明}。
    失败行为：规则版本缺失时保留原值并在 note 标注"待人工确认"，绝不臆造。
    """
    goods = float(order.get("goods_total", 0.0))   # 商品金额合计
    refund = float(order.get("refund_amount", 0.0))  # 已退款金额（拆单）
    promo_id = order.get("promo_id")               # 使用的门槛促销
    promo = float(order.get("promo_discount", 0.0))  # 原满减优惠
    if not promo_id or refund <= 0:                # 无门槛促销或无退款
        return {"promo_discount": promo, "recalculated": False, "note": "无退款或无门槛促销，不触发重算"}  # 不触发
    rule = find_promo(rules, promo_id)             # 查规则定义
    if rule is None:                               # 规则版本缺位
        return {"promo_discount": promo, "recalculated": False, "note": "规则版本缺失，待人工确认（不臆造口径）"}  # 交人工
    eligible = round(goods - refund, 2)            # 退款后参与门槛判定的金额
    if goods >= rule["threshold"] and eligible < rule["threshold"]:  # 退款后跨过门槛 → 触发重算
        policy = rule.get("refund_policy", "proportional")  # 回退策略（proportional/full）
        if policy == "proportional":               # 按比例回退
            new_promo = round(promo * eligible / goods, 2) if goods > 0 else 0.0  # 比例 = 退款后/原金额
        else:                                      # full：全额回退
            new_promo = 0.0                        # 优惠清零
        return {"promo_discount": new_promo, "recalculated": True,  # 触发重算
                "note": f"退款后{eligible}低于门槛{rule['threshold']}，按{policy}回退：{promo}->{new_promo}"}  # 口径说明
    return {"promo_discount": promo, "recalculated": False, "note": f"退款后{eligible}仍达门槛，优惠保留"}  # 仍达门槛
