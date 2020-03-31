import discord
from discord.ext import commands
import mysql.connector
import re


class LFJ(commands.Bot):
    event_channel = None
    event_created = True
    cursor = None
    cnx = None

    def __init__(self, command_prefix, case_insensitive, event_channel, cursor, cnx):
        super().__init__(command_prefix=command_prefix, case_insensitive=case_insensitive)
        self.cursor = cursor
        self.cnx = cnx
        self.event_channel = event_channel

    async def on_ready(self):
        """
        on_ready() is called when the bot is signed in to Discord and ready to send/receive event notifications
        :return: none; print ready status to console
        """
        print('We have logged in as {0.user}'.format(self))
        for channel in self.get_all_channels():
            if str(channel.name) == self.event_channel:
                self.event_channel = channel

    @commands.command()
    async def query_user(ctx, argument):
        """
        Query information from the user table.
        :param argument: either ALL (for a select * from user query) or a display name (for getting information about a
        specific user).
        :return: The result of the select statement
        """
        cursor = ctx.bot.cursor
        if argument.lower() == 'all':
            cursor.execute('select * from user')
        else:
            cursor.execute('select * from user where display_name = %s', (argument,))

        results = cursor.fetchall()
        if len(results) == 0:
            await ctx.send("No results found")
        else:
            await ctx.send(results)

    @commands.command()
    async def add_user(ctx, display_name, email, admin):
        """
        Add a user to the user table.
        :param display_name: display name of user to add)
        :param email: email of user to add
        :param admin: admin status of user
        :return: the new table after insertion or an error flag
        """
        cursor = ctx.bot.cursor
        cnx = ctx.bot.cnx

        admin_status = check_admin_status(str(ctx.author), cursor)  # see if the authorizing user is an admin
        if admin_status != 1:  # authorizing user does not exist or does not have permission
            await ctx.send('You do not have permission to execute this command.')
            return

        cursor.execute('insert into user '
                       '(user_id, display_name, e_mail, admin) '
                       'values (%s, %s, %s, %s)', (display_name.split('#')[1], display_name,
                                                   email, admin))  # add new user
        cnx.commit()  # commit changes to database

        cursor.execute('select * from user')  # get new user table
        await ctx.send(cursor.fetchall())

    @commands.command()
    async def delete_user(ctx, display_name):
        """
        Delete a row from the user table based on display name.
        :param auth_user: user who is authorizing the delete
        :param display_name: display name of the user to be deleted
        :param cursor: cursor object for executing query
        :param cnx: connection object for committing changes
        :return: the new table after deletion or an error flag
        """
        cursor = ctx.bot.cursor
        cnx = ctx.bot.cnx

        admin_status = check_admin_status(str(ctx.author), cursor)  # see if the authorizing user is an admin
        if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
            return 1

        delete_admin = check_admin_status(display_name, cursor)  # see if the user to be deleted is an admin
        if delete_admin == -1 or delete_admin == 1:  # trying to delete a non-existant user or another admin
            return 1

        cursor.execute('delete from user where display_name = %s', (display_name,))  # execute deletion query
        cnx.commit()  # commit changes to database
        cursor.execute('select * from user')  # get new user table
        await ctx.send(cursor.fetchall())

    @commands.command()
    async def set_email(ctx, display_name, email):
        """
        Update the email associated with a user.
        :param auth_user: user authorizing change
        :param display_name: display name of user whose email will be changed
        :param email: new email for user
        :param cursor: cursor object to execute query
        :param cnx: connection object to commit changes
        :return: the new table after updating the user table
        """
        cursor = ctx.bot.cursor
        cnx = ctx.bot.cnx

        admin_status = check_admin_status(str(ctx.author), cursor)  # see if the authorizing user is an admin
        if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
            return 1

        cursor.execute('update user '
                       'set e_mail = %s '
                       'where display_name = %s', (email, display_name))  # change the user table with new email
        cnx.commit()  # commit changes to user table
        cursor.execute('select * from user')  # get new user table
        await ctx.send(cursor.fetchall())

    @commands.command()
    async def set_admin_status(ctx, display_name, new_status):
        """
        Update the admin status associated with a user.
        :param auth_user: user authorizing change
        :param display_name: display name of user whose admin status will be changed
        :param new_status: true or false depending on admin status being set
        :param cursor: cursor object to execute query
        :param cnx: connection object to commit changes
        :return: the new table after updating the user table
        """
        cursor = ctx.bot.cursor
        cnx = ctx.bot.cnx

        admin_status = check_admin_status(str(ctx.author), cursor)  # see if the authorizing user is an admin
        if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
            return 1

        if not (new_status.lower() == 'true' or new_status.lower() == 'false'):
            return 1

        cursor.execute('update user '
                       'set admin = %s '
                       'where display_name = %s', (1 if new_status == "true" else 0, display_name))
        cnx.commit()  # commit changes to user table
        cursor.execute('select * from user')  # get new user table
        await ctx.send(cursor.fetchall())

    @commands.command()
    async def add_game(ctx, id, name):
        cursor = ctx.bot.cursor
        cnx = ctx.bot.cnx

        admin_status = check_admin_status(str(ctx.author), cursor)  # see if the authorizing user is an admin
        if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
            return 1

        cursor.execute('insert into game '
                       '(game_id, name) '
                       'values (%(game_id)s, %(name)s)', (id, name))  # add new user
        cnx.commit()  # commit changes to database

        cursor.execute('select * from game')  # get new user table
        await ctx.send(cursor.fetchall())

    @commands.command()
    async def delete_game(ctx, name):
        cursor = ctx.bot.cusor
        cnx = ctx.bot.cnx

        admin_status = check_admin_status(str(ctx.author), cursor)  # see if the authorizing user is an admin
        if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
            return 1

        cursor.execute('delete from game where name = %s', (name,))  # execute deletion query
        cnx.commit()  # commit changes to database
        cursor.execute('select * from game')  # get new user table
        await ctx.send(cursor.fetchall())

    @commands.command()
    async def query_game(ctx, *, argument):
        cursor = ctx.bot.cursor

        if argument.lower() == 'all':
            cursor.execute('select * from game')
        else:
            cursor.execute('select * from game where name = %s', (argument,))

        results = cursor.fetchall()
        if len(results) == 0:
            await ctx.send("No results found")
        else:
            await ctx.send(results)

    @commands.command()
    async def edit_name(ctx, *args):
        cursor = ctx.bot.cursor
        cnx = ctx.bot.cnx

        admin_status = check_admin_status(str(ctx.author), cursor)  # see if the authorizing user is an admin
        if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
            return 1

        cursor.execute('update game '
                       'set name = %s '
                       'where name = %s', (args[1], args[0]))  # change the game table with new email
        cnx.commit()  # commit changes to user table
        cursor.execute('select * from game')  # get new user table
        await ctx.send(cursor.fetchall())

    @commands.command()
    async def edit_id(ctx, *args):
        cursor = ctx.bot.cursor
        cnx = ctx.bot.cnx

        admin_status = check_admin_status(str(ctx.author), cursor)  # see if the authorizing user is an admin
        if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
            return 1

        cursor.execute('update game '
                       'set game_id = %s '
                       'where name = %s', (args[1], args[0]))  # change the game table with new email
        cnx.commit()  # commit changes to user table
        cursor.execute('select * from game')  # get new user table
        await ctx.send(cursor.fetchall())

    @commands.command()
    async def create_event(ctx, *args):
        await ctx.bot.event_channel.send(event_message_creator(args))

    @commands.command()
    async def exit(ctx):
        ctx.bot.cursor.close()
        ctx.bot.cnx.close()
        await ctx.bot.logout()


