# jev-review-gate-poc

テキストとチェック項目を受け取り、[Jev](https://docs.typesafe.ai/api)（TypeSafe AI）で **項目ごとに判定する** API の PoC。

- フレームワーク: [FastAPI](https://fastapi.tiangolo.com/)
- OpenAPI 仕様は FastAPI が自動生成（`/docs`, `/openapi.json`）
- `JEV_API_KEY` が未設定なら **モック** で判定する（全項目 pass）

## 起動（Docker）

```sh
cp .env.example .env   # Jev を使うときは JEV_API_KEY を設定
docker compose up --build
```

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

## 使い方

```sh
curl -X POST http://localhost:8000/judge \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "本日の会議の結論は A 案で進めることです。",
    "checklist": [
      {"id": "has_conclusion", "description": "結論が明記されているか？"},
      {"id": "has_deadline", "description": "期限が明記されているか？"}
    ]
  }'
```

レスポンス例:

```json
{
  "passed": false,
  "judged_by": "jev",
  "results": [
    {"id": "has_conclusion", "passed": true, "probability": 0.92},
    {"id": "has_deadline", "passed": false, "probability": 0.1}
  ]
}
```

- `probability`: Jev が返した「yes」の確率（0〜1）
- `passed`（項目）: `probability` が `PASS_THRESHOLD`（既定 0.5）以上なら `true`
- `passed`（全体）: 全項目が `true` なら `true`
- `judged_by`: `jev` か `mock`

チェック項目の `description` は **yes/no で答えられる問い** にする（「〜か？」の形）。
`id` はリクエスト内で重複不可。

## Jev との対応

[Jev API](https://docs.typesafe.ai/api) の `POST /v1/systemone` を呼ぶ。

| この API | Jev |
|---|---|
| `text` | `state` |
| チェック項目 1 つ | `noul` 型の質問 1 つ（`id` が質問 ID、`description` が `instructions`） |
| `probability` | `answers[id].noul` |

Jev は判定理由のテキストは返さず、確率だけを返す。

## ローカルで起動（Docker なし）

Python 3.12 を想定。

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # Jev を使うときは JEV_API_KEY を設定
uvicorn app.main:app --reload
```

起動後は Docker のときと同じく http://localhost:8000/docs で確認できる。

テスト:

```sh
pytest
```

## 構成

```
app/
  main.py        # FastAPI アプリとエンドポイント
  schemas.py     # リクエスト/レスポンスの型（Pydantic）
  config.py      # 環境変数からの設定読み込み
  jev_client.py  # Jev の呼び出しとモック
tests/
  test_api.py
```
