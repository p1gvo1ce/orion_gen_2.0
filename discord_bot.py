import discord
from discord.ext import commands
from utils.logger import get_logger, set_process

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

async def run_bot(token: str):
    log = get_logger(module="discord_bot")
    set_process("discord_bot")            # тот же event_id, новый процесс
    log.INFO("Starting bot...")
    await bot.start(token)
    log.INFO("Bot started")
