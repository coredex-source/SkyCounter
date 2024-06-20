import discord
from discord.app_commands import default_permissions
from discord.ext import commands
from discord import Permissions
import csv
import os
from dotenv import load_dotenv, dotenv_values
import asyncio
from datetime import datetime, timedelta
import json

# File to store user message counts
CSV_FILE = 'message_counts.csv'
ANNOUNCEMENT_FILE = 'announcement.txt'
EVENT_END_FILE = 'eventend.txt'
SLOWMODE_CONFIG_FILE = 'slowmode.config'

intents = discord.Intents.all()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary to store message counts
user_message_counts = {}
user_last_message_time = {}

# Variables for slowmode
slowmode_enabled = False
slowmode_interval = 0  # in seconds

# Variables to track event timer
event_start_time = None
event_duration = None
event_end_task = None  # Task to keep track of event end
event_channel = None


# Function to load message counts from CSV
def load_message_counts():
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if row:  # Ensure the row is not empty
                    user_id, count = row
                    user_message_counts[int(user_id)] = int(count)
    print("Loaded message counts from CSV.")


# Function to save message counts to CSV
def save_message_counts():
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        for user_id, count in user_message_counts.items():
            writer.writerow([user_id, count])
    print("Saved message counts to CSV.")


# Function to load slowmode configuration from file
def load_slowmode_config():
    global slowmode_enabled, slowmode_interval
    if os.path.exists(SLOWMODE_CONFIG_FILE):
        with open(SLOWMODE_CONFIG_FILE, mode='r') as file:
            config = json.load(file)
            slowmode_enabled = config.get("enabled", False)
            slowmode_interval = config.get("interval", 0)
    print("Loaded slowmode configuration.")


# Function to save slowmode configuration to file
def save_slowmode_config():
    with open(SLOWMODE_CONFIG_FILE, mode='w') as file:
        config = {"enabled": slowmode_enabled, "interval": slowmode_interval}
        json.dump(config, file)
    print("Saved slowmode configuration.")


# Function to load text from a file
def load_text_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, mode='r') as file:
            return file.read()
    return "No text found."


@bot.event
async def on_ready():
    load_message_counts()
    await bot.tree.sync()  # Sync commands globally or specify a guild
    print(f'Logged in as {bot.user}')


@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore messages from bots

    if message.author == bot.user:
        return

    global slowmode_enabled, slowmode_interval
    user_id = message.author.id
    if slowmode_enabled:
        # Check if the user has sent a message within the slowmode interval
        current_time = datetime.utcnow()

        if user_id in user_last_message_time:
            last_message_time = user_last_message_time[user_id]
            if (current_time -
                    last_message_time).total_seconds() < slowmode_interval:
                return

        # Update last message time for the user
        user_last_message_time[user_id] = current_time

    # Update message count for the user
    if user_id in user_message_counts:
        user_message_counts[user_id] += 1
    else:
        user_message_counts[user_id] = 1

    save_message_counts()  # Save to CSV whenever a message is sent
    await bot.process_commands(message)


@bot.tree.command(name="messagecount",
                  description="Get the message count for a user")
async def message_count(interaction: discord.Interaction,
                        member: discord.Member = None):
    if member is None:
        member = interaction.user

    count = user_message_counts.get(member.id, 0)
    await interaction.response.send_message(
        f'{member.display_name} has sent {count} messages.')


@bot.tree.command(
    name="totalmessages",
    description="Get the total number of messages sent in the server")
async def total_messages(interaction: discord.Interaction):
    total = sum(user_message_counts.values())
    await interaction.response.send_message(f'Total messages sent: {total}')


@bot.tree.command(name="clearmessages",
                  description="Clear all message counts for the server")
async def clear_messages(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "You do not have the necessary permissions to use this command.",
            ephemeral=True)
        return
    user_message_counts.clear()
    save_message_counts()  # Save to CSV after clearing
    await interaction.response.send_message(f'Message counts cleared.')


