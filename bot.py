import os
import discord
from discord import app_commands
from dotenv import load_dotenv

# --- Configuration ---

load_dotenv()
token = os.getenv("TOKEN")
welcome_channel_id = os.getenv("WELCOME_CHANNEL_ID")
initial_member_role_id = os.getenv("INITIAL_MEMBER_ROLE_ID")


class sonny(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing, name="with penguins 🐧"
            ),
            status=discord.Status.online,
        )


client = sonny()


# --- EVENT Welcome & Auto-role ---
@client.event
async def on_member_join(member):
    # Assign the initial role
    role = member.guild.get_role(initial_member_role_id)
    if role:
        try:
            await member.add_roles(role)
        except discord.Forbidden as e:
            print(f"Error: {e}")

    # Send welcome message
    channel = client.get_channel(welcome_channel_id)
    if channel:
        welcome_embed = discord.Embed(
            title="Welcome 🎉🎉🎉",
            description=f"Hey {member.mention}, welcome to the AHMZA discord server!",
            color=discord.Color.blue(),
        )
        welcome_embed.set_thumbnail(url=member.display_avatar.url)
        welcome_embed.add_field(
            name="Total Members", value=f"{member.guild.member_count}", inline=True
        )
        welcome_embed.set_footer(
            text="You will need to be given a role before you can do more"
        )

        await channel.send(embed=embed)


# --- SLASH COMMAND: PING ---
@client.tree.command(name="ping", description="Check bots latency")
async def ping(interaction: discord.Interaction):
    latency = round(client.latency * 1000)
    await interaction.response.send_message(f"Pong! 🏓 ({latency}ms)")


# --- SLASH COMMAND: CLEAR ---
@client.tree.command(name="clear", description="Delete a specific number of messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    if amount < 1:
        return await interaction.response.send_message(
            "Please provide a number greater than 0.", ephemeral=True
        )

    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(
        f"✅ Deleted {amount} messages.", ephemeral=True
    )


# Error handling for the clear command (if user lacks permissions)
@clear.error
async def clear_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "You don't have permission to use this!", ephemeral=True
        )


client.run(token)
