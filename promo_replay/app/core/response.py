"""统一返回结构模块：所有对外接口返回 {"ok": bool, "data": ..., "error": {...}}（代码规范硬约束）。"""
from typing import Any  # data 字段可为任意类型


def ok(data: Any = None) -> dict:
    """构造成功返回。

    入参：data——业务数据，缺省 None。
    出参：统一结构字典。
    失败行为：无（纯构造函数）。
    """
    return {"ok": True, "data": data, "error": None}  # 成功时 error 恒为 None


def err(code: str, msg: str) -> dict:
    """构造失败返回。

    入参：code——稳定错误码；msg——人读错误信息。
    出参：统一结构字典。
    失败行为：无（纯构造函数）。
    """
    return {"ok": False, "data": None, "error": {"code": code, "msg": msg}}  # 失败时 data 恒为 None
