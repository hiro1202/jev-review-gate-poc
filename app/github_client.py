"""GitHub API から PR の情報を取ってくる部分（public リポジトリのみ対応）。"""

import re

import httpx

from app.config import Settings
from app.schemas import PullRequestSummary

# 例: https://github.com/owner/repo/pull/123
PR_URL_PATTERN = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$")


class InvalidPrUrlError(ValueError):
    pass


class GitHubApiError(RuntimeError):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """PR の URL を (owner, repo, number) に分解する。"""
    match = PR_URL_PATTERN.match(url)
    if match is None:
        raise InvalidPrUrlError(f"GitHub の PR URL として解釈できません: {url}")
    owner, repo, number = match.groups()
    return owner, repo, int(number)


async def fetch_pull_request(url: str, settings: Settings) -> PullRequestSummary:
    owner, repo, number = parse_pr_url(url)

    # 認証なしで呼ぶため public リポジトリのみ対象（レート制限: 60回/時/IP）
    headers = {"Accept": "application/vnd.github+json"}

    # async with を使うとブロックを抜けるときに接続を自動で閉じてくれる
    # リネーム・移管されたリポジトリは GitHub が 301 を返すので redirect を追う
    async with httpx.AsyncClient(
        base_url=settings.github_api_base_url,
        headers=headers,
        timeout=10.0,
        follow_redirects=True,
    ) as client:
        pr = await _get_json(client, f"/repos/{owner}/{repo}/pulls/{number}")
        # 変更ファイル一覧（最大100件。PoC なのでページングは省略）
        files = await _get_json(
            client,
            f"/repos/{owner}/{repo}/pulls/{number}/files",
            params={"per_page": 100},
        )

    return PullRequestSummary(
        owner=owner,
        repo=repo,
        number=number,
        title=pr["title"],
        changed_files=pr["changed_files"],
        additions=pr["additions"],
        deletions=pr["deletions"],
        files=_changed_paths(files),
    )


def _changed_paths(files: list[dict]) -> list[str]:
    """変更ファイルのパス一覧。リネームは旧パスも含める。

    旧パスを落とすと src/auth.py -> src/session.py のようなリネームで
    重要ファイルの判定をすり抜けてしまう。
    """
    paths: list[str] = []
    for f in files:
        paths.append(f["filename"])
        if f.get("previous_filename"):
            paths.append(f["previous_filename"])
    return paths


async def _get_json(client: httpx.AsyncClient, path: str, params: dict | None = None):
    try:
        response = await client.get(path, params=params)
    except httpx.HTTPError as e:
        # タイムアウトや接続失敗も上流エラーとして扱う（main で 502 になる）
        raise GitHubApiError(502, f"GitHub API に接続できません: {e!r}") from e
    if response.status_code != 200:
        raise GitHubApiError(
            response.status_code,
            f"GitHub API エラー ({response.status_code}): {response.text[:200]}",
        )
    return response.json()
