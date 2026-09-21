# jev-review-gate-poc

GitHub の PR URL を受け取り、**AI のみのレビューで良いか / 人間のレビューが必要か** を判定する API の PoC。

- フレームワーク: [FastAPI](https://fastapi.tiangolo.com/)
- OpenAPI 仕様は FastAPI が自動生成（`/docs`, `/openapi.json`）
- 対象は **public リポジトリの PR のみ**（GitHub API を認証なしで呼ぶため。レート制限は 60回/時）

## 起動（Docker）

```sh
cp .env.example .env   # Jev を使うときは JEV_API_KEY を設定
docker compose up --build
```

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

## 使い方

```sh
curl -X POST http://localhost:8000/review-gate \
  -H 'Content-Type: application/json' \
  -d '{"pr_url": "https://github.com/fastapi/fastapi/pull/1"}'
```

レスポンス例:

```json
{
  "review_type": "human_required",
  "reasons": ["変更行数が多い (512 行 > 300 行)"],
  "pull_request": { "owner": "fastapi", "repo": "fastapi", "number": 1, "...": "..." }
}
```

`review_type` は `ai_only` か `human_required`。

## 判定ロジック

1. `JEV_API_KEY` が設定されていれば Jev で判定（**未実装のスタブ**。`app/jev_client.py` を参照）
2. 使えなければ以下のルールで判定（`app/judge.py`）。1つでも該当すれば `human_required`
   - 変更行数（追加 + 削除）が `MAX_CHANGED_LINES`（既定 300）を超える
   - 変更ファイル数が `MAX_CHANGED_FILES`（既定 15）を超える
   - 認証・マイグレーション・CI 設定・Dockerfile・Terraform などの重要ファイルを変更している

## Jev をつなぐとき

1. `.env` に `JEV_API_KEY` と `JEV_API_BASE_URL` を設定
2. `app/jev_client.py` の `judge_with_jev` を Jev の API 仕様に合わせて実装

## ローカル開発（Docker なし）

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
pytest
```

## 構成

```
app/
  main.py          # FastAPI アプリとエンドポイント
  schemas.py       # リクエスト/レスポンスの型（Pydantic）
  config.py        # 環境変数からの設定読み込み
  github_client.py # GitHub API から PR 情報を取得
  judge.py         # ルールベースの判定ロジック
  jev_client.py    # Jev 連携（スタブ）
tests/
```
