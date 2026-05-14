from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

_client = None


def _get_client():
    global _client
    if _client is None:
        if not DEEPSEEK_API_KEY:
            raise RuntimeError(
                "DeepSeek API Key 未设置。请创建 .env 文件并设置 DEEPSEEK_API_KEY=sk-..."
            )
        _client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    return _client


def generate_workflow(prompt: str, system: str) -> str:
    """调用 DeepSeek API，返回原始 JSON 字符串。失败时重试一次。"""
    last_error = None
    for attempt in range(2):
        try:
            response = _get_client().chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=4096,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
    raise RuntimeError(f"DeepSeek API 调用失败: {last_error}")
