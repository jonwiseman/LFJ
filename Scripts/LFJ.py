from discord.ext import commands
import mysql.connector


class LFJ(commands.Bot):
    event_channel = None
    event_created = True
    cursor = None
    cnx = None

    def __init__(self, command_prefix, case_insensitive, event_channel, cursor, cnx):
        super().__init__(command_prefix=command_prefix, case_insensitive=case_insensitive)
        self.event_channel = event_channel
        self.cursor = cursor
        self.cnx = cnx

    async def on_ready(self):
        """
        on_ready() is called when the bot is signed in to Discord and ready to send/receive event notifications
        :return: none; print ready status to console
        """
        print('We have logged in as {0.user}'.format(self))

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
        :param auth_user: user authorizing add
        :param data_insert: dictionary of data to be inserted (user id, display name, email, and admin status)
        :param cursor: cursor for executing query
        :param cnx: connection object for committing change
        :return: the new table after insertion or an error flag
        """
        admin_status = check_admin_status(str(ctx.author), ctx.bot.cursor)  # see if the authorizing user is an admin
        if admin_status != 1:  # authorizing user does not exist or does not have permission
            await ctx.send('You do not have permission to execute this command.')
            return

        ctx.bot.cursor.execute('insert into user '
                       '(user_id, display_name, e_mail, admin) '
                       'values (%s, %s, %s, %s)', (display_name.split('#')[1], display_name,
                                                   email, admin))  # add new user
        ctx.bot.cnx.commit()  # commit changes to database

        ctx.bot.cursor.execute('select * from user')  # get new user table
        await ctx.send(ctx.bot.cursor.fetchall())

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
    async def exit(ctx):
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
