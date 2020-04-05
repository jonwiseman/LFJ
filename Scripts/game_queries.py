from discord.ext import commands
from mysql.connector.errors import IntegrityError
from helper_commands import check_admin_status, AdminPermissionError


class GameQueries(commands.Cog):
    def __init__(self, bot, cursor, cnx):
        self.bot = bot
        self.cursor = cursor
        self.cnx = cnx

    @commands.command()
    async def add_game(self, ctx, game_id, name):
        """
        Add a game to backend
        :param game_id: numeric ID of game
        :param name: title of game
        :return: new game table or error message
        """
        try:
            message = sql_add_game(str(ctx.author), game_id, name, self.cursor, self.cnx)
        except AdminPermissionError:
            await ctx.send("Permission error encountered: only admins can add games")
        except ExistingGameError:
            await ctx.send("Error: this game already exists")
        except IntegrityError:
            await ctx.send("Error: a game already exists with this ID.  Please choose another.")
        else:
            await ctx.send(message)

    @commands.command()
    async def delete_game(self, ctx, name):
        """
        Delete a game from backend
        :param name: title of game
        :return: new game table or error message
        """
        try:
            message = sql_delete_game(str(ctx.author), name, self.cursor, self.cnx)
        except GameNotFoundError:
            await ctx.send("Error: attempting to delete a game that does not exist")
        else:
            await ctx.send(message)

    @commands.command()
    async def edit_name(self, ctx, old_name, new_name):
        """
        Edit game's title
        :param old_name: previous game title
        :param new_name: new game title
        :return: new game table or error message
        """
        try:
            message = sql_edit_name(str(ctx.author), old_name, new_name, self.cursor, self.cnx)
        except GameNotFoundError:
            await ctx.send("Error: trying to update a game that does not exist")
        except ExistingGameError:
            await ctx.send("Error: a game already exists with this name")
        else:
            await ctx.send(message)

    @commands.command()
    async def edit_id(self, ctx, name, game_id):
        """
        Edit game's ID
        :param name: game's title
        :param game_id: new game ID
        :return: new game table or error message
        """
        try:
            message = sql_edit_id(str(ctx.author), name, game_id, self.cursor, self.cnx)
        except GameNotFoundError:
            await ctx.send("Error: trying to update a game that does not exist")
        except IntegrityError:
            await ctx.send("Error: game with this ID already exists.  Please choose another")
        else:
            await ctx.send(message)

    @commands.command()
    async def query_game(self, ctx, name):
        """
        Inspect a game
        :param name: game's title
        :return: result of query
        """
        await ctx.send(sql_query_game(name, self.cursor))

    @commands.command()
    async def list_games(self, ctx):
        """
        List all games
        :return: list of all games
        """
        await ctx.send(sql_list_games(self.cursor))

    @commands.command()
    async def create_membership(self, ctx, game_name, skill_level):
        """
        Create a game membership
        :param game_name: game's title
        :param skill_level: player's skill level
        :return: confirmation or error message
        """
        await ctx.send(sql_set_membership(str(ctx.author), game_name, skill_level, self.cursor, self.cnx))

    @commands.command()
    async def delete_membership(self, ctx, display_name, game_name):
        """
        Remove a user's game membership
        :param display_name: user's display name
        :param game_name: game's title
        :return: confirmation or error message
        """
        await ctx.send(sql_delete_membership(display_name, game_name, self.cursor, self.cnx))


def sql_add_game(auth_user, game_id, name, cursor, cnx):
    check_admin_status(auth_user, True, cursor)  # see if the authorizing user is an admin
    if len(sql_query_game(name, cursor)) > 0:
        raise ExistingGameError

    cursor.execute('insert into game '
                   '(game_id, name) '
                   'values (%s, %s)', (game_id, name))  # add new user
    cnx.commit()  # commit changes to database

    cursor.execute('select * from game')  # get new user table
    return cursor.fetchall()


def sql_delete_game(auth_user, name, cursor, cnx):
    check_admin_status(auth_user, True, cursor)  # see if the authorizing user is an admin

    if len(sql_query_game(name, cursor)) == 0:
        raise GameNotFoundError

    cursor.execute('delete from game where name = %s', (name,))  # execute deletion query
    cnx.commit()  # commit changes to database
    cursor.execute('select * from game')  # get new user table
    return cursor.fetchall()