def check_admin_status(display_name, cursor):
    """
    Check to see if a given user is an admin.  Only admins can change the database.
    :param display_name: display name of requesting user
    :param cursor: cursor object for executing search query
    :return: -1 if user does not exist, 0 if the user is not an admin, or 1 if the user is an admin
    """
    cursor.execute('select admin from user where display_name = %s', (display_name,))
    result = cursor.fetchall()

    if len(result) == 0:  # user not found
        return -1

    return result[0][0]  # return 0 or 1


def parse_creation_message(message):
    """
    Parse the bot's creation message and extract event title, event date, and event game using regular expressions.
    :param message: bot's creation message
    :return: title, date and game (or three error flags)
    """
    title = re.search('Title: [\w]+([_]*[\w]*)*', message).group(0).split(' ')[1]
    date = re.search('Date: [0-9]+/[0-9]+/[0-9][0-9][0-9][0-9]', message).group(0).split(' ')[1]
    game = re.search('Game: [\w]+', message).group(0).split(' ')[1]

    if title is None or date is None or game is None:
        return 1, 1, 1
    else:
        return title, date, game


def get_game_id(game_name, cursor):
    """
    Query the game table to get the numeric ID associated with a game's name
    :param game_name: name of the game
    :param cursor: MySQL cursor for executing commands
    :return: integer ID of game
    """
    cursor.execute('select game_id from game where name = %s', (game_name,))
    return cursor.fetchall()


def event_message_creator(message):
    return f'--------------------------------------------------\n' \
        f'Title: {message[0]}\n' \
        f'Date: {message[1]}\n' \
        f'Game: {message[2]}\n' \
        f'--------------------------------------------------'
