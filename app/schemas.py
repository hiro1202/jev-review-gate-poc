"""API の入出力の型定義（Pydantic モデル）。

FastAPI はここで定義したモデルから
- リクエストのバリデーション
- レスポンスのシリアライズ
- OpenAPI スキーマ（/docs に出る仕様書）
を自動で作ってくれる。
"""

from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class ReviewType(str, Enum):
    """判定結果。str を継承すると JSON では "ai_only" のような文字列になる。"""

    AI_ONLY = "ai_only"
    HUMAN_REQUIRED = "human_required"


class ReviewGateRequest(BaseModel):
    pr_url: HttpUrl = Field(
        description="GitHub の Pull Request の URL",
        examples=["https://github.com/fastapi/fastapi/pull/1"],
    )


class PullRequestSummary(BaseModel):
    """判定に使った PR の情報。"""

    owner: str
    repo: str
    number: int
    title: str
    changed_files: int
    additions: int
    deletions: int
    files: list[str]


class ReviewGateResponse(BaseModel):
    review_type: ReviewType = Field(description="判定結果")
    reasons: list[str] = Field(description="その判定になった理由")
    pull_request: PullRequestSummary
