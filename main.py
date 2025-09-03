import asyncio

from pydantic_settings import BaseSettings

from discord_bot import run_bot


class Settings(BaseSettings):
    discord_token: str

    class Config:
        env_file = ".env"

settings = Settings()

async def main():

    await run_bot(settings.discord_token)


if __name__ == '__main__':
    asyncio.run(main())