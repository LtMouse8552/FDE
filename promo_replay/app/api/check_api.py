"""规则检查接口：按活动返回异常清单与解释（REQ-1 对外入口，只读）。"""
from fastapi import APIRouter     # 路由
from app.core.response import ok, err  # 统一返回结构
from app.core.config import load_config  # 数据目录来自配置
from app.replay.orchestrator import run_replay  # 回放编排（含复算）
from app.explain.narrator import explain_activity  # 解释生成（KB 引用）

router = APIRouter()              # 路由实例


@router.get("/check/{activity_id}")  # 按活动查询
def check_activity(activity_id: str) -> dict:
    """返回指定活动的异常清单与逐单解释。

    出参：统一结构；data 含异常单清单与解释（判定依据引用 KB）。
    失败行为：数据/规则缺失返回统一错误结构，不抛裸异常。
    """
    data_dir = load_config().get("data", {}).get("sample_dir", "data/sample")  # 数据目录
    try:                                           # 引擎异常转统一错误
        result = run_replay(data_dir)              # 执行回放（含复算）
    except FileNotFoundError as e:                 # 数据/规则缺失
        return err("DATA_NOT_FOUND", str(e))       # 明确错误码，不臆造数据
    act = next((a for a in result["activities"] if a["activity_id"] == activity_id), None)  # 定位活动
    if act is None:                                # 活动不存在
        return err("ACTIVITY_NOT_FOUND", f"活动 {activity_id} 不在回放结果中")  # 统一错误
    exp = explain_activity(act)                    # 生成解释（KB 引用）
    flagged = [c["cart_id"] for c in act["carts"] if c["anomalies"]]  # 异常单清单
    return ok({"explanation": exp, "flagged_carts": flagged})  # 统一结构返回
