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

## 試した結果

実際に Jev で判定した結果（2026-10-05）。`probability` は実行ごとに多少ぶれる。
各サンプルは処理の流れの順に載せている。

1. **JSON**: Swagger UI の `POST /judge` → **Try it out** にそのまま貼れるボディ
2. **リクエスト**: Swagger UI が実際に送る curl
3. **Jev へのリクエスト**: この API が組み立てて Jev に送るもの（API キーは伏せている）
4. **Jev からのレスポンス**: Jev が返したそのまま（整形のみ）
5. **レスポンス**: この API が最終的に返すもの

### 1. 議事録（全項目 pass）

JSON:

```json
{
  "text": "【議事録】10/5 定例\n結論: 新ログイン画面は B 案で進める。\n担当: 山田さんがデザイン修正、佐藤さんが実装。\n期限: 10/20 までにステージング環境へ反映する。\n次回: 10/12 15:00〜",
  "checklist": [
    {"id": "has_conclusion", "description": "結論が明記されているか？"},
    {"id": "has_owner", "description": "担当者が明記されているか？"},
    {"id": "has_deadline", "description": "期限が明記されているか？"},
    {"id": "has_next_meeting", "description": "次回の予定が書かれているか？"}
  ]
}
```

リクエスト:

```sh
curl -X 'POST' \
  'http://localhost:8000/judge' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -d '{
  "text": "【議事録】10/5 定例\n結論: 新ログイン画面は B 案で進める。\n担当: 山田さんがデザイン修正、佐藤さんが実装。\n期限: 10/20 までにステージング環境へ反映する。\n次回: 10/12 15:00〜",
  "checklist": [
    {"id": "has_conclusion", "description": "結論が明記されているか？"},
    {"id": "has_owner", "description": "担当者が明記されているか？"},
    {"id": "has_deadline", "description": "期限が明記されているか？"},
    {"id": "has_next_meeting", "description": "次回の予定が書かれているか？"}
  ]
}'
```

Jev へのリクエスト:

```sh
curl -X 'POST' \
  'https://api.typesafe.ai/v1/systemone' \
  -H "Authorization: Bearer $JEV_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
  "state": "【議事録】10/5 定例\n結論: 新ログイン画面は B 案で進める。\n担当: 山田さんがデザイン修正、佐藤さんが実装。\n期限: 10/20 までにステージング環境へ反映する。\n次回: 10/12 15:00〜",
  "model": "jev-latest",
  "questions": {
    "has_conclusion": {
      "type": "noul",
      "instructions": "結論が明記されているか？"
    },
    "has_owner": {
      "type": "noul",
      "instructions": "担当者が明記されているか？"
    },
    "has_deadline": {
      "type": "noul",
      "instructions": "期限が明記されているか？"
    },
    "has_next_meeting": {
      "type": "noul",
      "instructions": "次回の予定が書かれているか？"
    }
  }
}'
```

Jev からのレスポンス:

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "has_conclusion": {
      "type": "noul",
      "noul": 0.99
    },
    "has_owner": {
      "type": "noul",
      "noul": 0.99
    },
    "has_deadline": {
      "type": "noul",
      "noul": 0.99
    },
    "has_next_meeting": {
      "type": "noul",
      "noul": 0.99
    }
  },
  "usage": {
    "input_tokens": 442,
    "output_tokens": 78
  }
}
```

レスポンス:

```json
{
  "passed": true,
  "judged_by": "jev",
  "results": [
    {
      "id": "has_conclusion",
      "passed": true,
      "probability": 0.99
    },
    {
      "id": "has_owner",
      "passed": true,
      "probability": 0.99
    },
    {
      "id": "has_deadline",
      "passed": true,
      "probability": 0.99
    },
    {
      "id": "has_next_meeting",
      "passed": true,
      "probability": 0.99
    }
  ]
}
```

### 2. 雑な PR 説明文（全項目 fail）

JSON:

```json
{
  "text": "ログイン処理を修正しました。いろいろ直したので見てください。",
  "checklist": [
    {"id": "has_purpose", "description": "変更の目的や背景が説明されているか？"},
    {"id": "has_change_detail", "description": "具体的に何を変更したかが書かれているか？"},
    {"id": "has_test", "description": "どのようにテストしたかが書かれているか？"},
    {"id": "has_impact", "description": "影響範囲やリスクについて触れられているか？"}
  ]
}
```

リクエスト:

```sh
curl -X 'POST' \
  'http://localhost:8000/judge' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -d '{
  "text": "ログイン処理を修正しました。いろいろ直したので見てください。",
  "checklist": [
    {"id": "has_purpose", "description": "変更の目的や背景が説明されているか？"},
    {"id": "has_change_detail", "description": "具体的に何を変更したかが書かれているか？"},
    {"id": "has_test", "description": "どのようにテストしたかが書かれているか？"},
    {"id": "has_impact", "description": "影響範囲やリスクについて触れられているか？"}
  ]
}'
```

Jev へのリクエスト:

```sh
curl -X 'POST' \
  'https://api.typesafe.ai/v1/systemone' \
  -H "Authorization: Bearer $JEV_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
  "state": "ログイン処理を修正しました。いろいろ直したので見てください。",
  "model": "jev-latest",
  "questions": {
    "has_purpose": {
      "type": "noul",
      "instructions": "変更の目的や背景が説明されているか？"
    },
    "has_change_detail": {
      "type": "noul",
      "instructions": "具体的に何を変更したかが書かれているか？"
    },
    "has_test": {
      "type": "noul",
      "instructions": "どのようにテストしたかが書かれているか？"
    },
    "has_impact": {
      "type": "noul",
      "instructions": "影響範囲やリスクについて触れられているか？"
    }
  }
}'
```

Jev からのレスポンス:

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "has_purpose": {
      "type": "noul",
      "noul": 0.37
    },
    "has_change_detail": {
      "type": "noul",
      "noul": 0.05
    },
    "has_test": {
      "type": "noul",
      "noul": 0.05
    },
    "has_impact": {
      "type": "noul",
      "noul": 0.07
    }
  },
  "usage": {
    "input_tokens": 397,
    "output_tokens": 76
  }
}
```

