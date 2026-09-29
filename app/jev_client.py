"""Jev（TypeSafe AI）の呼び出し部分。

API 仕様: https://docs.typesafe.ai/api
- POST {base_url}/v1/systemone
- テキストを state に、チェック項目を noul（yes/no の確率を返す質問）として送る
- レスポンスの answers[質問ID].noul に 0〜1 の確率が入って返ってくる
"""

import httpx

from app.config import Settings
from app.schemas import CheckItem


class JevError(RuntimeError):
    """Jev で判定できなかったときのエラー。"""


def build_body(text: str, checklist: list[CheckItem], model: str) -> dict:
    """Jev に送るリクエストボディを作る。"""
    return {
        "state": text,
        "model": model,
        # 辞書内包表記: {キー: 値 for ...} で辞書を1行で作れる
        "questions": {
            item.id: {"type": "noul", "instructions": item.description} for item in checklist
        },
    }


async def judge(text: str, checklist: list[CheckItem], settings: Settings) -> dict[str, float]:
    """Jev に判定させて {項目ID: yes の確率} を返す。"""
    body = build_body(text, checklist, settings.jev_model)
    headers = {"Authorization": f"Bearer {settings.jev_api_key}"}

    try:
        # async with を使うとブロックを抜けるときに接続を自動で閉じてくれる
        async with httpx.AsyncClient(base_url=settings.jev_api_base_url, timeout=30.0) as client:
            response = await client.post("/v1/systemone", json=body, headers=headers)
    except httpx.HTTPError as e:
        raise JevError(f"Jev に接続できません: {e!r}") from e

    if response.status_code != 200:
        raise JevError(f"Jev API エラー ({response.status_code}): {response.text[:200]}")

    try:
        answers = response.json()["answers"]
        return {item.id: float(answers[item.id]["noul"]) for item in checklist}
    except (ValueError, KeyError, TypeError) as e:
        # 想定外の形のレスポンスも Jev のエラーとして扱う（main で 502 になる）
        raise JevError(f"Jev のレスポンスを解釈できません: {e!r}") from e


def mock_judge(checklist: list[CheckItem]) -> dict[str, float]:
    """Jev なしで動作確認するためのモック。全項目を確率 1.0（yes）にする。"""
    return {item.id: 1.0 for item in checklist}
