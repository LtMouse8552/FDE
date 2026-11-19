"""SQLite 数据层：自有回放库（可写），创建回放记录 / 审计留痕 / 修复队列三张表。

红线说明：本库只存本系统自己的回放与留痕数据；
线上三系统（活动平台/价格引擎/经营分析库）只能以脱敏只读快照方式接入（f30/f32），
本模块的建库建表动作不触碰任何线上系统。
"""
import sqlite3             # 标准库 SQLite 驱动，不引入额外中间件
from pathlib import Path   # 建父目录用

# 三张表的 DDL：幂等设计，已存在则跳过（IF NOT EXISTS）
_DDL = """
CREATE TABLE IF NOT EXISTS replay_records (   -- 回放记录表
  id INTEGER PRIMARY KEY AUTOINCREMENT,        -- 自增主键
  activity_id TEXT NOT NULL,                   -- 活动编号
  cart_id TEXT NOT NULL,                       -- 业务编号（购物车/订单）
  cart_type TEXT,                              -- 极端购物车类别（对应 harness.carts_spec）
  payable_original REAL,                       -- 原单应付（来自只读快照）
  payable_recomputed REAL,                     -- 复算应付（M2 引擎产出，M0 为 stub）
  negative_flag INTEGER DEFAULT 0,             -- 是否检出负应付/优惠超额异常
  rule_version TEXT,                           -- 复算所用规则版本（留痕六要素之"版本"）
  created_at TEXT DEFAULT (datetime('now','localtime'))  -- 本地时间戳（f35 带时间戳）
);
CREATE TABLE IF NOT EXISTS audit_logs (        -- 审计留痕表：六要素（f45）
  id INTEGER PRIMARY KEY AUTOINCREMENT,        -- 自增主键
  biz_id TEXT NOT NULL,                        -- 要素1 业务编号
  rule_version TEXT,                           -- 要素2 版本
  trigger_reason TEXT,                         -- 要素3 触发原因
  handler TEXT,                                -- 要素4 接手人
  confirm_time TEXT,                           -- 要素5 确认时间
  conclusion TEXT,                             -- 要素6 结论
  created_at TEXT DEFAULT (datetime('now','localtime'))  -- 记录创建时间（暂留90天口径，f43）
);
CREATE TABLE IF NOT EXISTS repair_queue (      -- 人工修复队列表：歧义/脏数据只进队列不进样本（f33）
  id INTEGER PRIMARY KEY AUTOINCREMENT,        -- 自增主键
  biz_id TEXT NOT NULL,                        -- 业务编号
  reason TEXT NOT NULL,                        -- 歧义/脏数据原因说明
  status TEXT DEFAULT 'pending',               -- pending/fixed/dismissed
  created_at TEXT DEFAULT (datetime('now','localtime'))  -- 入队时间
);
"""


def init_db(db_path: str) -> str:
    """初始化自有 SQLite 库与三张表。

    入参：db_path——库文件路径（相对项目根）。
    出参：实际使用的库路径字符串。
    失败行为：目录不可写或 SQLite 报错时异常上抛，不做静默降级。
    """
    p = Path(db_path)                             # 转路径对象
    p.parent.mkdir(parents=True, exist_ok=True)   # 父目录不存在则创建
    conn = sqlite3.connect(str(p))                # 连接自有库（可写）
    try:                                          # 确保连接总能关闭
        conn.executescript(_DDL)                  # 幂等建表
        conn.commit()                             # 提交 DDL
    finally:                                      # 无论成败都释放连接
        conn.close()
    return str(p)                                 # 返回实际库路径，便于自测断言
