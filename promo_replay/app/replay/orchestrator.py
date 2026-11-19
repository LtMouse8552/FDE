"""回放编排模块：加载 → 归一化 → 复算（M2 真实引擎）→ 异常留痕 → 组装断言输入。"""
import json                                        # 解析规则版本
from pathlib import Path                           # 定位规则文件
from app.replay.loader import load_activities      # 快照加载（去重+时间戳，f35）
from app.replay.carts import normalize_carts, register_repair  # 归一化与修复队列（f33）
from app.rules.engine import recompute_cart        # 复算引擎（REQ-2）
from app.rules.manual import classify_manual       # 四类强制转人工判定（f44）
from app.core.audit import log_audit               # 六要素留痕（f45）


def load_rules(data_dir: str) -> dict:
    """读取目录下 rules.json 脱敏规则版本。

    入参：data_dir——快照目录。
    出参：规则版本字典。
    失败行为：文件缺失时抛 FileNotFoundError——规则缺位不得臆造（f35）。
    """
    fp = Path(data_dir) / "rules.json"             # 规则与快照同目录
    if not fp.exists():                            # 缺失属边界错误
        raise FileNotFoundError(f"规则版本文件缺失: {fp}")  # 不臆造规则，立即失败
    with open(fp, "r", encoding="utf-8") as f:     # 显式 UTF-8
        return json.load(f)                        # 返回规则字典


def run_replay(data_dir: str) -> dict:
    """对指定数据目录执行一次离线回放。

    入参：data_dir——脱敏快照目录。
    出参：{"activities":[{"activity_id","carts":[...]}]}，每个 cart 含复算结果与异常清单。
    失败行为：数据/规则缺失异常上抛，由调用方转统一错误返回。
    """
    doc = load_activities(data_dir)                # 只读加载 + 业务编号去重（f35）
    rules = load_rules(data_dir)                   # 脱敏规则版本
    result = {"activities": []}                    # 输出容器
    for act in doc["activities"]:                  # 逐场活动回放
        done: list[dict] = []                      # 本场已复算购物车
        for c in normalize_carts(act):             # 归一化（未知类别已进修复队列）
            merged = recompute_cart(c, rules)      # 真实复算（REQ-2）
            if merged["cart_type"] == "T8":        # T8 零元/负金额脏样本
                register_repair(merged["cart_id"], "零元/负金额脏样本（f33：只进队列不进样本）")  # 进修复队列
            for ano in merged["anomalies"]:        # 负应付/优惠超额/缺字段 = 强制转人工情形（f44）
                log_audit(merged["cart_id"], c.get("rule_version", ""), ano)  # 检出即留痕，绝不静默自动通过
            triggers = classify_manual(merged)     # 四类强制转人工判定（f44）
            merged["manual_required"] = bool(triggers)  # 标注是否强制转人工
            merged["manual_triggers"] = triggers   # 触发原因（解释与交接用）
            done.append(merged)                    # 收集本场结果
        result["activities"].append({"activity_id": act["activity_id"], "carts": done})  # 单场结果
    return result                                  # 断言输入
