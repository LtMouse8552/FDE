"""FastAPI 入口：只读离线回放系统的对外接口（M0 仅健康检查）。"""
from fastapi import FastAPI        # Web 框架（MVP 指定，不替换）
from app.core.response import ok   # 统一返回结构（代码规范硬约束）
from app.api.replay_api import router as replay_router  # 回放接口路由
from app.api.check_api import router as check_router    # 规则检查接口路由（REQ-1）
from app.api.manual_api import router as manual_router  # 人工兜底接口路由（f33/f44/f45）

app = FastAPI(title="促销规则与活动复盘", version="0.1.0")  # 应用实例
app.include_router(replay_router)  # 挂载回放接口（M1）
app.include_router(check_router)   # 挂载规则检查接口（M3）
app.include_router(manual_router)  # 挂载人工兜底接口（M4）


@app.get("/healthz")               # 健康检查路由
def healthz() -> dict:
    """返回服务健康状态。

    出参：统一结构 {"ok": True, "data": {...}, "error": None}。
    失败行为：无（M0 无外部依赖）。
    """
    return ok({"service": "promo-replay", "phase": "M0-skeleton"})  # 统一结构返回
