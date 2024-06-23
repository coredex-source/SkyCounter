import discord
from discord.ext import commands, tasks
from discord import Permissions
import csv
import os
import asyncio
from datetime import datetime, timedelta
import json
from cogs.ticket_system import Ticket_System
from cogs.ticket_commands import Ticket_Command
from cogs.countevent_system_commands import MainCog

#Initailizing ticket system files
with open("config.json", mode="r") as config_file:
    config = json.load(config_file)

TOKEN = config["token"]  #Your Bot Token

# Initialize bot with intents
intents = discord.Intents.all()
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

#Add ticket functions
bot.add_cog(Ticket_System(bot))
bot.add_cog(Ticket_Command(bot))
bot.add_cog(MainCog(bot))

#Load token from .env
#load_dotenv()
#TOKEN = os.getenv("TOKEN")
if __name__ == '__main__':
    bot.run(TOKEN)
