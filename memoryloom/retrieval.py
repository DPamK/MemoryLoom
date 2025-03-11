import os
import requests
from dotenv import load_dotenv
load_dotenv()

def rerank_api(query: str, docs: list[str], use_proxy: bool = False) -> list[dict]:
    """
    使用rerank模型计算query和docs的相关性

    Args:
        query (str): 查询语句
        docs (list[str]): 文档列表
        use_proxy (bool, optional): 是否使用代理. Defaults to False.

    Returns:
        list[dict]: 相关性列表
    """
    payload = {
        "query": query,
        "texts": docs
    }
    url = os.environ.get("RERANK_API", None)
    if url is None:
        raise Exception("RERANK_API is not set")
    
    if use_proxy:
        proxy = os.environ.get("PROXY_URL", None)
        if proxy is None:
            raise Exception("PROXY_URL is not set")
        response = requests.post(url, json=payload, proxies={"http": proxy})
    else:
        response = requests.post(url, json=payload)

    return response.json()

if __name__ == '__main__':
    query = "介绍下雷军"
    docs = ["乔布斯是一个老板","雷军是一个企业家"]
    resp = rerank_api(query, docs, use_proxy=True)
    print(resp) 