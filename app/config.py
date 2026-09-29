"""アプリの設定値。

pydantic-settings を使うと、環境変数（や .env ファイル）から
型付きで設定を読み込める。例: 環境変数 JEV_API_KEY -> Settings.jev_api_key
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Jev の設定。API KEY が未設定ならモックで判定する
    jev_api_key: str | None = None
    jev_api_base_url: str = "https://api.typesafe.ai"
    jev_model: str = "jev-latest"

    # Jev が返す yes の確率がこれ以上なら pass とみなす
    pass_threshold: float = 0.5


# lru_cache で1回だけ生成して使い回す（シングルトン的な使い方）
@lru_cache
def get_settings() -> Settings:
    return Settings()