@bot.tree.command(name="leaderboard",
                  description="Show the top 10 users with the most messages")
async def leaderboard(interaction: discord.Interaction):
    # Sort the users by message count in descending order
    sorted_users = sorted(user_message_counts.items(),
                          key=lambda item: item[1],
                          reverse=True)
    top_users = sorted_users[:10]  # Get the top 10 users

    # Create the leaderboard message
    leaderboard_message = "Top 10 Users by Message Count:\n"
    for rank, (user_id, count) in enumerate(top_users, start=1):
        try:
            # Fetch user from the guild
            user = interaction.guild.get_member(
                user_id) or await bot.fetch_user(user_id)
            leaderboard_message += f"{rank}. {user.display_name} - {count} messages\n"
        except discord.NotFound:
            leaderboard_message += f"{rank}. Unknown User (ID: {user_id}) - {count} messages\n"

    await interaction.response.send_message(leaderboard_message,
                                            ephemeral=True)


@bot.tree.command(
    name="printleaderboard",
    description=
    "Show the top 10 users with the most messages in a static message")
async def printleaderboard(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "You do not have the necessary permissions to use this command.",
            ephemeral=True)
        return

    # Sort the users by message count in descending order
    sorted_users = sorted(user_message_counts.items(),
                          key=lambda item: item[1],
                          reverse=True)
    top_users = sorted_users[:10]  # Get the top 10 users

    # Create the leaderboard message
    leaderboard_message = "Top 10 Users by Message Count:\n"
    for rank, (user_id, count) in enumerate(top_users, start=1):
        try:
            # Fetch user from the guild
            user = interaction.guild.get_member(
                user_id) or await bot.fetch_user(user_id)
            leaderboard_message += f"{rank}. {user.display_name} - {count} messages\n"
        except discord.NotFound:
            leaderboard_message += f"{rank}. Unknown User (ID: {user_id}) - {count} messages\n"

    await interaction.response.send_message(leaderboard_message,
                                            ephemeral=False)


@bot.tree.command(name="eventstart",
                  description="Starts an event and schedules an end message")
async def event_start(interaction: discord.Interaction,
                      announcementchannel: discord.TextChannel,
                      duration_minutes: int):
    global event_start_time, event_duration, event_end_task, event_channel
    event_channel = announcementchannel

    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "You do not have the necessary permissions to use this command.",
            ephemeral=True)
        return

    # Clear all message counts
    user_message_counts.clear()
    save_message_counts()  # Save the cleared message counts to CSV

    # Load the announcement from file
    announcement = load_text_file(ANNOUNCEMENT_FILE)

    # Send the announcement
    await announcementchannel.send(announcement)
    await interaction.response.send_message("Event successfully started.",
                                            ephemeral=True)

    # Load the event end message from file
    event_end_message = load_text_file(EVENT_END_FILE)

    # Track event start time and duration
    event_start_time = datetime.utcnow()
    event_duration = timedelta(minutes=duration_minutes)

    # Cancel any existing event end task if present
    if event_end_task:
        event_end_task.cancel()

    # Schedule sending the event end message after specified minutes
    event_end_task = bot.loop.create_task(
        schedule_event_end(announcementchannel, event_end_message,
                           event_duration))


async def schedule_event_end(announcementchannel, event_end_message, duration):
    await asyncio.sleep(duration.total_seconds())
    await announcementchannel.send(event_end_message)
    reset_event_timer()


def reset_event_timer():
    global event_start_time, event_duration, event_end_task
    event_start_time = None
    event_duration = None
    event_end_task = None


@bot.tree.command(name="timer",
                  description="Shows the time left until event end")
