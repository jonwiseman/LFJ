import configparser
import mysql.connector
import discord
import re
import time
from datetime import date


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


def create_event(data_insert, cursor, cnx):
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


def delete_event(auth_user, title, cursor, cnx):
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


def qet_events(cursor):
    """
    Get all events in the event table
    :param cursor: MySQL cursor object for executing command and fetching results
    :return: all events in the event table
    """
    cursor.execute('select * from event')
    return cursor.fetchall()


def query_event(title, cursor):
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
