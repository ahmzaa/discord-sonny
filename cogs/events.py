import os
from typing import Union

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

GENERAL_CHANNEL_ID = os.getenv("GENERAL_CHANNEL_ID") or ""
SUPPORT_CHANNEL_ID = os.getenv("SUPPORT_CHANNEL_ID") or ""
VC_TEXT_CHANNEL_ID = os.getenv("VC_TEXT_CHANNEL_ID") or ""
DCADMIN_ROLE_ID = os.getenv("DCADMIN_ROLE_ID") or ""
NETWORKADMIN_ROLE_ID = os.getenv("NETWORKADMIN_ROLE_ID") or ""


# --- EVENT: MEMBER JOIN, AUTO ROLE & WELCOME MESSAGE
class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.welcome_channel_id = int(os.getenv("WELCOME_CHANNEL_ID") or 0)
        self.initial_member_role_id = int(os.getenv("INITIAL_MEMBER_ROLE_ID") or 0)

    def create_welcome_embed(
        self, member: Union[discord.Member, discord.User]
    ) -> discord.Embed:
        embed = discord.Embed(
            title="Welcome 🎉🎉",
            description=(
                f"Welcome to the ahmza discord server {member.mention}.\n\n"
                f"Before you can do much you will need to be assigned a role by a "
                f"<@&{DCADMIN_ROLE_ID}> or <@&{NETWORKADMIN_ROLE_ID}>"
            ),
            color=discord.Color.from_rgb(0, 176, 244),
            timestamp=discord.utils.utcnow(),
        )

        embed.add_field(
            name="Key Info",
            value=(
                f"Once you have your role checkout these pages:\n\n"
                f"- <#{GENERAL_CHANNEL_ID}> - For general conversation\n"
                f"- <#{SUPPORT_CHANNEL_ID}> - For support with ahmza.com services\n"
                f"- <#{VC_TEXT_CHANNEL_ID}> - For messages while in voice chat"
            ),
            inline=False,
        )

        embed.set_footer(
            text="I hope you enjoy your stay.",
            icon_url=self.bot.user.display_avatar.url if self.bot.user else None,
        )
        return embed

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # --- Assign the initial role ---
        role = member.guild.get_role(self.initial_member_role_id)
        if role:
            try:
                await member.add_roles(role)
            except discord.Forbidden:
                print(f"Error: Bot lacks permission to assign roles to {member.name}.")
            except discord.HTTPException as e:
                print(
                    f"An unexpected error occurred assigning role to {member.name}: {e}"
                )

        # --- Send the welcome message ---
        channel = self.bot.get_channel(self.welcome_channel_id)
        if isinstance(channel, discord.TextChannel):
            embed = self.create_welcome_embed(member)
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                print(
                    f"Error: Bot lacks permission to send in welcome channel {self.welcome_channel_id}."
                )
            except discord.HTTPException as e:
                print(f"Failed to send welcome message: {e}")

    # ------------------------------------------------------------------ #
    #  /testwelcome                                                        #
    # ------------------------------------------------------------------ #
    @app_commands.command(
        name="testwelcome",
        description="Preview the welcome embed (admin only).",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def test_welcome(self, interaction: discord.Interaction):
        embed = self.create_welcome_embed(interaction.user)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @test_welcome.error
    async def test_welcome_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
