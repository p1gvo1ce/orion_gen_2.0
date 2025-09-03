import os
import csv
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands


intents = discord.Intents.all()
intents.message_content = True
intents.guild_messages = True
intents.dm_messages = False
bot = commands.Bot(command_prefix='!', intents=intents)

def get_bot():
    return bot

async def run_bot(token):
    await bot.start(token)