def sql_edit_name(auth_user, old_name, new_name, cursor, cnx):
    admin_status = check_admin_status(auth_user, True, cursor)  # see if the authorizing user is an admin

    if len(sql_query_game(old_name, cursor)) == 0:
        raise GameNotFoundError
    if len(sql_query_game(new_name, cursor)) > 0:
        raise ExistingGameError

    cursor.execute('update game '
                   'set name = %s '
                   'where name = %s', (new_name, old_name))  # change the game table with new email
    cnx.commit()  # commit changes to user table
    cursor.execute('select * from game')  # get new user table
    return cursor.fetchall()


def sql_edit_id(auth_user, name, game_id, cursor, cnx):
    check_admin_status(auth_user, True, cursor)  # see if the authorizing user is an admin

    if len(sql_query_game(name, cursor)) == 0:
        raise GameNotFoundError

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


def sql_query_game(argument, cursor):
    if argument.upper() == 'ALL':
        cursor.execute('select * from game')
        return cursor.fetchall()
    else:
        cursor.execute('select * from game where name = %s', (argument,))
        return cursor.fetchall()


def sql_set_membership(auth_user, game_name, skill_level, cursor, cnx):
    """
    Sets a users membership with a particular game
    :param auth_user: user authorizing change
    :param game_name: name of game user wants to set skill_level for
    :param skill_level: the level of skill the user holds in a game
    :param cursor: cursor object for executing queries
    :param cnx: connection object to commit changes
    :return: 1 if there is an error, response text if successful
    """
    user_id = get_user_id(auth_user, cursor)  # gets user_id from display_name

    if user_id == -1:  # user not found
        return 1

    game_id = get_game_id(game_name, cursor)  # gets game_id from game_name

    if game_id == -1:  # game not found
        return 1

    if check_membership(user_id, game_id, cursor) == -1:  # user does not hold membership of game
        cursor.execute('insert into membership '
                       '(user_id, game_id, skill_level) '
                       'values (%s, %s, %s)', (user_id, game_id, skill_level))
    else:
        cursor.execute('update membership '
                       'set skill_level = %s '
                       'where user_id = %s and game_id = %s',
                       (skill_level, user_id, game_id,))  # bug fixed Bowler 03/30/2020
    cnx.commit()  # commit changes to membership table

    return "Successfully updated your skill level to " + skill_level + " for " + game_id


def sql_delete_membership(auth_user, game_name, cursor, cnx):
    """
    Delete a users membership with a particular game
    :param auth_user: user authorizing change
    :param game_name: name of game user wants to set skill_level for
    :param cursor: cursor object for executing queries
    :param cnx: connection object to commit changes
    :return: 1 if there is an error, response text if successful
    """
    user_id = get_user_id(auth_user, cursor)  # gets user_id from display_name

    if user_id == -1:  # user not found
        return 1

    game_id = get_game_id(game_name, cursor)  # gets game_id from game_name

    if game_id == -1:  # game not found
        return 1

    if check_membership(user_id, game_id, cursor) == -1:  # user does not hold membership of game
        return 1
    else:
        cursor.execute('delete from membership '
                       'where user_id = %s and game_id = %s',
                       (user_id, game_id,))
    cnx.commit()  # commit changes to membership table

    return "Deleted " + auth_user + " from " + game_name


def get_game_id(game_name, cursor):
    """
    Gets a game id from game name
    :param game_name: name of a game to get id for
    :param cursor: cursor object for executing search query
    :return: -1 if game does not exist, game_id if game is found
    """
    cursor.execute('select game_id from game where name = %s', (game_name,))
    result = cursor.fetchall()

    if len(result) == 0:  # game not found
        raise GameNotFoundError

    return result[0][0]  # return game id


def check_membership(user_id, game_id, cursor):
    """
    Check to see if a given user has membership to a game
    :param user_id: user id to check
    :param game_id: game id to check
    :param cursor: cursor object for executing search query
    :return: -1 if membership does not exist, 1 if user has membership to given game
    """
    cursor.execute('select user_id from membership where user_id = %s and game_id = %s', (user_id, game_id))
    result = cursor.fetchall()

    if len(result) == 0:  # user not found
        return -1

    return result[0][0]  # return user id


def get_user_id(display_name, cursor):
    """
    Gets a user id from display name of a user
    :param display_name: display name of user whose id will be gotten
    :param cursor: cursor object for executing search query
    :return: -1 if user does not exist, user_id if user is found
    """
    cursor.execute('select user_id from user where display_name = %s', display_name)
    result = cursor.fetchall()

    if len(result) == 0:  # user not found
        return -1

    return result[0][0]  # return user id

# ERRORS #


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class ExistingGameError(Error):
    pass


class GameNotFoundError(Error):
    pass
