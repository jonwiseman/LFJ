from discord.ext import commands
from game_queries import get_game_id

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
        await ctx.send(sql_add_user(str(ctx.author), display_name.split('#')[1], display_name, email, admin,
                                    self.cursor, self.cnx))

    @commands.command()
    async def delete_user(self, ctx, display_name):
        """
        Delete a user from LFJ backend
        :param display_name: display name of user to be deleted
        :return:  a message displaying the new user table or an error message
        """
        await ctx.send(sql_delete_user(str(ctx.author), display_name, self.cursor, self.cnx))

    @commands.command()
    async def set_email(self, ctx, display_name, email):
        """
        Update a user's email
        :param display_name: display name of user
        :param email: new email for user
        :return: a message displaying the new user table or an error message
        """
        await ctx.send(sql_set_email(str(ctx.author), display_name, email, self.cursor, self.cnx))

    @commands.command()
    async def set_admin_status(self, ctx, display_name, status):
        """
        Update a user's admin status
        :param display_name: display name of user to be updated
        :param status: TRUE|FALSE
        :return: the updated user table or an error message
        """
        await ctx.send(sql_set_admin_status(str(ctx.author), display_name, status, self.cursor, self.cnx))

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
        return cursor.fetchall()
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
    admin_status = check_admin_status(auth_user, cursor)  # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

    delete_admin = check_admin_status(display_name, cursor)  # see if the user to be deleted is an admin
    if delete_admin == -1 or delete_admin == 1:  # trying to delete a non-existant user or another admin
        return 1

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
    admin_status = check_admin_status(auth_user, cursor)  # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

    cursor.execute('insert into user '
                   '(user_id, display_name, e_mail, admin) '
                   'values (%s, %s, %s, %s)', (user_id, display_name, email, is_admin))
    cnx.commit()  # commit changes to database

    cursor.execute('select * from user')  # get new user table
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
    admin_status = check_admin_status(auth_user, cursor)  # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

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
    admin_status = check_admin_status(auth_user, cursor)  # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

    if not (new_status == 'true' or new_status == 'false'):  # syntax for setting admin status is not true or false
        return 1

    cursor.execute('update user '
                   'set admin = %s '
                   'where display_name = %s', (1 if new_status == "true" else 0, display_name))
    cnx.commit()  # commit changes to user table
    cursor.execute('select * from user')  # get new user table
    return cursor.fetchall()


# HELPER FUNCTIONS #


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
