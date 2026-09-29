"""FastAPI のエントリーポイント。

起動: uvicorn app.main:app --reload
仕様書: http://localhost:8000/docs (Swagger UI) / http://localhost:8000/openapi.json
"""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

from app import jev_client
from app.config import Settings, get_settings
from app.schemas import CheckResult, JudgeRequest, JudgeResponse

app = FastAPI(
    title="Jev Checklist Judge PoC",
    description="テキストとチェック項目を受け取り、Jev で項目ごとに判定する API",
    version="0.1.0",
)


@app.post(
    "/judge",
    response_model=JudgeResponse,
    summary="チェックリストをもとにテキストを判定する",
    responses={502: {"description": "Jev の呼び出しに失敗"}},
)
async def judge_checklist(
    request: JudgeRequest,
    # Depends で設定を注入する（テスト時に差し替えやすくなる）
    settings: Annotated[Settings, Depends(get_settings)],
) -> JudgeResponse:
    # API KEY があれば Jev、なければモックで判定する
    if settings.jev_api_key:
        try:
            probabilities = await jev_client.judge(request.text, request.checklist, settings)
        except jev_client.JevError as e:
            raise HTTPException(status_code=502, detail=str(e))
        judged_by = "jev"
    else:
        probabilities = jev_client.mock_judge(request.checklist)
        judged_by = "mock"

    results = [
        CheckResult(
            id=item.id,
            passed=probabilities[item.id] >= settings.pass_threshold,
            probability=probabilities[item.id],
        )
        for item in request.checklist
    ]
    # all() はすべての要素が True のときだけ True を返す
    passed = all(r.passed for r in results)
    return JudgeResponse(passed=passed, judged_by=judged_by, results=results)
