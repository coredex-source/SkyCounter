import discord
import asyncio
import pytz
import json
import sqlite3
from datetime import datetime
import chat_exporter
import io
from discord.ext import commands

#This will get everything from the config.json file
with open("config.json", mode="r") as config_file:
    config = json.load(config_file)

GUILD_ID = config["guild_id"]
SUPPORT_CHANNEL = config["support_channel_id"]
LOAN_CHANNEL = config["loan_channel_id"]
APPLICATION_CHANNEL = config["application_channel_id"]
CATEGORY_ID1 = config["category_id_1"] #Support
CATEGORY_ID2 = config["category_id_2"] #Loan
CATEGORY_ID3 = config["category_id_3"] #Applications
TEAM_ROLE1 = config["team_role_id_1"] #Support
TEAM_ROLE2 = config["team_role_id_2"] #Loans
TEAM_ROLE3 = config["team_role_id_3"] #Applications
TEAM_ROLE4 = config["team_role_id_4"] 
LOG_CHANNEL = config["log_channel_id"]
TIMEZONE = config["timezone"]
SUPPORT_TITLE = config["support_title"]
APPLICATION_TITLE = config["application_title"]
LOAN_TITLE = config["loan_title"]
EMBED_DESCRIPTION = config["embed_description"]
PING_ROLE1 = config["ping_role_1"]

#This will create and connect to the database
conn = sqlite3.connect('Database.db')
cur = conn.cursor()

#Create the table if it doesn't exist
cur.execute("""CREATE TABLE IF NOT EXISTS ticket 
           (id INTEGER PRIMARY KEY AUTOINCREMENT, discord_name TEXT, discord_id INTEGER, ticket_channel TEXT, ticket_created TIMESTAMP)""")
conn.commit()

