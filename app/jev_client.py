"""Jev 連携部分（未実装のスタブ）。

Jev のアカウント・API KEY を取得したら、ここに実際の呼び出しを実装する。
API の仕様（エンドポイント・リクエスト形式・レスポンス形式）がわかったら
`judge_with_jev` の中身を書き換えるだけで main.py 側は変更不要な作りにしている。
"""

import logging

from app.config import Settings
from app.schemas import PullRequestSummary, ReviewType

logger = logging.getLogger(__name__)


def is_enabled(settings: Settings) -> bool:
    return bool(settings.jev_api_key)


async def judge_with_jev(
    pr: PullRequestSummary, settings: Settings
) -> tuple[ReviewType, list[str]] | None:
    """Jev に判定させる。判定できなかった場合は None を返し、ルールベースにフォールバックする。

    TODO: Jev の API 仕様に合わせて実装する。イメージ:

        async with httpx.AsyncClient(
            base_url=settings.jev_api_base_url,
            headers={"Authorization": f"Bearer {settings.jev_api_key}"},
        ) as client:
            response = await client.post("<Jev のエンドポイント>", json={...})
            ...
    """
    logger.warning("JEV_API_KEY は設定されていますが Jev 連携は未実装です。ルールベースで判定します")
    return None
