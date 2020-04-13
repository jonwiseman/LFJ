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
    :param add: True if adding to database, False if deleting from database
    :param cursor: cursor object for executing search query
    :return: -1 if user does not exist, 0 if the user is not an admin, or 1 if the user is an admin
    """
    cursor.execute('select admin from user where display_name = %s', (display_name,))
    result = cursor.fetchall()

    if add and (len(result) == 0 or result[0][0] == 0):        # adding to the database
        raise AdminPermissionError(display_name)
    elif not add and (len(result) > 0 and result[0][0] == 1):       # removing from the database
        raise AdminPermissionError(display_name)


def get_id_from_name(display_name, cursor):
    """
    Gets a user id from display name of a user
    :param display_name: display name of user whose id will be gotten
    :param cursor: cursor object for executing search query
    :return: -1 if user does not exist, user_id if user is found
    """
    cursor.execute('select user_id from user where display_name = %s', (display_name,))
    result = cursor.fetchall()

    if len(result) == 0:  # user not found
        return -1

    return result[0][0]  # return user id


def get_name_from_id(user_id, cursor):
    """
    Gets a user id from display name of a user
    :param user_id: id of user whose display name will be gotten
    :param cursor: cursor object for executing search query
    :return: -1 if user does not exist, display_name if user is found
    """
    cursor.execute('select display_name from user where user_id = %s', (user_id,))
    result = cursor.fetchall()

    if len(result) == 0:  # user not found
        return -1

    return result[0][0]  # return display name


def get_id_from_title(title, cursor):
    """
    Gets an event id from title of event
    :param title: title of event name to get id for
    :param cursor: cursor object for executing search query
    :return: -1 if event does not exist, event_id if event is found
    """

    cursor.execute('select event_id from event where title = %s', (title,))
    result = cursor.fetchall()
    if len(result) == 0:  # event not found
        return -1
    return result[0][0] # return event id

# ERRORS #


class Error(Exception):
    """Base class for exceptions in this module."""


class AdminPermissionError(Error):
    """Invalid permission to modify database."""
    def __init__(self, display_name):
        self.display_name = display_name
