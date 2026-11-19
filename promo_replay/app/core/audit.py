"""审计留痕模块：六要素落库（f45）与强制转人工记录（f44）。"""
import sqlite3                                     # 标准库驱动
from app.core.db import init_db                    # 幂等建表
from app.core.config import load_config            # 库路径来自配置


def log_audit(biz_id: str, rule_version: str, trigger_reason: str,
              handler: str = "待分配", confirm_time: str | None = None,
              conclusion: str = "待人工确认") -> None:
    """写入一条六要素审计留痕（业务编号/版本/触发原因/接手人/确认时间/结论）。

    入参：六要素字段；接手人与确认时间缺省为"待分配/待人工确认"（授权人后续回填）。
    出参：无。
    失败行为：写库失败异常上抛——留痕不可静默丢失（f45）。
    """
    db_path = load_config().get("app", {}).get("db_path", "data/replay.db")  # 自有库路径
    init_db(db_path)                               # 幂等确保表存在
    conn = sqlite3.connect(db_path)                # 连接自有库
    try:                                           # 确保连接总能关闭
        conn.execute(                              # 插入六要素
            "INSERT INTO audit_logs (biz_id, rule_version, trigger_reason, handler, confirm_time, conclusion) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (biz_id, rule_version, trigger_reason, handler, confirm_time, conclusion))  # 参数化，防注入
        conn.commit()                              # 提交
    finally:                                       # 释放连接
        conn.close()