レスポンス:

```json
{
  "passed": false,
  "judged_by": "jev",
  "results": [
    {
      "id": "has_purpose",
      "passed": false,
      "probability": 0.37
    },
    {
      "id": "has_change_detail",
      "passed": false,
      "probability": 0.05
    },
    {
      "id": "has_test",
      "passed": false,
      "probability": 0.05
    },
    {
      "id": "has_impact",
      "passed": false,
      "probability": 0.07
    }
  ]
}
```

### 3. 障害報告（1 項目だけ fail）

JSON:

```json
{
  "text": "10/3 14:00〜14:40、決済 API がタイムアウトし一部ユーザーが購入できなかった。原因は DB の接続数上限に達したこと。接続プールの上限を 50→200 に引き上げて復旧した。再発防止として接続数の監視アラートを追加する予定。",
  "checklist": [
    {"id": "has_timeline", "description": "発生日時と期間が書かれているか？"},
    {"id": "has_impact", "description": "ユーザーへの影響が書かれているか？"},
    {"id": "has_root_cause", "description": "原因が特定されて書かれているか？"},
    {"id": "has_prevention", "description": "再発防止策が書かれているか？"},
    {"id": "has_apology", "description": "ユーザーへの謝罪が含まれているか？"}
  ]
}
```

リクエスト:

```sh
curl -X 'POST' \
  'http://localhost:8000/judge' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -d '{
  "text": "10/3 14:00〜14:40、決済 API がタイムアウトし一部ユーザーが購入できなかった。原因は DB の接続数上限に達したこと。接続プールの上限を 50→200 に引き上げて復旧した。再発防止として接続数の監視アラートを追加する予定。",
  "checklist": [
    {"id": "has_timeline", "description": "発生日時と期間が書かれているか？"},
    {"id": "has_impact", "description": "ユーザーへの影響が書かれているか？"},
    {"id": "has_root_cause", "description": "原因が特定されて書かれているか？"},
    {"id": "has_prevention", "description": "再発防止策が書かれているか？"},
    {"id": "has_apology", "description": "ユーザーへの謝罪が含まれているか？"}
  ]
}'
```

Jev へのリクエスト:

```sh
curl -X 'POST' \
  'https://api.typesafe.ai/v1/systemone' \
  -H "Authorization: Bearer $JEV_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
  "state": "10/3 14:00〜14:40、決済 API がタイムアウトし一部ユーザーが購入できなかった。原因は DB の接続数上限に達したこと。接続プールの上限を 50→200 に引き上げて復旧した。再発防止として接続数の監視アラートを追加する予定。",
  "model": "jev-latest",
  "questions": {
    "has_timeline": {
      "type": "noul",
      "instructions": "発生日時と期間が書かれているか？"
    },
    "has_impact": {
      "type": "noul",
      "instructions": "ユーザーへの影響が書かれているか？"
    },
    "has_root_cause": {
      "type": "noul",
      "instructions": "原因が特定されて書かれているか？"
    },
    "has_prevention": {
      "type": "noul",
      "instructions": "再発防止策が書かれているか？"
    },
    "has_apology": {
      "type": "noul",
      "instructions": "ユーザーへの謝罪が含まれているか？"
    }
  }
}'
```

Jev からのレスポンス:

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "has_impact": {
      "type": "noul",
      "noul": 0.97
    },
    "has_root_cause": {
      "type": "noul",
      "noul": 0.98
    },
    "has_prevention": {
      "type": "noul",
      "noul": 0.98
    },
    "has_apology": {
      "type": "noul",
      "noul": 0.04
    },
    "has_timeline": {
      "type": "noul",
      "noul": 0.98
    }
  },
  "usage": {
    "input_tokens": 490,
    "output_tokens": 96
  }
}
```

レスポンス:

```json
{
  "passed": false,
  "judged_by": "jev",
  "results": [
    {
      "id": "has_timeline",
      "passed": true,
      "probability": 0.98
    },
    {
      "id": "has_impact",
      "passed": true,
      "probability": 0.97
    },
    {
      "id": "has_root_cause",
      "passed": true,
      "probability": 0.98
    },
    {
      "id": "has_prevention",
      "passed": true,
      "probability": 0.98
    },
    {
      "id": "has_apology",
      "passed": false,
      "probability": 0.04
    }
  ]
}
```

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
