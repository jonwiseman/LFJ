from discord.ext import commands


class GameQueries(commands.Cog):
    def __init__(self, bot, cursor, cnx):
        self.bot = bot
        self.cursor = cursor
        self.cnx = cnx

    @commands.command()
    async def add_game(self, ctx, game_id, name):
        await ctx.send(sql_add_game(str(ctx.author), game_id, name, self.cursor, self.cnx))

    @commands.command()
    async def delete_game(self, ctx, name):
        await ctx.send(sql_delete_game(str(ctx.author), name, self.cursor, self.cnx))

    @commands.command()
    async def edit_name(self, ctx, old_name, new_name):
        await ctx.send(sql_edit_name(str(ctx.author), old_name, new_name, self.cursor, self.cnx))

    @commands.command()
    async def edit_id(self, ctx, name, game_id):
        await ctx.send(sql_edit_id(str(ctx.author), name, game_id, self.cursor, self.cnx))

    @commands.command()
    async def query_game(self, ctx, name):
        await ctx.send(sql_query_game(name, self.cursor))

    @commands.command()
    async def list_games(self,ctx):
        await ctx.send(sql_list_games(self.cursor))


def sql_add_game(auth_user, game_id, name, cursor, cnx):
    admin_status = check_admin_status(auth_user, cursor)  # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

    cursor.execute('insert into game '
                   '(game_id, name) '
                   'values (%s, %s)', (game_id, name))  # add new user
    cnx.commit()  # commit changes to database

    cursor.execute('select * from game')  # get new user table
    return cursor.fetchall()


def sql_query_game(argument, cursor):
    if argument.upper() == 'ALL':
        cursor.execute('select * from game')
        return cursor.fetchall()
    else:
        cursor.execute('select * from game where name = %s', (argument,))
        return cursor.fetchall()


def sql_delete_game(auth_user, name, cursor, cnx):
    admin_status = check_admin_status(auth_user, cursor)  # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

    cursor.execute('delete from game where name = %s', (name,))  # execute deletion query
    cnx.commit()  # commit changes to database
    cursor.execute('select * from game')  # get new user table
    return cursor.fetchall()


def sql_edit_name(auth_user, old_name, new_name, cursor, cnx):
    admin_status = check_admin_status(auth_user, cursor)  # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

    cursor.execute('update game '
                   'set name = %s '
                   'where name = %s', (new_name, old_name))  # change the game table with new email
    cnx.commit()  # commit changes to user table
    cursor.execute('select * from game')  # get new user table
    return cursor.fetchall()


def sql_edit_id(auth_user, name, game_id, cursor, cnx):
    admin_status = check_admin_status(auth_user, cursor)  # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

    cursor.execute('update game '
                   'set game_id = %s '
                   'where name = %s', (game_id, name))  # change the game table with new email
    cnx.commit()  # commit changes to user table
    cursor.execute('select * from game')  # get new user table
    return cursor.fetchall()


def sql_list_games(cursor):
    cursor.execute('select game_id, name from game')
    result = cursor.fetchall()

    msg = 'ID\tName\n'
    for record in result:
        msg += '%d\t%s\n' % record
    return msg


def check_admin_status(display_name, cursor):
    """
    Check to see if a given user is an admin.  Only admins can change the database.
    :param display_name: display name of requesting user
    :param cursor: cursor object for executing search query
    :return: -1 if user does not exist, 0 if the user is not an admin, or 1 if the user is an admin
    """
    cursor.execute('select admin from user where display_name = %s', (display_name,))
    result = cursor.fetchall()

    if len(result) == 0:    # user not found
        return -1

    return result[0][0]     # return 0 or 1


def get_game_id(game_name, cursor):
    """
    Gets a game id from game name
    :param game_name: name of a game to get id for
    :param cursor: cursor object for executing search query
    :return: -1 if game does not exist, game_id if game is found
    """
    cursor.execute('select game_id from game where name = %s', game_name.lower())
    result = cursor.fetchall()

    if len(result) == 0:  # game not found
        return -1

    return result[0][0]  # return game id
