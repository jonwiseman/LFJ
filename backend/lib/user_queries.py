from discord.ext import commands
from backend.lib.helper_commands import check_admin_status, AdminPermissionError


class UserQueries(commands.Cog):
    def __init__(self, bot, cursor, cnx):
        self.bot = bot
        self.cursor = cursor
        self.cnx = cnx

    @commands.command()
    async def add_user(self, ctx, display_name, email, admin):
        """
        Add a user to the LFJ backend
        :param display_name: display name of new user
        :param email: email of new user
        :param admin: admin status of new user
        :return: a message displaying the new user table or an error message
        """
        try:
            message = sql_add_user(str(ctx.author), display_name.split('#')[1], display_name, email, admin,
                                   self.cursor, self.cnx)
        except AdminPermissionError:
            await ctx.send("Permission error encountered.  Only admins can add users to the backend.")
        except ExistingUserError:
            await ctx.send("Error: this user already exists.")
        else:
            await ctx.send(message)

    @commands.command()
    async def delete_user(self, ctx, display_name):
        """
        Delete a user from LFJ backend
        :param display_name: display name of user to be deleted
        :return:  a message displaying the new user table or an error message
        """
        try:
            message = sql_delete_user(str(ctx.author), display_name, self.cursor, self.cnx)
        except AdminPermissionError:
            await ctx.send("Permission Error encountered.  Either you are not an admin or are attempting to delete an "
                           "admin.")
        except UserNotFoundError:
            await ctx.send("Error: attempting to delete a user that does not exist.")
        else:
            await ctx.send(message)

    @commands.command()
    async def set_email(self, ctx, display_name, email):
        """
        Update a user's email
        :param display_name: display name of user
        :param email: new email for user
        :return: a message displaying the new user table or an error message
        """
        try:
            message = sql_set_email(str(ctx.author), display_name, email, self.cursor, self.cnx)
        except AdminPermissionError:
            await ctx.send("Permission Error encountered.  You do not have permission to edit the database")
        except UserNotFoundError:
            await ctx.send("Error: you are attempting to modify a user that does not exist.")
        else:
            await ctx.send(message)

    @commands.command()
    async def set_admin_status(self, ctx, display_name, status):
        """
        Update a user's admin status
        :param display_name: display name of user to be updated
        :param status: TRUE|FALSE
        :return: the updated user table or an error message
        """
        try:
            message = sql_set_admin_status(str(ctx.author), display_name, status, self.cursor, self.cnx)
        except AdminPermissionError:
            await ctx.send("Permission Error encountered.  You do not have permission to edit the database")
        except UserNotFoundError:
            await ctx.send("Error: you are attempting to modify a user that does not exist.")
        except ResponseError:
            await ctx.send("Error: please supply either TRUE or FALSE for new admin status")
        else:
            await ctx.send(message)

    @commands.command()
    async def query_user(self, ctx, user):
        """
        Get information about users
        :param user: ALL|DISPLAY_NAME
        :return: result of query
        """
        await ctx.send(sql_query_user(user, self.cursor))


# SQL FUNCTIONS #


def sql_query_user(argument, cursor):
    """
    Query information from the user table.
    :param argument: either ALL (for a select * from user query) or a display name (for getting information about a
    specific user).
    :param cursor: cursor to execute queries
    :return: The result of the select statement
    """
    if argument.upper() == 'ALL':
        cursor.execute('select * from user')
    else:
        cursor.execute('select * from user where display_name = %s', (argument,))

    return cursor.fetchall()


def sql_delete_user(auth_user, display_name, cursor, cnx):
    """
    Delete a row from the user table based on display name.
    :param auth_user: user who is authorizing the delete
    :param display_name: display name of the user to be deleted
    :param cursor: cursor object for executing query
    :param cnx: connection object for committing changes
    :return: the new table after deletion or an error flag
    """
    check_admin_status(auth_user, True, cursor)  # see if the authorizing user is an admin
    check_admin_status(display_name, False, cursor)  # see if the user to be deleted is an admin

    if len(sql_query_user(display_name, cursor)) == 0:
        raise UserNotFoundError()

    cursor.execute('delete from user where display_name = %s', (display_name,))  # execute deletion query
    cnx.commit()  # commit changes to database
    cursor.execute('select * from user')  # get new user table
    return cursor.fetchall()


def sql_add_user(auth_user, user_id, display_name, email, is_admin, cursor, cnx):
    """
    Add a user to the user table.
    :param auth_user: user authorizing add
    :param user_id: numeric id of user
    :param display_name: display name of user
    :param email: email of user
    :param is_admin: admin status of new user
    :param cursor: cursor for executing query
    :param cnx: connection object for committing change
    :return: the new table after insertion or an error flag
    """
    check_admin_status(auth_user, True, cursor)  # see if the authorizing user is an admin

    if len(sql_query_user(display_name, cursor)) > 0:
        raise ExistingUserError()

    cursor.execute('insert into user '
                   '(user_id, display_name, e_mail, admin) '
                   'values (%s, %s, %s, %s)', (user_id, display_name, email, is_admin))
    cnx.commit()  # commit changes to database

    cursor.execute('select * from user where display_name = %s', (display_name,))  # get new user table
    return cursor.fetchall()


def sql_set_email(auth_user, display_name, email, cursor, cnx):
    """
    Update the email associated with a user.
    :param auth_user: user authorizing change
    :param display_name: display name of user whose email will be changed
    :param email: new email for user
    :param cursor: cursor object to execute query
    :param cnx: connection object to commit changes
    :return: the new table after updating the user table
    """
    check_admin_status(auth_user, True, cursor)  # see if the authorizing user is an admin

    if len(sql_query_user(display_name, cursor)) == 0:
        raise UserNotFoundError()

    cursor.execute('update user '
                   'set e_mail = %s '
                   'where display_name = %s', (email, display_name))  # change the user table with new email
    cnx.commit()  # commit changes to user table
    cursor.execute('select * from user')  # get new user table
    return cursor.fetchall()


def sql_set_admin_status(auth_user, display_name, new_status, cursor, cnx):
    """
    Update the admin status associated with a user.
    :param auth_user: user authorizing change
    :param display_name: display name of user whose admin status will be changed
    :param new_status: true or false depending on admin status being set
    :param cursor: cursor object to execute query
    :param cnx: connection object to commit changes
    :return: the new table after updating the user table
    """
    check_admin_status(auth_user, True, cursor)  # see if the authorizing user is an admin

    if len(sql_query_user(display_name, cursor)) == 0:
        raise UserNotFoundError()

    if not (new_status.lower() == 'true' or new_status.lower() == 'false'):  # check for valid response
        raise ResponseError()

    cursor.execute('update user '
                   'set admin = %s '
                   'where display_name = %s', (1 if new_status == "true" else 0, display_name))
    cnx.commit()  # commit changes to user table
    cursor.execute('select * from user')  # get new user table
    return cursor.fetchall()


# ERRORS #

class Error(Exception):
    """Base class for exceptions in this module."""


class UserNotFoundError(Error):
    """User not found in database."""


class ResponseError(Error):
    """Invalid response or argument supplied."""


class ExistingUserError(Error):
    """Trying to create a user that already exists"""
