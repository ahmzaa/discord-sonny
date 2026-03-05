import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()


# --- EVENT: MEMBER JOIN, AUTO ROLE & WELCOME MESSAGE
class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Pulling these from .env inside the Cog
        self.welcome_channel_id = int(os.getenv("WELCOME_CHANNEL_ID"))
        self.initial_member_role_id = int(os.getenv("INITIAL_MEMBER_ROLE_ID"))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # 1. Assign the initial role
        role = member.guild.get_role(self.initial_member_role_id)
        if role:
            try:
                await member.add_roles(role)
            except discord.Forbidden:
                print(f"Error: Bot lacks permission to assign roles to {member.name}.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

        # 2. Send the welcome message
        channel = self.bot.get_channel(self.welcome_channel_id)
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

            await channel.send(embed=welcome_embed)
        else:
            print(
                f"Error: Could not find welcome channel with ID {self.welcome_channel_id}"
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
