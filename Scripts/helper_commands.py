from discord.ext import commands


class HelperCommands(commands.Cog):
    def __init__(self, bot, cursor, cnx):
        self.bot = bot
        self.cursor = cursor
        self.cnx = cnx

    @commands.command(name='exit')
    async def exit_bot(self, ctx):
        """
        Prompt bot to logout
        :return: none
        """
        self.cursor.close()
        self.cnx.close()
        await self.bot.logout()  # log the bot out

# HELPER FUNCTIONS #


def check_admin_status(display_name, add, cursor):
    """
    Check to see if a given user is an admin.  Only admins can change the database.
    :param display_name: display name of requesting user
    :param cursor: cursor object for executing search query
    :return: -1 if user does not exist, 0 if the user is not an admin, or 1 if the user is an admin
    """
    cursor.execute('select admin from user where display_name = %s', (display_name,))
    result = cursor.fetchall()

    if add and (len(result) == 0 or result[0][0] == -1):        # adding to the database
        raise AdminPermissionError(display_name)
    elif not add and (len(result) > 0 and result[0][0] == 1):       # removing from the database
        raise AdminPermissionError(display_name)

# ERRORS #


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class AdminPermissionError(Error):
    def __init__(self, display_name):
        self.display_name = display_name
