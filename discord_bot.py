import discord
from discord.ext import commands
from utils.logger import get_logger, set_process

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    log = get_logger(module="discord_bot")
    log.INFO(msg=f"✅ Bot connected as {bot.user} (id={bot.user.id})")

async def run_bot(token: str, event_id=None):
    log = get_logger(module="discord_bot")
    set_process("discord_bot")            # тот же event_id, новый процесс
    log.INFO(msg="Starting bot...", event_id=event_id)
    await bot.start(token)