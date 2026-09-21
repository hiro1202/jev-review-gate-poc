"""AI のみのレビューで良いか、人間のレビューが必要かを判定するロジック。

外部通信をしない「純粋な関数」にしておくと、テストが書きやすい。
"""

from fnmatch import fnmatch

from app.config import Settings
from app.schemas import PullRequestSummary, ReviewType

# これらに当たるファイルが変更されていたら人間レビュー必須
# fnmatch 形式（* はスラッシュもまたぐ）
SENSITIVE_PATTERNS: dict[str, str] = {
    "*auth*": "認証・認可まわり",
    "*security*": "セキュリティ関連",
    "*secret*": "シークレット関連",
    "*migration*": "DB マイグレーション",
    "*.sql": "SQL",
    ".github/workflows/*": "CI/CD 設定",
    "*Dockerfile*": "コンテナ設定",
    "*.tf": "Terraform（インフラ）",
    "*payment*": "決済まわり",
}


def judge(pr: PullRequestSummary, settings: Settings) -> tuple[ReviewType, list[str]]:
    reasons: list[str] = []

    changed_lines = pr.additions + pr.deletions
    if changed_lines > settings.max_changed_lines:
        reasons.append(
            f"変更行数が多い ({changed_lines} 行 > {settings.max_changed_lines} 行)"
        )

    if pr.changed_files > settings.max_changed_files:
        reasons.append(
            f"変更ファイル数が多い ({pr.changed_files} > {settings.max_changed_files})"
        )

    for path in pr.files:
        for pattern, label in SENSITIVE_PATTERNS.items():
            if fnmatch(path.lower(), pattern.lower()):
                reasons.append(f"{label}のファイルを変更している: {path}")
                break  # 1ファイルにつき理由は1つで十分

    if reasons:
        return ReviewType.HUMAN_REQUIRED, reasons
    return ReviewType.AI_ONLY, ["小規模かつ重要領域に触れていないため AI レビューのみで可"]
