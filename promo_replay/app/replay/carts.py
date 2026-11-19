"""购物车归一化模块：把原始订单行整理为回放购物车记录，并做 8 类清单校验。"""
from harness.carts_spec import cart_ids  # 8 类基准清单（覆盖 100% 的判定口径）


def normalize_carts(activity: dict) -> list[dict]:
    """把单活动的原始订单行归一化为回放购物车记录。

    入参：activity——{"activity_id","rule_version","orders":[...]}。
    出参：购物车记录列表，含 cart_id/cart_type/payable_original/rule_version。
    失败行为：未知类别的订单行不进回放结果，按脏数据登记进修复队列（f33）。
    """
    valid = set(cart_ids())                        # 合法类别集合
    carts: list[dict] = []                         # 归一化输出
    for od in activity.get("orders", []):          # 逐条订单行
        if od.get("cart_type") not in valid:       # 类别不在 8 类基准内
            register_repair(od.get("biz_id", "unknown"), f"未知购物车类别: {od.get('cart_type')}")  # 只进队列
            continue                               # 不进回放结果，绝不臆造归类
        carts.append({                             # 归一化后的购物车记录
            **od,                                  # 保留快照全部原始字段（复算需要金额/退款/优惠等）
            "cart_id": od["biz_id"],               # 业务编号
            "cart_type": od["cart_type"],          # 类别 id
            "payable_original": float(od.get("payable_original", 0.0)),  # 原单应付
            "rule_version": activity.get("rule_version", ""),            # 规则版本（留痕要素）
        })
    return carts                                   # 返回归一化结果


def register_repair(biz_id: str, reason: str) -> None:
    """把歧义/脏数据登记进人工修复队列（f33：绝不进自动样本）。

    入参：biz_id——业务编号；reason——原因说明。
    出参：无。失败行为：库写入失败时异常上抛（人工队列必须落库，不许静默丢）。
    """
    from app.core.db import init_db        # 延迟导入避免循环依赖
    import sqlite3                         # 标准库驱动
    from app.core.config import load_config  # 库路径来自配置
    cfg = load_config()                    # 读配置
    db_path = cfg.get("app", {}).get("db_path", "data/replay.db")  # 自有库路径
    init_db(db_path)                       # 幂等确保表存在
    conn = sqlite3.connect(db_path)        # 连接自有库
    try:                                   # 确保连接关闭
        conn.execute("INSERT INTO repair_queue (biz_id, reason) VALUES (?, ?)", (biz_id, reason))  # 入队
        conn.commit()                      # 提交
    finally:                               # 释放连接
        conn.close()