class Ticket_System(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Bot Loaded  | ticket_system.py ')
        self.bot.add_view(SupportView(bot=self.bot))
        self.bot.add_view(LoanView(bot=self.bot))
        self.bot.add_view(ApplicationView(bot=self.bot))
        self.bot.add_view(TicketOptions(bot=self.bot))

    #Closes the Connection to the Database when shutting down the Bot
    @commands.Cog.listener()
    async def on_bot_shutdown():
        cur.close()
        conn.close()

##Support & Loan Ticket Handling

class SupportView(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.select(
        custom_id="support",
        placeholder="Choose a Ticket option",
        options=[
            discord.SelectOption(
                label="General Support",  #Name of the 1 Select Menu Option
                description="You will get help here!",  #Description of the 1 Select Menu Option
                emoji="🎟️",
                value="support1"   #Don't change this value otherwise the code will not work anymore!!!!
            ),
            discord.SelectOption(
                label="Giveaway Claim",  #Name of the 2 Select Menu Option
                description="Claim those wins!", #Description of the 2 Select Menu Option
                emoji="🎉",
                value="support2"   #Don't change this value otherwise the code will not work anymore!!!!
            ),
            discord.SelectOption(
                label="Partner Ticket",  #Name of the 2 Select Menu Option
                description="Want to partner ?", #Description of the 2 Select Menu Option
                emoji="🤝",
                value="support3"   #Don't change this value otherwise the code will not work anymore!!!!
            ),
            discord.SelectOption(
                label="Reports",  #Name of the 2 Select Menu Option
                description="Found any issue or any abuse, use this to send all kinds of reports.", #Description of the 2 Select Menu Option
                emoji="⁉️",
                value="support4"   #Don't change this value otherwise the code will not work anymore!!!!
            )
        ]
    )
    async def callback(self, select, interaction):
        await interaction.response.defer()
        timezone = pytz.timezone(TIMEZONE)
        creation_date = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
        user_name = interaction.user.name
        user_id = interaction.user.id

        cur.execute("SELECT discord_id FROM ticket WHERE discord_id=?", (user_id,)) #Check if the User already has a Ticket open
        existing_ticket = cur.fetchone()

        if existing_ticket is None:
            if "support1" in interaction.data['values']:
                if interaction.channel.id == SUPPORT_CHANNEL:
                    guild = self.bot.get_guild(GUILD_ID)

                    cur.execute("INSERT INTO ticket (discord_name, discord_id, ticket_created) VALUES (?, ?, ?)", (user_name, user_id, creation_date)) #If the User doesn't have a Ticket open it will insert the User into the Database and create a Ticket
                    conn.commit()
                    await asyncio.sleep(1)
                    cur.execute("SELECT id FROM ticket WHERE discord_id=?", (user_id,)) #Get the Ticket Number from the Database
                    ticket_number = cur.fetchone()[0]

                    category = self.bot.get_channel(CATEGORY_ID1)
                    ticket_channel = await guild.create_text_channel(f"support-{ticket_number}", category=category,
                                                                        topic=f"{interaction.user.id}")

                    await ticket_channel.set_permissions(guild.get_role(TEAM_ROLE1), send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the Staff Team
                                                            embed_links=True, attach_files=True, read_message_history=True,
                                                            external_emojis=True)
                    await ticket_channel.set_permissions(interaction.user, send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the User
                                                            embed_links=True, attach_files=True, read_message_history=True,
                                                            external_emojis=True)
                    await ticket_channel.set_permissions(guild.default_role, send_messages=False, read_messages=False, view_channel=False) #Set the Permissions for the @everyone role
                    embed = discord.Embed(description=f'Welcome {interaction.user.mention},\n'
                                                        'describe your Problem and our Support will help you soon.',   #Ticket Welcome message
                                                        color=discord.colour.Color.blue())
                    await ticket_channel.send(embed=embed, view=SupportMainButton(bot=self.bot))
                    
                    channel_id = ticket_channel.id
                    cur.execute("UPDATE ticket SET ticket_channel = ? WHERE id = ?", (channel_id, ticket_number))
                    conn.commit()

                    embed = discord.Embed(description=f'📬 Ticket was Created! Look here --> {ticket_channel.mention}',  
                                                color=discord.colour.Color.green())
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    await asyncio.sleep(1)
                    embed = discord.Embed(title=SUPPORT_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
                    await interaction.message.edit(embed=embed, view=SupportView(bot=self.bot)) #This will reset the SelectMenu in the Ticket Channel

            if "support2" in interaction.data['values']:
                if interaction.channel.id == SUPPORT_CHANNEL:
                    guild = self.bot.get_guild(GUILD_ID)

                    cur.execute("INSERT INTO ticket (discord_name, discord_id, ticket_created) VALUES (?, ?, ?)", (user_name, user_id, creation_date)) #If the User doesn't have a Ticket open it will insert the User into the Database and create a Ticket
                    conn.commit()
                    await asyncio.sleep(1)
                    cur.execute("SELECT id FROM ticket WHERE discord_id=?", (user_id,)) #Get the Ticket Number from the Database
                    ticket_number = cur.fetchone()[0]

                    category = self.bot.get_channel(CATEGORY_ID1)
                    ticket_channel = await guild.create_text_channel(f"claim-{ticket_number}", category=category,
                                                                    topic=f"{interaction.user.id}")

                    await ticket_channel.set_permissions(guild.get_role(TEAM_ROLE2), send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the Staff Team
                                                        embed_links=True, attach_files=True, read_message_history=True,
                                                        external_emojis=True)
                    await ticket_channel.set_permissions(interaction.user, send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the User
                                                        embed_links=True, attach_files=True, read_message_history=True,
                                                        external_emojis=True)
                    
                    await ticket_channel.set_permissions(guild.default_role, send_messages=False, read_messages=False, view_channel=False) #Set the Permissions for the @everyone role
                    embed = discord.Embed(description=f'Welcome {interaction.user.mention},\n' #Ticket Welcome message
                                                       'Please mention the giveaway you won and ping the host.',
                                                    color=discord.colour.Color.blue())
                    await ticket_channel.send(embed=embed, view=SupportMainButton(bot=self.bot))

                    channel_id = ticket_channel.id
                    cur.execute("UPDATE ticket SET ticket_channel = ? WHERE id = ?", (channel_id, ticket_number))
                    conn.commit()

                    embed = discord.Embed(description=f'📬 Ticket was Created! Look here --> {ticket_channel.mention}',
                                            color=discord.colour.Color.green())
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    await asyncio.sleep(1)
                    embed = discord.Embed(title=SUPPORT_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
                    await interaction.message.edit(embed=embed, view=SupportView(bot=self.bot)) #This will reset the SelectMenu in the Ticket Channel
            if "support3" in interaction.data['values']:
                if interaction.channel.id == SUPPORT_CHANNEL:
                    guild = self.bot.get_guild(GUILD_ID)

                    cur.execute("INSERT INTO ticket (discord_name, discord_id, ticket_created) VALUES (?, ?, ?)", (user_name, user_id, creation_date)) #If the User doesn't have a Ticket open it will insert the User into the Database and create a Ticket
                    conn.commit()
                    await asyncio.sleep(1)
                    cur.execute("SELECT id FROM ticket WHERE discord_id=?", (user_id,)) #Get the Ticket Number from the Database
                    ticket_number = cur.fetchone()[0]

                    category = self.bot.get_channel(CATEGORY_ID1)
                    ticket_channel = await guild.create_text_channel(f"partner-{ticket_number}", category=category,
                                                                    topic=f"{interaction.user.id}")

                    await ticket_channel.set_permissions(guild.get_role(TEAM_ROLE3), send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the Staff Team
                                                        embed_links=True, attach_files=True, read_message_history=True,
                                                        external_emojis=True)
                    await ticket_channel.set_permissions(interaction.user, send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the User
                                                        embed_links=True, attach_files=True, read_message_history=True,
                                                        external_emojis=True)
                    
                    await ticket_channel.set_permissions(guild.default_role, send_messages=False, read_messages=False, view_channel=False) #Set the Permissions for the @everyone role
                    embed = discord.Embed(description=f'Welcome {interaction.user.mention},\n' #Ticket Welcome message
                                                       'A '+PING_ROLE1+' will be with you soon',
                                                    color=discord.colour.Color.blue())
                    await ticket_channel.send(embed=embed, view=SupportMainButton(bot=self.bot))

                    channel_id = ticket_channel.id
                    cur.execute("UPDATE ticket SET ticket_channel = ? WHERE id = ?", (channel_id, ticket_number))
                    conn.commit()

                    embed = discord.Embed(description=f'📬 Ticket was Created! Look here --> {ticket_channel.mention}',
                                            color=discord.colour.Color.green())
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    await asyncio.sleep(1)
                    embed = discord.Embed(title=SUPPORT_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
                    await interaction.message.edit(embed=embed, view=SupportView(bot=self.bot)) #This will reset the SelectMenu in the Ticket Channel
            if "support4" in interaction.data['values']:
                if interaction.channel.id == SUPPORT_CHANNEL:
                    guild = self.bot.get_guild(GUILD_ID)

                    cur.execute("INSERT INTO ticket (discord_name, discord_id, ticket_created) VALUES (?, ?, ?)", (user_name, user_id, creation_date)) #If the User doesn't have a Ticket open it will insert the User into the Database and create a Ticket
                    conn.commit()
                    await asyncio.sleep(1)
                    cur.execute("SELECT id FROM ticket WHERE discord_id=?", (user_id,)) #Get the Ticket Number from the Database
                    ticket_number = cur.fetchone()[0]

                    category = self.bot.get_channel(CATEGORY_ID1)
                    ticket_channel = await guild.create_text_channel(f"report-{ticket_number}", category=category,
                                                                    topic=f"{interaction.user.id}")

                    await ticket_channel.set_permissions(guild.get_role(TEAM_ROLE4), send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the Staff Team
                                                        embed_links=True, attach_files=True, read_message_history=True,
                                                        external_emojis=True)
                    await ticket_channel.set_permissions(interaction.user, send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the User
                                                        embed_links=True, attach_files=True, read_message_history=True,
                                                        external_emojis=True)
                    
                    await ticket_channel.set_permissions(guild.default_role, send_messages=False, read_messages=False, view_channel=False) #Set the Permissions for the @everyone role
                    embed = discord.Embed(description=f'Welcome {interaction.user.mention},\n' #Ticket Welcome message
                                                       'Someone from the staff team will be here soon, please describe your issue.',
                                                    color=discord.colour.Color.blue())
                    await ticket_channel.send(embed=embed, view=SupportMainButton(bot=self.bot))

                    channel_id = ticket_channel.id
                    cur.execute("UPDATE ticket SET ticket_channel = ? WHERE id = ?", (channel_id, ticket_number))
                    conn.commit()

                    embed = discord.Embed(description=f'📬 Ticket was Created! Look here --> {ticket_channel.mention}',
                                            color=discord.colour.Color.green())
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    await asyncio.sleep(1)
                    embed = discord.Embed(title=SUPPORT_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
                    await interaction.message.edit(embed=embed, view=SupportView(bot=self.bot)) #This will reset the SelectMenu in the Ticket Channel
        else:
            embed = discord.Embed(title=f"You already have a open Ticket", color=0xff0000)
            await interaction.followup.send(embed=embed, ephemeral=True) #This will tell the User that he already has a Ticket open
            await asyncio.sleep(1)
            embed = discord.Embed(title=SUPPORT_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
            await interaction.message.edit(embed=embed, view=SupportView(bot=self.bot)) #This will reset the SelectMenu in the Ticket Channel
             
class SupportModal(discord.ui.Modal):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="IGN:"))
        self.add_item(
            discord.ui.InputText(label="Describe the required support:",
                                 style=discord.InputTextStyle.long))

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Ticket Information:")
        embed.add_field(name="IGN:", value=self.children[0].value)
        embed.add_field(name="Support Description:",
                        value=self.children[1].value)
        await interaction.response.send_message(embeds=[embed])


class SupportMainButton(discord.ui.View):

    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label="Enter Information")
    async def button_callback(self, button: discord.ui.Button,
                              interaction: discord.Interaction):
        await interaction.response.send_modal(
            SupportModal(title="Enter Information"))

    @discord.ui.button(label="Delete Ticket 🎫",
                       style=discord.ButtonStyle.blurple,
                       custom_id="close")
    async def close(self, button: discord.ui.Button,
                    interaction: discord.Interaction):
        embed = discord.Embed(
            title="Delete Ticket 🎫",
            description="Are you sure you want to delete this Ticket?",
            color=discord.colour.Color.green())
        await interaction.response.send_message(
            embed=embed, view=TicketOptions(bot=self.bot)
        )  #This will show the User the TicketOptions View
        await interaction.message.edit(view=self)

##Loan Ticket Handling

class LoanView(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.select(
        custom_id="loan",
        placeholder="Choose a Ticket option",
        options=[
            discord.SelectOption(
                label="Get Loan",  #Name of the 1 Select Menu Option
                description="You can apply for a loan here!",  #Description of the 1 Select Menu Option
                emoji="💳",
                value="loan1"   #Don't change this value otherwise the code will not work anymore!!!!
            ),
            discord.SelectOption(
                label="Repay Loan",  #Name of the 2 Select Menu Option
                description="You can re-pay the taken loan here!", #Description of the 2 Select Menu Option
                emoji="💴",
                value="loan2"   #Don't change this value otherwise the code will not work anymore!!!!
            )
        ]
    )
    async def callback(self, select, interaction):
        await interaction.response.defer()
        timezone = pytz.timezone(TIMEZONE)
        creation_date = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
        user_name = interaction.user.name
        user_id = interaction.user.id

        cur.execute("SELECT discord_id FROM ticket WHERE discord_id=?", (user_id,)) #Check if the User already has a Ticket open
        existing_ticket = cur.fetchone()

        if existing_ticket is None:
            if "loan1" in interaction.data['values']:
                if interaction.channel.id == LOAN_CHANNEL:
                    guild = self.bot.get_guild(GUILD_ID)

                    cur.execute("INSERT INTO ticket (discord_name, discord_id, ticket_created) VALUES (?, ?, ?)", (user_name, user_id, creation_date)) #If the User doesn't have a Ticket open it will insert the User into the Database and create a Ticket
                    conn.commit()
                    await asyncio.sleep(1)
                    cur.execute("SELECT id FROM ticket WHERE discord_id=?", (user_id,)) #Get the Ticket Number from the Database
                    ticket_number = cur.fetchone()[0]

                    category = self.bot.get_channel(CATEGORY_ID2)
                    ticket_channel = await guild.create_text_channel(f"getloan-{ticket_number}", category=category,
                                                                        topic=f"{interaction.user.id}")

                    await ticket_channel.set_permissions(guild.get_role(TEAM_ROLE2), send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the Staff Team
                                                            embed_links=True, attach_files=True, read_message_history=True,
                                                            external_emojis=True)
                    await ticket_channel.set_permissions(interaction.user, send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the User
                                                            embed_links=True, attach_files=True, read_message_history=True,
                                                            external_emojis=True)
                    await ticket_channel.set_permissions(guild.default_role, send_messages=False, read_messages=False, view_channel=False) #Set the Permissions for the @everyone role
                    embed = discord.Embed(description=f'Welcome {interaction.user.mention},\n'
                                                        'a banker will be with you soon.',   #Ticket Welcome message
                                                        color=discord.colour.Color.blue())
                    await ticket_channel.send(embed=embed, view=LoanMainButton(bot=self.bot))
                    
                    channel_id = ticket_channel.id
                    cur.execute("UPDATE ticket SET ticket_channel = ? WHERE id = ?", (channel_id, ticket_number))
                    conn.commit()

                    embed = discord.Embed(description=f'📬 Ticket was Created! Look here --> {ticket_channel.mention}',  
                                                color=discord.colour.Color.green())
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    await asyncio.sleep(1)
                    embed = discord.Embed(title=LOAN_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
                    await interaction.message.edit(embed=embed, view=LoanView(bot=self.bot)) #This will reset the SelectMenu in the Ticket Channel

            if "loan2" in interaction.data['values']:
                if interaction.channel.id == LOAN_CHANNEL:
                    guild = self.bot.get_guild(GUILD_ID)

                    cur.execute("INSERT INTO ticket (discord_name, discord_id, ticket_created) VALUES (?, ?, ?)", (user_name, user_id, creation_date)) #If the User doesn't have a Ticket open it will insert the User into the Database and create a Ticket
                    conn.commit()
                    await asyncio.sleep(1)
                    cur.execute("SELECT id FROM ticket WHERE discord_id=?", (user_id,)) #Get the Ticket Number from the Database
                    ticket_number = cur.fetchone()[0]

                    category = self.bot.get_channel(CATEGORY_ID2)
                    ticket_channel = await guild.create_text_channel(f"payloan-{ticket_number}", category=category,
                                                                    topic=f"{interaction.user.id}")

                    await ticket_channel.set_permissions(guild.get_role(TEAM_ROLE2), send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the Staff Team
                                                        embed_links=True, attach_files=True, read_message_history=True,
                                                        external_emojis=True)
                    await ticket_channel.set_permissions(interaction.user, send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the User
                                                        embed_links=True, attach_files=True, read_message_history=True,
                                                        external_emojis=True)
                    
                    await ticket_channel.set_permissions(guild.default_role, send_messages=False, read_messages=False, view_channel=False) #Set the Permissions for the @everyone role
                    embed = discord.Embed(description=f'Welcome {interaction.user.mention},\n' #Ticket Welcome message
                                                       'a banker will be with you soon.',
                                                    color=discord.colour.Color.blue())
                    await ticket_channel.send(embed=embed, view=LoanMainButton(bot=self.bot))

                    channel_id = ticket_channel.id
                    cur.execute("UPDATE ticket SET ticket_channel = ? WHERE id = ?", (channel_id, ticket_number))
                    conn.commit()

                    embed = discord.Embed(description=f'📬 Ticket was Created! Look here --> {ticket_channel.mention}',
                                            color=discord.colour.Color.green())
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    await asyncio.sleep(1)
                    embed = discord.Embed(title=LOAN_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
                    await interaction.message.edit(embed=embed, view=LoanView(bot=self.bot)) #This will reset the SelectMenu in the Ticket Channel
        else:
            embed = discord.Embed(title=f"You already have a open Ticket", color=0xff0000)
            await interaction.followup.send(embed=embed, ephemeral=True) #This will tell the User that he already has a Ticket open
            await asyncio.sleep(1)
            embed = discord.Embed(title=LOAN_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
            await interaction.message.edit(embed=embed, view=LoanView(bot=self.bot)) #This will reset the SelectMenu in the Ticket Channel
             
class LoanModal(discord.ui.Modal):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="IGN:"))
        self.add_item(
            discord.ui.InputText(label="Describe the required support:",
                                 style=discord.InputTextStyle.long))

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Ticket Information:")
        embed.add_field(name="IGN:", value=self.children[0].value)
        embed.add_field(name="Support Description:",
                        value=self.children[1].value)
        await interaction.response.send_message(embeds=[embed])


class LoanMainButton(discord.ui.View):

    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label="Enter Information")
    async def button_callback(self, button: discord.ui.Button,
                              interaction: discord.Interaction):
        await interaction.response.send_modal(
            LoanModal(title="Enter Information"))

    @discord.ui.button(label="Delete Ticket 🎫",
                       style=discord.ButtonStyle.blurple,
                       custom_id="close")
    async def close(self, button: discord.ui.Button,
                    interaction: discord.Interaction):
        embed = discord.Embed(
            title="Delete Ticket 🎫",
            description="Are you sure you want to delete this Ticket?",
            color=discord.colour.Color.green())
        await interaction.response.send_message(
            embed=embed, view=TicketOptions(bot=self.bot)
        )  #This will show the User the TicketOptions View
        await interaction.message.edit(view=self)

##Application Ticket Handling

class ApplicationView(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.select(
        custom_id="application",
        placeholder="Choose a Ticket option",
        options=[
            discord.SelectOption(
                label="Staff Application",  #Name of the 1 Select Menu Option
                description="Apply for a staff position here.",  #Description of the 1 Select Menu Option
                emoji="🚨",
                value="application1"   #Don't change this value otherwise the code will not work anymore!!!!
            ),
            discord.SelectOption(
                label="Carrier Application",  #Name of the 2 Select Menu Option
                description="Apply for a carrier position here.", #Description of the 2 Select Menu Option
                emoji="👮",
                value="application2"   #Don't change this value otherwise the code will not work anymore!!!!
            ),
            discord.SelectOption(
                label="Banker Applicaton",  #Name of the 2 Select Menu Option
                description="Apply to be a banker here.", #Description of the 2 Select Menu Option
                emoji="🏦",
                value="application3"   #Don't change this value otherwise the code will not work anymore!!!!
            )
        ]
    )
    async def callback(self, select, interaction):
        await interaction.response.defer()
        timezone = pytz.timezone(TIMEZONE)
        creation_date = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
        user_name = interaction.user.name
        user_id = interaction.user.id

        cur.execute("SELECT discord_id FROM ticket WHERE discord_id=?", (user_id,)) #Check if the User already has a Ticket open
        existing_ticket = cur.fetchone()
        global apptype
        if existing_ticket is None:
            if "application1" in interaction.data['values']:
                if interaction.channel.id == APPLICATION_CHANNEL:
                    guild = self.bot.get_guild(GUILD_ID)
                    apptype="staff"
                    cur.execute("INSERT INTO ticket (discord_name, discord_id, ticket_created) VALUES (?, ?, ?)", (user_name, user_id, creation_date)) #If the User doesn't have a Ticket open it will insert the User into the Database and create a Ticket
                    conn.commit()
                    await asyncio.sleep(1)
                    cur.execute("SELECT id FROM ticket WHERE discord_id=?", (user_id,)) #Get the Ticket Number from the Database
                    ticket_number = cur.fetchone()[0]

                    category = self.bot.get_channel(CATEGORY_ID1)
                    ticket_channel = await guild.create_text_channel(f"staffapp-{ticket_number}", category=category,
                                                                        topic=f"{interaction.user.id}")

                    await ticket_channel.set_permissions(guild.get_role(TEAM_ROLE1), send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the Staff Team
                                                            embed_links=True, attach_files=True, read_message_history=True,
                                                            external_emojis=True)
                    await ticket_channel.set_permissions(interaction.user, send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the User
                                                            embed_links=True, attach_files=True, read_message_history=True,
                                                            external_emojis=True)
                    await ticket_channel.set_permissions(guild.default_role, send_messages=False, read_messages=False, view_channel=False) #Set the Permissions for the @everyone role
                    embed = discord.Embed(description=f'Welcome {interaction.user.mention},\n'
                                                        'someone from the recruiting team will be here soon.',   #Ticket Welcome message
                                                        color=discord.colour.Color.blue())
                    await ticket_channel.send(embed=embed, view=ApplicationMainButton(bot=self.bot))
                    
                    channel_id = ticket_channel.id
                    cur.execute("UPDATE ticket SET ticket_channel = ? WHERE id = ?", (channel_id, ticket_number))
                    conn.commit()

                    embed = discord.Embed(description=f'📬 Ticket was Created! Look here --> {ticket_channel.mention}',  
                                                color=discord.colour.Color.green())
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    await asyncio.sleep(1)
                    embed = discord.Embed(title=APPLICATION_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
                    await interaction.message.edit(embed=embed, view=ApplicationView(bot=self.bot)) #This will reset the SelectMenu in the Ticket Channel

            if "application2" in interaction.data['values']:
                if interaction.channel.id == APPLICATION_CHANNEL:
                    guild = self.bot.get_guild(GUILD_ID)
                    apptype="carrier"
                    cur.execute("INSERT INTO ticket (discord_name, discord_id, ticket_created) VALUES (?, ?, ?)", (user_name, user_id, creation_date)) #If the User doesn't have a Ticket open it will insert the User into the Database and create a Ticket
                    conn.commit()
                    await asyncio.sleep(1)
                    cur.execute("SELECT id FROM ticket WHERE discord_id=?", (user_id,)) #Get the Ticket Number from the Database
                    ticket_number = cur.fetchone()[0]

                    category = self.bot.get_channel(CATEGORY_ID1)
                    ticket_channel = await guild.create_text_channel(f"carryapp-{ticket_number}", category=category,
                                                                    topic=f"{interaction.user.id}")

                    await ticket_channel.set_permissions(guild.get_role(TEAM_ROLE2), send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the Staff Team
                                                        embed_links=True, attach_files=True, read_message_history=True,
                                                        external_emojis=True)
                    await ticket_channel.set_permissions(interaction.user, send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the User
                                                        embed_links=True, attach_files=True, read_message_history=True,
                                                        external_emojis=True)
                    
                    await ticket_channel.set_permissions(guild.default_role, send_messages=False, read_messages=False, view_channel=False) #Set the Permissions for the @everyone role
                    embed = discord.Embed(description=f'Welcome {interaction.user.mention},\n' #Ticket Welcome message
                                                       'someone from the recruiting team will be here soon.',
                                                    color=discord.colour.Color.blue())
                    await ticket_channel.send(embed=embed, view=ApplicationMainButton(bot=self.bot))

                    channel_id = ticket_channel.id
                    cur.execute("UPDATE ticket SET ticket_channel = ? WHERE id = ?", (channel_id, ticket_number))
                    conn.commit()

                    embed = discord.Embed(description=f'📬 Ticket was Created! Look here --> {ticket_channel.mention}',
                                            color=discord.colour.Color.green())
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    await asyncio.sleep(1)
                    embed = discord.Embed(title=APPLICATION_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
                    await interaction.message.edit(embed=embed, view=ApplicationView(bot=self.bot)) #This will reset the SelectMenu in the Ticket Channel
            if "application3" in interaction.data['values']:
                if interaction.channel.id == APPLICATION_CHANNEL:
                    guild = self.bot.get_guild(GUILD_ID)
                    apptype="banker"
                    cur.execute("INSERT INTO ticket (discord_name, discord_id, ticket_created) VALUES (?, ?, ?)", (user_name, user_id, creation_date)) #If the User doesn't have a Ticket open it will insert the User into the Database and create a Ticket
                    conn.commit()
                    await asyncio.sleep(1)
                    cur.execute("SELECT id FROM ticket WHERE discord_id=?", (user_id,)) #Get the Ticket Number from the Database
                    ticket_number = cur.fetchone()[0]

                    category = self.bot.get_channel(CATEGORY_ID1)
                    ticket_channel = await guild.create_text_channel(f"bankapp-{ticket_number}", category=category,
                                                                    topic=f"{interaction.user.id}")

                    await ticket_channel.set_permissions(guild.get_role(TEAM_ROLE3), send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the Staff Team
                                                        embed_links=True, attach_files=True, read_message_history=True,
                                                        external_emojis=True)
                    await ticket_channel.set_permissions(interaction.user, send_messages=True, read_messages=True, add_reactions=False, #Set the Permissions for the User
                                                        embed_links=True, attach_files=True, read_message_history=True,
                                                        external_emojis=True)
                    
                    await ticket_channel.set_permissions(guild.default_role, send_messages=False, read_messages=False, view_channel=False) #Set the Permissions for the @everyone role
                    embed = discord.Embed(description=f'Welcome {interaction.user.mention},\n' #Ticket Welcome message
                                                       'someone from the recruiting team will be here soon.',
                                                    color=discord.colour.Color.blue())
                    await ticket_channel.send(embed=embed, view=ApplicationMainButton(bot=self.bot))

                    channel_id = ticket_channel.id
                    cur.execute("UPDATE ticket SET ticket_channel = ? WHERE id = ?", (channel_id, ticket_number))
                    conn.commit()

                    embed = discord.Embed(description=f'📬 Ticket was Created! Look here --> {ticket_channel.mention}',
                                            color=discord.colour.Color.green())
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    await asyncio.sleep(1)
                    embed = discord.Embed(title=APPLICATION_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
                    await interaction.message.edit(embed=embed, view=ApplicationView(bot=self.bot)) #This will reset the SelectMenu in the Ticket Channel
        else:
            embed = discord.Embed(title=f"You already have a open Ticket", color=0xff0000)
            await interaction.followup.send(embed=embed, ephemeral=True) #This will tell the User that he already has a Ticket open
            await asyncio.sleep(1)
            embed = discord.Embed(title=APPLICATION_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
            await interaction.message.edit(embed=embed, view=ApplicationView(bot=self.bot)) #This will reset the SelectMenu in the Ticket Channel
             
class ApplicationModal(discord.ui.Modal):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="IGN:"))
        self.add_item(discord.ui.InputText(label="Are you a "+apptype+" in any other server?"))
        self.add_item(
            discord.ui.InputText(label="Why should we choose you?",
                                 style=discord.InputTextStyle.long))
        self.add_item(
            discord.ui.InputText(label="Why do you want to be a "+apptype+"?",
                                 style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Do you have 2FA enabled?"))

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Ticket Information:")
        embed.add_field(name="IGN:", value=self.children[0].value)
        embed.add_field(name="Are you a "+apptype+" in any other server?",
                        value=self.children[1].value)
        embed.add_field(name="Why should we choose you?",
                        value=self.children[2].value)
        embed.add_field(name="Why do you want to be a "+apptype+"?",
                        value=self.children[3].value)
        embed.add_field(name="Do you have 2FA enabled?",
                        value=self.children[4].value)
        await interaction.response.send_message(embeds=[embed])


class ApplicationMainButton(discord.ui.View):

    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label="Enter Information")
    async def button_callback(self, button: discord.ui.Button,
                              interaction: discord.Interaction):
        await interaction.response.send_modal(
            ApplicationModal(title="Enter Information"))

    @discord.ui.button(label="Delete Ticket 🎫",
                       style=discord.ButtonStyle.blurple,
                       custom_id="close")
    async def close(self, button: discord.ui.Button,
                    interaction: discord.Interaction):
        embed = discord.Embed(
            title="Delete Ticket 🎫",
            description="Are you sure you want to delete this Ticket?",
            color=discord.colour.Color.green())
        await interaction.response.send_message(
            embed=embed, view=TicketOptions(bot=self.bot)
        )  #This will show the User the TicketOptions View
        await interaction.message.edit(view=self)

#Buttons to reopen or delete the Ticket
class TicketOptions(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label="Delete Ticket 🎫", style = discord.ButtonStyle.red, custom_id="delete")
    async def delete_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        guild = self.bot.get_guild(GUILD_ID)
        channel = self.bot.get_channel(LOG_CHANNEL)
        ticket_id = interaction.channel.id

        cur.execute("SELECT id, discord_id, ticket_created FROM ticket WHERE ticket_channel=?", (ticket_id,))
        ticket_data = cur.fetchone()
        id, ticket_creator_id, ticket_created = ticket_data
        ticket_creator = guild.get_member(ticket_creator_id)

        ticket_created_unix = self.convert_to_unix_timestamp(ticket_created)
        timezone = pytz.timezone(TIMEZONE)
        ticket_closed = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
        ticket_closed_unix = self.convert_to_unix_timestamp(ticket_closed)

        #Creating the Transcript
        military_time: bool = True
        transcript = await chat_exporter.export(interaction.channel, limit=200, tz_info=TIMEZONE, military_time=military_time, bot=self.bot)
        
        transcript_file = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"transcript-{interaction.channel.name}.html")
        transcript_file2 = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"transcript-{interaction.channel.name}.html")
        
        embed = discord.Embed(description=f'Ticket is deleting in 5 seconds.', color=0xff0000)
        transcript_info = discord.Embed(title=f"Ticket Deleted | {interaction.channel.name}", color=discord.colour.Color.blue())
        transcript_info.add_field(name="ID", value=id, inline=True)
        transcript_info.add_field(name="Opened by", value=ticket_creator.mention, inline=True)
        transcript_info.add_field(name="Closed by", value=interaction.user.mention, inline=True)
        transcript_info.add_field(name="Ticket Created", value=f"<t:{ticket_created_unix}:f>", inline=True)
        transcript_info.add_field(name="Ticket Closed", value=f"<t:{ticket_closed_unix}:f>", inline=True)

        await interaction.response.send_message(embed=embed)
        try:
            await ticket_creator.send(embed=transcript_info, file=transcript_file)
        except:
            transcript_info.add_field(name="Error", value="Ticket Creator's DM is disabled", inline=True)

        await channel.send(embed=transcript_info, file=transcript_file2)
        await asyncio.sleep(3)
        await interaction.channel.delete(reason="Ticket Deleted")
        cur.execute("DELETE FROM ticket WHERE discord_id=?", (ticket_creator_id,))
        conn.commit()

    def convert_to_unix_timestamp(self, date_string):
        date_format = "%Y-%m-%d %H:%M:%S"
        dt_obj = datetime.strptime(date_string, date_format)
        berlin_tz = pytz.timezone('Europe/Berlin')
        dt_obj = berlin_tz.localize(dt_obj)
        dt_obj_utc = dt_obj.astimezone(pytz.utc)
        return int(dt_obj_utc.timestamp())
