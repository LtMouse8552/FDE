"""配置加载模块：统一从 config.yaml 读取配置，任何环境信息禁止写死在代码里。"""
from pathlib import Path  # 路径处理，跨平台定位项目根目录
import yaml               # 解析 config.yaml（MVP 指定配置载体）

_CONFIG: dict | None = None  # 模块级缓存，进程内只读一次盘


def load_config(root: str | None = None) -> dict:
    """加载并缓存 config.yaml。

    入参：root——项目根目录（调试用），缺省按本文件位置自动定位。
    出参：配置字典。
    失败行为：配置文件缺失时抛 FileNotFoundError，立即失败不静默。
    """
    global _CONFIG                                   # 声明使用模块级缓存
    if _CONFIG is not None:                          # 已加载则直接命中缓存
        return _CONFIG
    base = Path(root) if root else Path(__file__).resolve().parents[2]  # 项目根 = core/ 上两级
    cfg_path = base / "config.yaml"                  # 配置固定放项目根目录
    if not cfg_path.exists():                        # 缺配置属系统边界校验，属致命错误
        raise FileNotFoundError(f"缺少配置文件: {cfg_path}")  # 立即失败，不降级
    with open(cfg_path, "r", encoding="utf-8") as f:  # 显式 UTF-8，规避 Windows 默认编码
        _CONFIG = yaml.safe_load(f) or {}            # 解析 YAML，空文件回退为空字典
    return _CONFIG                                   # 返回解析结果
