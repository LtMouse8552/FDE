"""人工兜底接口：审计留痕查询（f45）/ 修复队列查询（f33）/ 授权人确认回填（f40/f44）。

红线说明：确认动作只能由授权人执行；系统只提供依据与待确认记录，不代替签核（f22/f40）。
"""
from fastapi import APIRouter     # 路由
from pydantic import BaseModel    # 请求体模型
import sqlite3                    # 标准库驱动
from app.core.response import ok  # 统一返回结构
from app.core.config import load_config  # 库路径来自配置
from app.core.db import init_db   # 幂等建表

router = APIRouter()              # 路由实例


def _db() -> sqlite3.Connection:  # 内部：打开自有库连接
    """打开自有 SQLite 连接（调用方负责关闭）。出参：连接对象；无失败分支（异常上抛）。"""
    db_path = load_config().get("app", {}).get("db_path", "data/replay.db")  # 库路径
    init_db(db_path)               # 幂等确保表存在
    return sqlite3.connect(db_path)  # 返回连接


@router.get("/manual/audit")      # 审计留痕查询
def list_audit() -> dict:
    """返回全部审计留痕（六要素）。出参：统一结构；无失败分支（异常上抛由框架兜底）。"""
    conn = _db()                   # 打开连接
    try:                           # 确保关闭
        rows = conn.execute(       # 读取六要素
            "SELECT id, biz_id, rule_version, trigger_reason, handler, confirm_time, conclusion "
            "FROM audit_logs ORDER BY id DESC").fetchall()  # 新的在前
    finally:                       # 释放连接
        conn.close()
    keys = ["id", "biz_id", "rule_version", "trigger_reason", "handler", "confirm_time", "conclusion"]  # 列名
    return ok([dict(zip(keys, r)) for r in rows])  # 统一结构返回


@router.get("/manual/queue")      # 修复队列查询
def list_queue() -> dict:
    """返回人工修复队列（f33：歧义/脏数据只进队列不进样本）。"""
    conn = _db()                   # 打开连接
    try:                           # 确保关闭
        rows = conn.execute("SELECT id, biz_id, reason, status, created_at FROM repair_queue ORDER BY id DESC").fetchall()  # 全量
    finally:                       # 释放连接
        conn.close()
    keys = ["id", "biz_id", "reason", "status", "created_at"]  # 列名
    return ok([dict(zip(keys, r)) for r in rows])  # 统一结构返回


class ConfirmBody(BaseModel):     # 确认请求体
    audit_id: int                  # 留痕记录 id
    handler: str                   # 接手人（授权人）
    conclusion: str                # 结论


@router.post("/manual/confirm")   # 授权人确认
def confirm(body: ConfirmBody) -> dict:
    """授权人回填接手人/确认时间/结论，完成六要素（f45）。

    入参：body——留痕 id + 接手人 + 结论。
    出参：统一结构；确认时间由服务端写入本地时间。
    失败行为：留痕不存在时返回统一错误结构。
    """
    conn = _db()                   # 打开连接
    try:                           # 确保关闭
        cur = conn.execute(        # 回填三要素（确认时间取服务端时间）
            "UPDATE audit_logs SET handler = ?, confirm_time = datetime('now','localtime'), conclusion = ? "
            "WHERE id = ?", (body.handler, body.conclusion, body.audit_id))  # 参数化防注入
        conn.commit()              # 提交
        if cur.rowcount == 0:      # 留痕不存在
            from app.core.response import err  # 统一错误构造
            return err("AUDIT_NOT_FOUND", f"留痕 {body.audit_id} 不存在")  # 明确错误码
    finally:                       # 释放连接
        conn.close()
    return ok({"audit_id": body.audit_id, "confirmed": True})  # 返回确认结果
