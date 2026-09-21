import pytest

from app.config import Settings
from app.github_client import InvalidPrUrlError, _changed_paths, parse_pr_url
from app.judge import judge
from app.schemas import PullRequestSummary, ReviewType

SETTINGS = Settings(max_changed_lines=300, max_changed_files=15)


def make_pr(**overrides) -> PullRequestSummary:
    """テスト用の PR を作るヘルパー。必要な項目だけ上書きする。"""
    data = dict(
        owner="o",
        repo="r",
        number=1,
        title="t",
        changed_files=1,
        additions=10,
        deletions=5,
        files=["src/utils.py"],
    )
    data.update(overrides)
    return PullRequestSummary(**data)


def test_small_pr_is_ai_only():
    review_type, _ = judge(make_pr(), SETTINGS)
    assert review_type == ReviewType.AI_ONLY


def test_large_pr_requires_human():
    review_type, reasons = judge(make_pr(additions=400), SETTINGS)
    assert review_type == ReviewType.HUMAN_REQUIRED
    assert "変更行数" in reasons[0]


def test_many_files_requires_human():
    review_type, _ = judge(make_pr(changed_files=20), SETTINGS)
    assert review_type == ReviewType.HUMAN_REQUIRED


# parametrize で同じテストを複数の入力で回せる
@pytest.mark.parametrize(
    "path",
    [
        "src/auth/login.py",
        "db/migrations/0001_init.py",
        ".github/workflows/ci.yml",
        "infra/main.tf",
        "Dockerfile",
    ],
)
def test_sensitive_files_require_human(path):
    review_type, _ = judge(make_pr(files=[path]), SETTINGS)
    assert review_type == ReviewType.HUMAN_REQUIRED


def test_parse_pr_url():
    assert parse_pr_url("https://github.com/fastapi/fastapi/pull/123") == (
        "fastapi",
        "fastapi",
        123,
    )


def test_parse_pr_url_invalid():
    with pytest.raises(InvalidPrUrlError):
        parse_pr_url("https://github.com/fastapi/fastapi/issues/123")


def test_renamed_sensitive_file_requires_human():
    # src/auth.py を src/session.py にリネームしても重要ファイル判定をすり抜けない
    files = _changed_paths([{"filename": "src/session.py", "previous_filename": "src/auth.py"}])
    review_type, _ = judge(make_pr(files=files), SETTINGS)
    assert review_type == ReviewType.HUMAN_REQUIRED
