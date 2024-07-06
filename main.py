import discord
from discord.ext import commands, tasks
from discord import Permissions
from colorama import Back, Fore, Style
import json
import sys
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

@bot.event
async def on_ready():
      print("\n-------------------------------------")
      print(Fore.WHITE + Style.BRIGHT + "Bot is ready!")
      print(Fore.LIGHTWHITE_EX + Style.BRIGHT + "Logged in as: " +
            Fore.LIGHTRED_EX + bot.user.name)
      print(Fore.LIGHTWHITE_EX + Style.BRIGHT + "ID: " + Fore.LIGHTRED_EX +
            str(bot.user.id))
      print(Fore.LIGHTWHITE_EX + Style.BRIGHT + "Python Version: " +
            Fore.LIGHTRED_EX + sys.version)
      print(Fore.LIGHTWHITE_EX + Style.BRIGHT + "Discord.py(pycord) Version: " +
            Fore.LIGHTRED_EX + discord.__version__)
      print(Fore.RESET + "-------------------------------------\n")

#Add ticket functions
bot.add_cog(Ticket_System(bot))
bot.add_cog(Ticket_Command(bot))
bot.add_cog(MainCog(bot))

#Load token from .env
#load_dotenv()
#TOKEN = os.getenv("TOKEN")
if __name__ == '__main__':
    bot.run(TOKEN)