async def timer(interaction: discord.Interaction):
    global event_start_time, event_duration

    if event_start_time is None or event_duration is None:
        await interaction.response.send_message(
            "No event is currently running.", ephemeral=True)
        return

    current_time = datetime.utcnow()
    time_elapsed = current_time - event_start_time
    time_left = event_duration - time_elapsed

    if time_left.total_seconds() <= 0:
        await interaction.response.send_message("The event has already ended.",
                                                ephemeral=True)
    else:
        minutes_left = int(time_left.total_seconds() // 60)
        seconds_left = int(time_left.total_seconds() % 60)
        await interaction.response.send_message(
            f'Time left until event end: {minutes_left} minutes and {seconds_left} seconds',
            ephemeral=True)


@bot.tree.command(name="printtimer",
                  description="Prints the time left until event end")
async def printtimer(interaction: discord.Interaction):
    global event_start_time, event_duration

    if event_start_time is None or event_duration is None:
        await interaction.response.send_message(
            "No event is currently running.", ephemeral=True)
        return

    current_time = datetime.utcnow()
    time_elapsed = current_time - event_start_time
    time_left = event_duration - time_elapsed

    if time_left.total_seconds() <= 0:
        await interaction.response.send_message("The event has already ended.",
                                                ephemeral=True)
    else:
        minutes_left = int(time_left.total_seconds() // 60)
        seconds_left = int(time_left.total_seconds() % 60)
        await interaction.response.send_message(
            f'Time left until event end: {minutes_left} minutes and {seconds_left} seconds',
            ephemeral=False)


@bot.tree.command(name="eventend",
                  description="Ends the ongoing event and clears the timer")
async def event_end(interaction: discord.Interaction):
    global event_start_time, event_duration, event_end_task, event_channel
    announcementchannel = event_channel
    event_end_message = load_text_file(EVENT_END_FILE)
    if event_start_time is None or event_duration is None:
        await interaction.response.send_message(
            "No event is currently running.", ephemeral=True)
        return

    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "You do not have the necessary permissions to use this command.",
            ephemeral=True)
        return

    if event_end_task:
        event_end_task.cancel()

    reset_event_timer()
    await interaction.response.send_message("Event ended and timer cleared.",
                                            ephemeral=True)
    await announcementchannel.send(event_end_message)


@bot.tree.command(name="resetuser",
                  description="Resets the message count of a user")
async def reset_count(interaction: discord.Interaction,
                      member: discord.Member):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "You do not have the necessary permissions to use this command.",
            ephemeral=True)
        return

    if member.id in user_message_counts:
        del user_message_counts[member.id]
        save_message_counts()  # Save updated message counts to CSV
        await interaction.response.send_message(
            f"Message count reset for {member.display_name}.", ephemeral=False)
    else:
        await interaction.response.send_message(
            "This user has no recorded message count.", ephemeral=False)


@bot.tree.command(
    name="slowmode",
    description="Enable or disable slowmode and set the interval in seconds")
async def slowmode(interaction: discord.Interaction,
                   enable: bool = None,
                   interval_seconds: int = 0):
    global slowmode_enabled, slowmode_interval

    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "You do not have the necessary permissions to use this command.",
            ephemeral=True)
        return

    if enable is None:
        # Show current slowmode status and interval
        await interaction.response.send_message(
            f"Slowmode is {'enabled' if slowmode_enabled else 'disabled'}. Current interval: {slowmode_interval} seconds.",
            ephemeral=True)
    else:
        # Enable or disable slowmode
        slowmode_enabled = enable
        slowmode_interval = interval_seconds
        save_slowmode_config()
        await interaction.response.send_message(
            f"Slowmode {'enabled' if enable else 'disabled'}. Interval set to {interval_seconds} seconds.",
            ephemeral=True)


@bot.tree.command(name="slowmodestatus",
                  description="Shows the current slowmode status and interval")
async def slowmode_status(interaction: discord.Interaction):
    global slowmode_enabled, slowmode_interval
    status_message = f"Slowmode is {'enabled' if slowmode_enabled else 'disabled'}. Current interval: {slowmode_interval} seconds."
    await interaction.response.send_message(status_message, ephemeral=False)


# Load slowmode configuration at startup
load_slowmode_config()

load_dotenv()
#TOKEN = os.environ['TOKEN']
TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
