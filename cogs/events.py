import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

channel_general = os.getenv("GENERAL_CHANNEL_ID")
channel_support = os.getenv("SUPPORT_CHANNEL_ID")
channel_vc_text = os.getenv("VC_TEXT_CHANNEL_ID")
dcadmin_role_id = os.getenv("DCADMIN_ROLE_ID")
networkadmin_role_id = os.getenv("NETWORKADMIN_ROLE_ID")


# --- EVENT: MEMBER JOIN, AUTO ROLE & WELCOME MESSAGE
class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Pulling these from .env inside the Cog
        self.welcome_channel_id = int(os.getenv("WELCOME_CHANNEL_ID"))
        self.initial_member_role_id = int(os.getenv("INITIAL_MEMBER_ROLE_ID"))

    def create_welcome_embed(self, member: discord.Member):
        embed = discord.Embed(
            title="Welcome 🎉🎉",
            description=(
                f"Welcome to the ahmza discord server {member.mention}.\n\n"
                f"Before you can do much you will need to be assigned a role by a"
                f"<@&{dcadmin_role_id}> or <@&{networkadmin_role_id}>"
            ),
            colour=0x00B0F4,
            timestamp=datetime.now(),
        )

        embed.add_field(
            name="Key Info",
            value=(
                f"Once you have your role checkout these pages:\n\n"
                f"- <#{channel_general}> - For general conversation\n"
                f"- <#{channel_support}> - For support with ahmza.com services\n"
                f"- <#{channel_vc_text}> - For messages while in voice chat"
            ),
            inline=False,
        )

        embed.set_footer(
            text="I hope you enjoy your stay.",
            icon_url="https://cdn.discordapp.com/app-icons/1477746789493899449/b439974fe19aaf9143bd3be7f36fd593.png?size=256",
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
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

        # --- Send the welcome message ---
        channel = self.bot.get_channel(self.welcome_channel_id)
        if channel:
            embed = self.create_welcome_embed(member)
            await channel.send(embed=embed)

    @commands.command(name="testwelcome")
    @commands.has_permissions(administrator=True)
    async def test_welcome(self, ctx):
        # --- Manually trigger welcome message to test embed ---
        embed = self.create_welcome_embed(ctx.author)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
