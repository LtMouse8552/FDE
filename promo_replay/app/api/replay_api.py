"""回放接口：触发离线回放并返回汇总结果（只读，不写回任何线上系统）。"""
from fastapi import APIRouter     # 路由
from app.core.response import ok  # 统一返回结构
from app.core.config import load_config  # 样例/快照目录来自配置
from app.replay.orchestrator import run_replay  # 回放编排

router = APIRouter()              # 路由实例


@router.post("/replay/run")       # 触发一次回放
def replay_run() -> dict:
    """执行一次离线回放并返回汇总。

    出参：统一结构；data 含活动数、回放单量、负应付检出清单。
    失败行为：数据缺失时返回统一错误结构（不抛裸异常给调用方）。
    """
    data_dir = load_config().get("data", {}).get("sample_dir", "data/sample")  # 数据目录
    try:                           # 把引擎异常转成统一错误返回
        result = run_replay(data_dir)                # 执行回放
    except FileNotFoundError as e: # 目录缺失属边界错误
        from app.core.response import err  # 统一错误构造
        return err("DATA_NOT_FOUND", str(e))       # 明确错误码，不臆造数据（f35）
    carts = [c for a in result["activities"] for c in a["carts"]]  # 拍平统计
    return ok({                    # 汇总返回，避免整包明细刷屏
        "activities": len(result["activities"]),                     # 活动数
        "carts": len(carts),                                         # 回放单量
        "negative_detected": [c["cart_id"] for c in carts if c["negative_flag"]],  # 负应付检出清单
    })
