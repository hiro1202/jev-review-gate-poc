"""アプリの設定値。

pydantic-settings を使うと、環境変数（や .env ファイル）から
型付きで設定を読み込める。例: 環境変数 JEV_API_KEY -> Settings.jev_api_key
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    github_api_base_url: str = "https://api.github.com"

    # Jev の設定。API KEY が未設定ならルールベース判定だけで動く
    jev_api_key: str | None = None
    jev_api_base_url: str | None = None

    # --- 判定ルールのしきい値（環境変数で上書き可能） ---
    # 変更行数（追加 + 削除）がこれを超えたら人間レビュー
    max_changed_lines: int = 300
    # 変更ファイル数がこれを超えたら人間レビュー
    max_changed_files: int = 15


# lru_cache で1回だけ生成して使い回す（シングルトン的な使い方）
@lru_cache
def get_settings() -> Settings:
    return Settings()
