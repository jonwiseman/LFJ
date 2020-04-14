import re
import time
from datetime import date
from discord.ext import commands
from backend.lib.game_queries import get_game_id
from backend.lib.helper_commands import check_admin_status, AdminPermissionError
from backend.lib.game_queries import GameNotFoundError
from mysql.connector.errors import IntegrityError


class EventQueries(commands.Cog):
    def __init__(self, bot, cursor, cnx):
        self.bot = bot
        self.cursor = cursor
        self.cnx = cnx

    @commands.command()
    async def create_event(self, ctx, event_title, event_date, game_name):
        """
        Create new event
        :param event_title: title of event
        :param event_date: date of event (formatted DD/MM/YYYY)
        :param game_name: title of game to be played
        :return: new event table or error message
        """
        try:
            game_id = get_game_id(game_name, self.cursor)
            check_date_format(event_date)
            data_insert = {  # prepare data insert
                'event_id': ctx.message.id % 2147483647,
                'date': date.fromtimestamp(int(time.mktime(time.strptime(event_date, '%m/%d/%Y')))),  # create date
                'game_id': game_id,  # get game's ID number
                'title': event_title,  # event's title
            }

            message = sql_create_event(data_insert, self.cursor, self.cnx)
        except DateFormatError:
            await ctx.send("Error: your date is invalid.  Please use MM/DD/YYYY format")
        except GameNotFoundError:
            await ctx.send("Error: trying to create an event for a game that does not exist")
        except ExistingEventError:
            await ctx.send("Error: event with this title already exists")
        except IntegrityError:
            await ctx.send("Error: this event already exists")
        else:
            await ctx.send(message)

    @commands.command()
    async def delete_event(self, ctx, title):
        """
        Delete an event
        :param title: title of event
        :return: new event table or error message
        """
        try:
            message = sql_delete_event(str(ctx.author), title, self.cursor, self.cnx)
        except AdminPermissionError:
            await ctx.send("Permission error: only admins may delete events")
        except EventNotFoundError:
            await ctx.send("Error: trying to remove an event that does not exist")
        else:
            await ctx.send(message)

    @commands.command()
    async def get_events(self, ctx):
        """
        Get all events
        :return: list of all scheduled events
        """
        await ctx.send(sql_get_events(self.cursor))

    @commands.command()
    async def create_registration(self, ctx, event_name):
        """
        Register for an event
        :param event_name: event's title
        :return: new count of event registrations
        """
        await ctx.send(sql_create_registration(event_name, str(ctx.author), self.cursor, self.cnx))

    @commands.command()
    async def delete_registration(self, ctx, event_name):
        """
        Cancel a registration
        :param event_name: name of event to cancel registration for
        :return: new count of event registrations
        """
        await ctx.send(sql_delete_registration(event_name, str(ctx.author), self.cursor, self.cnx))

    @commands.command()
    async def query_event(self, ctx, event_name):
        """
        Inspect an event
        :param event_name: event's title
        :return: information about that event
        """
        await ctx.send(sql_query_event(event_name, self.cursor))


def check_date_format(date_string):
    if re.search(r'[0-9]+/[0-9]+/\d{4}\b', date_string) is None:
        raise DateFormatError


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

    return title, date, game


def sql_create_event(data_insert, cursor, cnx):
    """
    Create a new event row in the event table.
    :param data_insert: prepared data insert (event's id, event's date, game's name, event's title)
    :param cursor: MySQL cursor object for executing command and fetching result
    :param cnx: MySQL connection for verifying changes
    :return: new event table after update
    """
    if len(sql_query_event(data_insert['title'], cursor)) > 0:
        raise ExistingEventError

    cursor.execute('insert into event '
                   '(event_id, date, game_id, title) '
                   'values (%(event_id)s, %(date)s, %(game_id)s, %(title)s)', data_insert)  # add new event
    cnx.commit()  # commit changes to database

    cursor.execute('select * from event where title = %s', (data_insert['title'],))  # get new event table

    return cursor.fetchall()


def sql_delete_event(auth_user, title, cursor, cnx):
    """
    Delete an event based on its title.
    :param auth_user: user requesting the delete (must be an admin to delete events)
    :param title: title of the event to be deleted
    :param cursor: cursor object for executing command
    :param cnx: connection object for verifying change
    :return: new event table after deletion
    """
    check_admin_status(auth_user, True, cursor)  # see if the authorizing user is an admin

    if len(sql_query_event(title, cursor)) == 0:
        raise EventNotFoundError

    cursor.execute('delete from event where title = %s', (title, ))  # execute deletion query
    cnx.commit()  # commit changes to database
    cursor.execute('select * from event')  # get new user table
    return cursor.fetchall()


def sql_get_events(cursor):
    """
    Get all events in the event table
    :param cursor: MySQL cursor object for executing command and fetching results
    :return: all events in the event table
    """
    cursor.execute(
        'select event_id, DATE_FORMAT(event.date,"%M %d %Y"), event.title, '
        'game.name from event inner join game on event.game_id = game.game_id'
        )
    event_list = '\n'.join(['\t'.join([str(e) for e in lne]) for lne in cursor.fetchall()])
    return 'Event ID\tDate\tEvent Title\tGame\n' + event_list


def sql_create_registration(title, user, cursor, cnx):
    """
    Register user for event based on title
    :param title: title of the event to register for
    :param user: the user to register for
    :param cursor: cursor object for executing command
    :param cnx: connection object for verifying change
    :return: count of users registered for the event
    """
    cursor.execute('select user_id from user where display_name = %s', (user,))
    result = cursor.fetchall()
    if len(result) == 0:  # user not found
        return -1
    user_id = result[0][0]

    cursor.execute('select event_id from event where title = %s', (title,))
    result = cursor.fetchall()
    if len(result) == 0:  # event not found
        return -1
    event_id = result[0][0]

    cursor.execute('insert into registration '
                   '(user_id, event_id) '
                   'values (%s, %s)', (user_id, event_id,))  # add new event
    cnx.commit()  # commit changes to database
    cursor.execute('select count(*) from registration where event_id = %s', (event_id,))        # Get registration count
    result = cursor.fetchall()
    print(result)
    return result


def sql_delete_registration(title, user, cursor, cnx):
    """
    Delete user registration for event based on title
    :param title: title of the event to delete registration for
    :param user: the user to delete registration for
    :param cursor: cursor object for executing command
    :param cnx: connection object for verifying change
    :return: count of users registered for the event
    """
    cursor.execute('select user_id from user where display_name = %s', (user,))
    result = cursor.fetchall()
    if len(result) == 0:  # user not found
        return -1
    user_id = result[0][0]

    cursor.execute('select event_id from event where title = %s', (title,))
    result = cursor.fetchall()
    if len(result) == 0:  # event not found
        return -1
    event_id = result[0][0]

    cursor.execute('delete from registration where '
                   'user_id = %s and event_id = %s', (user_id, event_id,))  # delete user registration
    cnx.commit()  # commit changes to database
    cursor.execute('select count(*) from registration where event_id = %s', (event_id,))  # get count of registered user
    return cursor.fetchall()


def sql_query_event(title, cursor):
    cursor.execute('select * from event where title = %s', (title,))
    return cursor.fetchall()


# ERRORS #


class Error(Exception):
    """Base class for exceptions in this module."""


class ExistingEventError(Error):
    """Trying to create an event that already exists."""


class EventNotFoundError(Error):
    """Trying to register for or change an event that does not exist."""


class DateFormatError(Error):
    """User supplied incorrectly formatted date"""
