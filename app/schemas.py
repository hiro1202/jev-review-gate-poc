"""API の入出力の型定義（Pydantic モデル）。

FastAPI はここで定義したモデルから
- リクエストのバリデーション
- レスポンスのシリアライズ
- OpenAPI スキーマ（/docs に出る仕様書）
を自動で作ってくれる。
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CheckItem(BaseModel):
    id: str = Field(min_length=1, description="チェック項目の ID", examples=["has_conclusion"])
    description: str = Field(
        min_length=1,
        description="チェック内容（yes/no で答えられる問いにする）",
        examples=["結論が明記されているか？"],
    )


class JudgeRequest(BaseModel):
    # min_length=1 で空文字・空リストを 422 エラーにできる
    text: str = Field(min_length=1, description="判定対象のテキスト")
    checklist: list[CheckItem] = Field(min_length=1, description="チェック項目の一覧")

    # field_validator で独自のチェックを足せる（ここで例外を投げると 422 になる）
    @field_validator("checklist")
    @classmethod
    def ids_must_be_unique(cls, checklist: list[CheckItem]) -> list[CheckItem]:
        ids = [item.id for item in checklist]
        if len(ids) != len(set(ids)):
            raise ValueError("チェック項目の id が重複しています")
        return checklist


class CheckResult(BaseModel):
    id: str = Field(description="チェック項目の ID")
    passed: bool = Field(description="probability がしきい値以上なら true")
    probability: float = Field(description="Jev が返した yes の確率（0〜1）")


class JudgeResponse(BaseModel):
    passed: bool = Field(description="全項目が pass なら true")
    # Literal を使うと、決まった値しか入らないことを型で表せる
    judged_by: Literal["jev", "mock"] = Field(description="判定に使ったもの")
    results: list[CheckResult]
