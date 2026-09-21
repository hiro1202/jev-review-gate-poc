"""FastAPI のエントリーポイント。

起動: uvicorn app.main:app --reload
仕様書: http://localhost:8000/docs (Swagger UI) / http://localhost:8000/openapi.json
"""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

from app import jev_client
from app.config import Settings, get_settings
from app.github_client import GitHubApiError, InvalidPrUrlError, fetch_pull_request
from app.judge import judge
from app.schemas import ReviewGateRequest, ReviewGateResponse

app = FastAPI(
    title="Jev Review Gate PoC",
    description="PR の URL から、AI のみのレビューで良いか人間のレビューが必要かを判定する API",
    version="0.1.0",
)


@app.post(
    "/review-gate",
    response_model=ReviewGateResponse,
    summary="PR のレビュー方式を判定する",
    responses={
        400: {"description": "PR URL の形式が不正"},
        502: {"description": "GitHub API からの取得に失敗"},
    },
)
async def review_gate(
    request: ReviewGateRequest,
    # Depends で設定を注入する（テスト時に差し替えやすくなる）
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReviewGateResponse:
    try:
        pr = await fetch_pull_request(str(request.pr_url), settings)
    except InvalidPrUrlError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except GitHubApiError as e:
        # 404 はそのまま返し、それ以外は上流エラーとして 502 にする
        status = 404 if e.status_code == 404 else 502
        raise HTTPException(status_code=status, detail=str(e))

    # Jev が使えるなら Jev の判定を優先し、使えなければルールベースで判定する
    result = await jev_client.judge_with_jev(pr, settings) if jev_client.is_enabled(settings) else None
    review_type, reasons = result or judge(pr, settings)
    return ReviewGateResponse(review_type=review_type, reasons=reasons, pull_request=pr)
