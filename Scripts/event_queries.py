import configparser
import mysql.connector
import discord
import re
import time
from datetime import date
from discord.ext import commands
from game_queries import get_game_id


class EventQueries(commands.Cog):
    def __init__(self, bot, cursor, cnx):
        self.bot = bot
        self.cursor = cursor
        self.cnx = cnx

    @commands.command()
    async def create_event(self, ctx, event_title, event_date, game_name):
        game_id = get_game_id(game_name,self.cursor)
        if game_id is None:
            return 1
        data_insert = {  # prepare data insert
            'event_id': 2,  #NOT SURE WHERE TO GET THIS FROM SEND HELP PLEASE
            'date': date.fromtimestamp(int(time.mktime(time.strptime(event_date, '%m/%d/%Y')))),  # create date
            'game_id': game_id,  # get game's ID number
            'title': event_title,  # event's title
        }
        await ctx.send(sql_create_event(data_insert, self.cursor, self.cnx))

    @commands.command()
    async def delete_event(self, ctx, title):
        await ctx.send(sql_delete_event(str(ctx.author), title, self.cursor, self.cnx))

    @commands.command()
    async def get_events(self, ctx):
        await ctx.send(sql_get_events(self.cursor))

    @commands.command()
    async def create_registration(self, ctx, event_name):
        await ctx.send(sql_create_registration(event_name, str(ctx.author), self.cursor, self.cnx))

    @commands.command()
    async def delete_registration(self, ctx, event_name):
        await ctx.send(sql_delete_registration(event_name, str(ctx.author), self.cursor, self.cnx))

    @commands.command()
    async def query_event(self, ctx,event_name):
        await ctx.send(sql_query_event(event_name, self.cursor))

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


def sql_create_event(data_insert, cursor, cnx):
    """
    Create a new event row in the event table.
    :param data_insert: prepared data insert (event's id, event's date, game's name, event's title)
    :param cursor: MySQL cursor object for executing command and fetching result
    :param cnx: MySQL connection for verifying changes
    :return: new event table after update
    """
    cursor.execute('insert into event '
                   '(event_id, date, game_id, title) '
                   'values (%(event_id)s, %(date)s, %(game_id)s, %(title)s)', data_insert)  # add new event
    cnx.commit()  # commit changes to database

    cursor.execute('select * from event')  # get new event table
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
    admin_status = check_admin_status(auth_user, cursor)  # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

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
    event_list = '\n'.join([ '\t'.join([str(e) for e in lne]) for lne in cursor.fetchall()])
    return 'Event ID\tDate\tEvent Title\tGame\n'+ event_list


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
    cursor.execute('select count(*) from registration where event_id = %s', (event_id,))  # get new user table
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
                   'user_id = %s and event_id = %s) ', (user_id, event_id,))  # delete user registration
    cnx.commit()  # commit changes to database
    cursor.execute('select count(*) from registration where event_id = %s', (event_id,))  # get count of registered user
    return cursor.fetchall()


def sql_query_event(title, cursor):
    cursor.execute('select * from event where title = %s', (title,))
    return cursor.fetchall()


def check_admin_status(display_name, cursor):
    """
    Check to see if a given user is an admin.  Only admins can change the database.
    :param display_name: display name of requesting user
    :param cursor: cursor object for executing search query
    :return: 0 if the user is not an admin (or does not exist) or 1 if the user is an admin
    """
    cursor.execute('select admin from user where display_name = %s', (display_name,))
    result = cursor.fetchall()

    if len(result) == 0:        # user not found
        return -1

    return result[0][0]     # return 0 or 1


if __name__ == '__main__':
    main(0, [])
