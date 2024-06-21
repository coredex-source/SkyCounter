import discord
from discord.ext import commands, tasks
from discord import Permissions
import csv
import os
import asyncio
from datetime import datetime, timedelta
import json



class MainCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Dictionary to store message counts
        self.user_message_counts = {}
        self.user_last_message_time = {}

        # Variables for slowmode
        self.slowmode_enabled = False
        self.slowmode_interval = 0  # in seconds

        # Variables to track event timer
        self.event_start_time = None
        self.event_duration = None
        self.event_end_task = None
        self.event_channel = None

        self.load_config()
        self.load_message_counts()
        self.load_slowmode_config()


    def load_config(self):

        #Initailizing ticket system files
        with open("config.json", mode="r") as config_file:
            config = json.load(config_file)
        self.TOKEN = config["token"]
        self.GUILD_ID = config["guild_id"]
        self.CATEGORY_ID1 = config["category_id_1"]
        #self.CATEGORY_ID2 = config["category_id_2"]

    # Function to load text from a file
    def load_text_file(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, mode='r') as file:
                return file.read()
        return "No text found."


    # Function to load message counts from CSV
    def load_message_counts(self):
        if os.path.exists('message_counts.csv'):
            with open('message_counts.csv', mode='r', newline='') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row:  # Ensure the row is not empty
                        user_id, count = row
                        self.user_message_counts[int(user_id)] = int(count)
        print("Loaded message counts from CSV.")


    # Function to save message counts to CSV
    def save_message_counts(self):
        with open('message_counts.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            for user_id, count in self.user_message_counts.items():
                writer.writerow([user_id, count])
        print("Saved message counts to CSV.")


    # Function to load slowmode configuration from file
    def load_slowmode_config(self):
        global slowmode_enabled, slowmode_interval
        if os.path.exists('slowmode.config'):
            with open('slowmode.config', mode='r') as file:
                config = json.load(file)
                self.slowmode_enabled = config.get("enabled", False)
                self.slowmode_interval = config.get("interval", 0)
        print("Loaded slowmode configuration.")


    # Function to save slowmode configuration to file
    def save_slowmode_config(self):
        with open('slowmode.config', mode='w') as file:
            config = {"enabled": self.slowmode_enabled, "interval": self.slowmode_interval}
            json.dump(config, file)
        print("Saved slowmode configuration.")


    # Event: Bot is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user}')
        print(f'Bot Loaded  | maincog.py ')

    # Event: Message is received
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = message.author.id
        if self.slowmode_enabled:
            current_time = datetime.utcnow()
            if user_id in self.user_last_message_time:
                last_message_time = self.user_last_message_time[user_id]
                if (current_time -
                        last_message_time).total_seconds() < self.slowmode_interval:
                    return
            self.user_last_message_time[user_id] = current_time

        if user_id in self.user_message_counts:
            self.user_message_counts[user_id] += 1
        else:
            self.user_message_counts[user_id] = 1

        self.save_message_counts()
        #await bot.process_commands(message)


    # Command: Get message count for a user
    @commands.slash_command(
        name="messagecount",
        description="Get the message count for a user"
    )
    async def message_count(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        count = self.user_message_counts.get(member.id, 0)
        await ctx.send(f'{member.display_name} has sent {count} messages.')


    # Command: Get total messages sent in the server
    @commands.slash_command(
        name="totalmessages",
        description="Get the total number of messages sent in the server")
    async def total_messages(self,ctx):
        total = sum(self.user_message_counts.values())
        await ctx.send(f'Total messages sent: {total}')


    # Command: Clear all message counts
    @commands.slash_command(
        name="clearmessages",
        description="Clear all message counts for the server"
    )
    async def clear_messages(self, ctx):
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send(
                "You do not have the necessary permissions to use this command.",
                ephemeral=True
            )
            return

        self.user_message_counts.clear()
        self.save_message_counts()  # You should have a method to save this data
        await ctx.send("Message counts cleared.")


    # Command: Show leaderboard of top message senders
    @commands.slash_command(
        name="leaderboard",
        description="Show the top 10 users with the most messages"
    )
    async def leaderboard(self, ctx):
        sorted_users = sorted(self.user_message_counts.items(),
                              key=lambda item: item[1],
                              reverse=True)
        top_users = sorted_users[:10]

        leaderboard_message = "Top 10 Users by Message Count:\n"
        for rank, (user_id, count) in enumerate(top_users, start=1):
            try:
                user = await self.bot.fetch_user(user_id)
                leaderboard_message += f"{rank}. {user.display_name} - {count} messages\n"
            except discord.NotFound:
                leaderboard_message += f"{rank}. Unknown User (ID: {user_id}) - {count} messages\n"

        await ctx.send(leaderboard_message, ephemeral=True)
        
    @commands.slash_command(
        name="printleaderboard",
        description="Prints the top 10 users with the most messages"
    )
    async def print_leaderboard(self, ctx):
        sorted_users = sorted(self.user_message_counts.items(),
                              key=lambda item: item[1],
                              reverse=True)
        top_users = sorted_users[:10]

        embed = discord.Embed(
            title="Top 10 Users by Message Count",
            color=discord.Color.blue()
        )

        for rank, (user_id, count) in enumerate(top_users, start=1):
            try:
                user = await self.bot.fetch_user(user_id)
                embed.add_field(
                    name=f"{rank}. {user.display_name}",
                    value=f"{count} messages",
                    inline=False
                )
            except discord.NotFound:
                embed.add_field(
                    name=f"{rank}. Unknown User (ID: {user_id})",
                    value=f"{count} messages",
                    inline=False
                )

        await ctx.send(embed=embed)


    # Command: Start an event and schedule an end message
    @commands.slash_command(
        name="eventstart",
        description="Starts an event and schedules an end message"
    )
    async def event_start(self, ctx,
                          announcementchannel: discord.TextChannel,
                          duration_minutes: int):
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send(
                "You do not have the necessary permissions to use this command.",
                ephemeral=True
            )
            return

        # Clear all message counts (optional based on your needs)
        self.user_message_counts.clear()
        self.save_message_counts()  # Save the cleared message counts to CSV (example method)

        # Load the announcement from a file (example method)
        announcement = self.load_text_file("announcement.txt")

        # Send the announcement
        await announcementchannel.send(announcement)
        await ctx.send("Event successfully started.", ephemeral=True)

        # Track event start time and duration
        self.event_start_time = datetime.utcnow()
        self.event_duration = timedelta(minutes=duration_minutes)

        # Schedule sending the event end message after specified minutes
        self.event_end_task = self.bot.loop.create_task(
            self.schedule_event_end(announcementchannel, self.load_text_file("eventend.txt"))
        )

    async def schedule_event_end(self, announcementchannel, event_end_message):
        await asyncio.sleep(self.event_duration.total_seconds())
        await announcementchannel.send(event_end_message)
        self.reset_event_timer()

    def reset_event_timer(self):
        self.event_start_time = None
        self.event_duration = None
        self.event_end_task = None


    # Command: Show time left until event ends
    @commands.slash_command(
        name="timer",
        description="Shows the time left until event end"
    )
    async def timer(self, ctx):
        if self.event_start_time is None or self.event_duration is None:
            await ctx.send(
                "No event is currently running.",
                ephemeral=True
            )
            return

        current_time = datetime.utcnow()
        time_elapsed = current_time - self.event_start_time
        time_left = self.event_duration - time_elapsed

        if time_left.total_seconds() <= 0:
            await ctx.send("The event has already ended.", ephemeral=True)
        else:
            minutes_left = int(time_left.total_seconds() // 60)
            seconds_left = int(time_left.total_seconds() % 60)
            await ctx.send(
                f'Time left until event end: {minutes_left} minutes and {seconds_left} seconds',
                ephemeral=True
            )

    @commands.slash_command(
        name="printtimer",
        description="Shows the time left until event end"
    )
    async def print_timer(self, ctx):
        if self.event_start_time is None or self.event_duration is None:
            await ctx.send(
                "No event is currently running.",
                ephemeral=True
            )
            return

        current_time = datetime.utcnow()
        time_elapsed = current_time - self.event_start_time
        time_left = self.event_duration - time_elapsed

        if time_left.total_seconds() <= 0:
            await ctx.send("The event has already ended.", ephemeral=True)
        else:
            minutes_left = int(time_left.total_seconds() // 60)
            seconds_left = int(time_left.total_seconds() % 60)

            embed = discord.Embed(
                title="Event Timer",
                description=f"Time left until event end: {minutes_left} minutes and {seconds_left} seconds",
                color=discord.Color.green()
            )

            await ctx.send(embed=embed)

    # Command: End the ongoing event and send the end message
    @commands.slash_command(
        name="eventend",
        description="Ends the ongoing event and sends the end message"
    )
    async def event_end(self, ctx):
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send(
                "You do not have the necessary permissions to use this command.",
                ephemeral=True
            )
            return

        if self.event_start_time is None or self.event_duration is None:
            await ctx.send("No event is currently running.", ephemeral=True)
            return

        # Load the event end message from file (example method)
        event_end_message = self.load_text_file("eventend.txt")

        # Cancel any existing event end task if present
        if self.event_end_task:
            self.event_end_task.cancel()

        # Reset event timer
        self.reset_event_timer()

        # Send event end confirmation message
        await ctx.send("Event ended and timer cleared.", ephemeral=True)

        # Send event end message to event channel
        if self.event_channel:
            await self.event_channel.send(event_end_message)


    # Command: Reset message count of a user
    @commands.slash_command(
        name="resetuser",
        description="Resets the message count of a user"
    )
    async def reset_count(self, ctx, member: discord.Member):
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send(
                "You do not have the necessary permissions to use this command.",
                ephemeral=True
            )
            return

        if member.id in self.user_message_counts:
            del self.user_message_counts[member.id]
            self.save_message_counts()  # Save updated message counts (example method)
            await ctx.send(
                f"Message count reset for {member.display_name}.",
                ephemeral=False
            )
        else:
            await ctx.send(
                "This user has no recorded message count.",
                ephemeral=False
            )


    # Command: Enable or disable slowmode
    @commands.slash_command(
        name="slowmode",
        description="Enable or disable slowmode and set the interval in seconds"
    )
    async def slowmode(self, ctx, enable: bool = None, interval_seconds: int = 0):
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send(
                "You do not have the necessary permissions to use this command.",
                ephemeral=True
            )
            return

        if enable is None:
            await ctx.send(
                f"Slowmode is {'enabled' if self.slowmode_enabled else 'disabled'}. Current interval: {self.slowmode_interval} seconds.",
                ephemeral=True
            )
        else:
            self.slowmode_enabled = enable
            self.slowmode_interval = interval_seconds
            self.save_slowmode_config()  # Save slowmode configuration (example method)
            await ctx.send(
                f"Slowmode {'enabled' if enable else 'disabled'}. Interval set to {interval_seconds} seconds.",
                ephemeral=True
            )


    # Command: Show current slowmode status and interval
    @commands.slash_command(
        name="slowmodestatus",
        description="Shows the current slowmode status and interval"
    )
    async def slowmode_status(self, ctx):
        status_message = (
            f"Slowmode is {'enabled' if self.slowmode_enabled else 'disabled'}. "
            f"Current interval: {self.slowmode_interval} seconds."
        )
        await ctx.send(status_message, ephemeral=False)

def setup(bot):
    bot.add_cog(MainCog(bot))