from discord.ext import commands

# DB에 없는 유저
class NotRegisteredUser(commands.CheckFailure): ...