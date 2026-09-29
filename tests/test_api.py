import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from app import jev_client
from app.config import Settings, get_settings
from app.main import app
from app.schemas import CheckItem

# TestClient を使うと、サーバーを起動せずに API を呼び出せる
client = TestClient(app)

BODY = {
    "text": "本日の会議の結論は A 案で進めることです。",
    "checklist": [
        {"id": "has_conclusion", "description": "結論が明記されているか？"},
        {"id": "has_deadline", "description": "期限が明記されているか？"},
    ],
}


def use_settings(settings: Settings) -> None:
    """get_settings の代わりに、テスト用の設定を使うようにする。"""
    app.dependency_overrides[get_settings] = lambda: settings


def teardown_function():
    # 各テストの後に差し替えを元に戻す
    app.dependency_overrides.clear()


def test_mock_judge_when_jev_not_configured():
    use_settings(Settings(jev_api_key=None))
    response = client.post("/judge", json=BODY)

    assert response.status_code == 200
    data = response.json()
    assert data["judged_by"] == "mock"
    assert data["passed"] is True
    assert [r["id"] for r in data["results"]] == ["has_conclusion", "has_deadline"]


def test_judge_with_jev_uses_threshold(monkeypatch):
    # monkeypatch で Jev の呼び出しを差し替え、実際の通信をしないようにする
    async def fake_judge(text, checklist, settings):
        return {"has_conclusion": 0.92, "has_deadline": 0.1}

    monkeypatch.setattr(jev_client, "judge", fake_judge)
    use_settings(Settings(jev_api_key="dummy", pass_threshold=0.5))
    data = client.post("/judge", json=BODY).json()

    assert data["judged_by"] == "jev"
    assert data["passed"] is False
    assert data["results"] == [
        {"id": "has_conclusion", "passed": True, "probability": 0.92},
        {"id": "has_deadline", "passed": False, "probability": 0.1},
    ]


def test_returns_502_when_jev_fails(monkeypatch):
    async def failing_judge(text, checklist, settings):
        raise jev_client.JevError("Jev API エラー (529)")

    monkeypatch.setattr(jev_client, "judge", failing_judge)
    use_settings(Settings(jev_api_key="dummy"))
    response = client.post("/judge", json=BODY)

    assert response.status_code == 502


def test_malformed_jev_response_raises_jev_error(monkeypatch):
    # 200 だが answers に項目がないレスポンスを返すようにする
    async def fake_post(self, url, **kwargs):
        return httpx.Response(200, json={"answers": {}})

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    checklist = [CheckItem(id="c1", description="問い")]

    with pytest.raises(jev_client.JevError):
        asyncio.run(jev_client.judge("テキスト", checklist, Settings(jev_api_key="dummy")))


def test_build_body_follows_jev_spec():
    checklist = [CheckItem(id="has_conclusion", description="結論が明記されているか？")]
    body = jev_client.build_body("テキスト", checklist, "jev-latest")

    assert body == {
        "state": "テキスト",
        "model": "jev-latest",
        "questions": {
            "has_conclusion": {"type": "noul", "instructions": "結論が明記されているか？"},
        },
    }


def test_empty_checklist_is_rejected():
    response = client.post("/judge", json={"text": "テキスト", "checklist": []})
    assert response.status_code == 422


def test_duplicate_ids_are_rejected():
    item = {"id": "c1", "description": "問い"}
    response = client.post("/judge", json={"text": "テキスト", "checklist": [item, item]})
    assert response.status_code == 422
