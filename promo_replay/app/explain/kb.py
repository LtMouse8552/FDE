"""知识库检索模块：RAG + LLM Wiki 的最小实现，只提供"解释依据"，绝不作为放行/改价/发资金的依据。

红线说明：仅检索 kb/ 下脱敏资料；检索不到时明示"无检索依据"，绝不编造。
"""
from pathlib import Path   # 遍历 kb 目录

_KB_DIR = Path(__file__).resolve().parents[2] / "kb"  # 知识库根目录（项目根/kb）


def _load_docs() -> list[dict]:
    """加载 kb/ 下全部 Markdown 文档。

    出参：[{"path": 相对路径, "text": 全文}]。
    失败行为：目录缺失返回空列表（检索时明示无依据），不抛异常。
    """
    docs: list[dict] = []                          # 文档容器
    if not _KB_DIR.exists():                       # 知识库未初始化
        return docs                                # 空列表，交由调用方明示
    for fp in sorted(_KB_DIR.rglob("*.md")):       # 递归读取全部 md
        with open(fp, "r", encoding="utf-8") as f:  # 显式 UTF-8
            docs.append({"path": str(fp.relative_to(_KB_DIR)), "text": f.read()})  # 记录来源便于追溯
    return docs                                    # 返回文档集


def retrieve(query_terms: list[str], top_k: int = 3) -> list[dict]:
    """按关键词命中数检索知识库，返回最相关的文档片段。

    入参：query_terms——业务关键词（如类别、异常码）；top_k——返回条数。
    出参：[{"path", "snippet", "score"}]，按相关度降序。
    失败行为：无命中或库为空时返回空列表，由解释层明示"无检索依据"。
    """
    hits: list[dict] = []                          # 命中容器
    for doc in _load_docs():                       # 逐文档打分
        score = sum(1 for t in query_terms if t and t in doc["text"])  # 关键词命中计数
        if score > 0:                              # 有命中才算相关
            snippet = doc["text"][:200].replace("\n", " ")  # 摘要片段（脱敏资料，可直接展示）
            hits.append({"path": doc["path"], "snippet": snippet, "score": score})  # 记录依据
    hits.sort(key=lambda h: -h["score"])           # 相关度降序
    return hits[:top_k]                            # 截取 top_k
