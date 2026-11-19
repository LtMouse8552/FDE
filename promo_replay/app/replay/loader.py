"""快照加载模块：读取脱敏快照 JSON，按业务编号去重并保留最新时间戳版本（f35）。

红线说明：快照目录是外部脱敏数据的只读入口，本模块绝不写回快照文件；
接口中断时按"带时间戳快照 + 业务编号去重补齐"的口径处理（f35）。
"""
import json                       # 解析快照 JSON
from pathlib import Path          # 遍历快照目录


def load_activities(data_dir: str) -> dict:
    """读取目录下全部 *.json 脱敏快照，合并为回放输入。

    入参：data_dir——快照目录（data/sample 或 data/snapshots）。
    出参：{"snapshot_time", "activities": [...]}；
          每条 order 附带解析后的 snapshot_time（缺省继承文件级默认值）。
    失败行为：目录不存在时抛 FileNotFoundError；单文件 JSON 损坏时抛 ValueError 上抛。
    """
    root = Path(data_dir)                          # 目录转路径对象
    if not root.exists():                          # 目录缺失属系统边界校验
        raise FileNotFoundError(f"快照目录不存在: {root}")  # 立即失败，不臆造数据（f35）
    default_ts = ""                                # 文件级默认时间戳
    merged: dict[str, dict] = {}                   # 业务编号 -> 最新订单行（去重核心）
    activities: list[dict] = []                    # 活动有序列表（保持文件内顺序）
    for fp in sorted(root.glob("*.json")):         # 逐个快照文件
        with open(fp, "r", encoding="utf-8") as f:  # 显式 UTF-8，规避 Windows 编码
            doc = json.load(f)                     # 解析快照
        default_ts = doc.get("snapshot_time", "")  # 记录文件级默认时间戳
        for act in doc.get("activities", []):      # 逐个活动
            aid = act["activity_id"]               # 活动编号
            existing = next((a for a in activities if a["activity_id"] == aid), None)  # 已合并过的活动
            if existing is None:                   # 首次出现则登记
                existing = {"activity_id": aid, "rule_version": act.get("rule_version", ""), "orders": []}
                activities.append(existing)        # 保持出现顺序
            for od in act.get("orders", []):       # 逐条订单行
                row = dict(od)                     # 拷贝避免改写原对象
                row["snapshot_time"] = row.get("snapshot_time") or default_ts  # 缺省继承文件级
                key = (aid, od["biz_id"])          # 去重键 =（活动, 业务编号）
                old = merged.get(key)              # 旧记录
                if old is None or row["snapshot_time"] >= old["snapshot_time"]:  # 比时间戳留最新
                    merged[key] = row              # 覆盖为最新版本
    for act in activities:                         # 回填去重后的订单到各活动
        act["orders"] = [r for (a, _), r in merged.items() if a == act["activity_id"]]  # 按活动过滤
    return {"snapshot_time": default_ts, "activities": activities}  # 返回合并结果
