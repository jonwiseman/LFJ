import random
import re
import time
from datetime import date

import discord
from discord.ext import commands

from backend.lib.game_queries import get_game_id
from backend.lib.helper_commands import check_admin_status, get_id_from_name, \
    get_id_from_title, get_game_name, AdminPermissionError, GameNotFoundError, check_event_exists, \
    InvalidEventTitleError
from mysql.connector.errors import IntegrityError
from backend.lib.user_queries import UserNotFoundError


class EventQueries(commands.Cog):
    def __init__(self, bot, cursor, cnx, event_channel_id):
        self.bot = bot
        self.cursor = cursor
        self.cnx = cnx
        self.event_channel_id = event_channel_id

    @commands.command()
    async def create_event(self, ctx, event_title, event_date, game_name, team_size):
        """
        Create new event
        :param event_title: title of event
        :param event_date: date of event (formatted DD/MM/YYYY)
        :param game_name: title of game to be played
        :param team_size: size of individual teams
        :return: new event table or error message
        """
        try:
            game_id = get_game_id(game_name, self.cursor)
            check_date_format(event_date)
            data_insert = {  # prepare data insert
                'event_id': -1,
                'date': date.fromtimestamp(int(time.mktime(time.strptime(event_date, '%m/%d/%Y')))),  # create date
                'game_id': game_id,  # get game's ID number
                'title': event_title,  # event's title
                'team_size': team_size, # individual team size
            }

            sql_create_event(data_insert, self.cursor, self.cnx)

            team_size = int(data_insert['team_size'])
            teams = create_blank_teams(team_size)

            embed = create_embed_message(data_insert['title'], data_insert['date'],
                                         get_game_name(data_insert['game_id'], self.cursor),
                                         teams, ctx)  # Created embeded message
        except DateFormatError:
            await ctx.send("Error: your date is invalid.  Please use MM/DD/YYYY format")
        except GameNotFoundError:
            await ctx.send("Error: trying to create an event for a game that does not exist")
        except ExistingEventError:
            await ctx.send("Error: event with this title already exists")
        except IntegrityError:
            await ctx.send("Error: this event already exists")
        except TeamSizeError:
            await ctx.send("Error: team size must be above 0")
        else:
            event_channel = self.bot.get_channel(self.event_channel_id)
            msg = await event_channel.send(embed=embed)
            sql_update_event_id(msg.id, event_title, self.cursor, self.cnx) # Set event_id in database
            await msg.add_reaction('☑')   # Add accept emoji to message
            await msg.add_reaction('🇽')    # Add decline emoji to message

            await ctx.send("Successfully created event " + event_title + "!")

    @commands.command()
    async def delete_event(self, ctx, event_title):
        """
        Delete an event
        :param event_title: title of event
        :return: new event table or error message
        """

        try:
            event_id = get_id_from_title(event_title, self.cursor)
            sql_delete_event(ctx.author.id, event_id, self.cursor, self.cnx)
        except AdminPermissionError:
            await ctx.send("Permission error: only admins may delete events")
        except InvalidEventTitleError:
            await ctx.send("Error: trying to delete an event that does not exist")
        else:
            sql_delete_all_registrations(event_id, self.cursor, self.cnx)   # Remove all registrations for event
            event_channel = self.bot.get_channel(self.event_channel_id)     # Get event channel
            msg = await event_channel.fetch_message(event_id)       # Get event message
            await msg.delete()

            await ctx.send("Successfully deleted event " + event_title + "!")

    @commands.command()
    async def get_events(self, ctx, past=True):
        """
        Get all events
        :return: list of all scheduled events
        """
        await ctx.send(sql_get_events(self.cursor, past))

    @commands.command()
    async def sort_teams(self, ctx, event_title, sort_type):
        """
        Sorts event teams with given sort type
        :param ctx:
        :param event_title: title of event to sort
        :param sort_type: type of sort to use
        :return: void
        """
        sort_type = sort_type.lower()
        try:
            event_id = get_id_from_title(event_title, self.cursor)

            event_channel = self.bot.get_channel(self.event_channel_id)  # Get event channel
            msg = await event_channel.fetch_message(event_id)  # Get event message

            team_size = sql_get_team_size(event_id, self.cursor)  # Get size of teams from event
            teams = get_teams_from_embed(msg.embeds[0], team_size)  # Get teams of event

            if sort_type == 'random':
                random.shuffle(teams[0])
                random.shuffle(teams[1])

            teams[0] = rebase_team(teams[0], team_size)    # Order team 0
            teams[1] = rebase_team(teams[1], team_size)    # Order team 1
            embed = modify_embed_message_teams(msg.embeds[0], teams)
            await msg.edit(embed=embed)
            await ctx.send("Successfully sorted teams in event " + event_title + " with shuffle type " + sort_type + "!")

        except InvalidEventTitleError:
            await ctx.send("Error: trying to sort an event that does not exist")

    @commands.command()
    async def query_event(self, ctx, event_name):
        """
        Inspect an event
        :param ctx: command parameter
        :param event_name: event's title
        :return: information about that event
        """
        await ctx.send(sql_query_event(event_name, self.cursor))


def check_date_format(date_string):
    if re.search(r'[0-9]+/[0-9]+/\d{4}\b', date_string) is None:
        raise DateFormatError


def sql_create_event(data_insert, cursor, cnx):
    """
    Create a new event row in the event table.
    :param data_insert: prepared data insert (event's id, event's date, game's name, event's title)
    :param cursor: MySQL cursor object for executing command and fetching result
    :param cnx: MySQL connection for verifying changes
    :return: new event table after update
    """
    try:
        get_id_from_title(data_insert['title'], cursor)
    except InvalidEventTitleError:
        pass
    else:
        raise ExistingEventError

    if int(data_insert['team_size']) <= 0:
        raise TeamSizeError

    cursor.execute('insert into event '
                   '(event_id, date, game_id, title, team_size) '
                   'values (%(event_id)s, %(date)s, %(game_id)s, '
                   '%(title)s, %(team_size)s)', data_insert)        # add new event
    cnx.commit()  # commit changes to database

    cursor.execute('select * from event where title = %s', (data_insert['title'],))

    return cursor.fetchall()    # return embed message to send via events channel


def sql_update_event_id(event_id, title, cursor, cnx):
    cursor.execute('update event '
                   'set event_id = %s '
                   'where title = %s', (event_id, title))
    cnx.commit()  # commit changes to user table


def sql_delete_event(auth_user, event_id, cursor, cnx):
    """
    Delete an event based on its title.
    :param auth_user: user requesting the delete (must be an admin to delete events)
    :param event_id: id of the event to be deleted
    :param cursor: cursor object for executing command
    :param cnx: connection object for verifying change
    :return: new event table after deletion
    """
    check_admin_status(auth_user, True, cursor)  # see if the authorizing user is an admin

    cursor.execute('delete from event where event_id = %s', (event_id, ))  # execute deletion query
    cnx.commit()  # commit changes to database

    cursor.execute('select * from event where event_id = %s', (event_id,))
    return cursor.fetchall()


def sql_get_events(cursor, include_past = True):
    """
    Get all events in the event table
    :param cursor: MySQL cursor object for executing command and fetching results
    :return: all events in the event table
    """
    command =  'select event_id, DATE_FORMAT(event.date,"%M %d %Y"), event.title, '\
               'game.name from event inner join game on event.game_id = game.game_id'
    if not include_past:
        command += 'where event.date >= CURDATE()'
    cursor.execute(command)
    event_list = '\n'.join(['\t'.join([str(e) for e in lne]) for lne in cursor.fetchall()])
    return 'Event ID\tDate\tEvent Title\tGame\n' + event_list


def sql_create_registration(event_id, user, cursor, cnx):
    """
    Register user for event based on title
    :param event_id: event id to create registration for
    :param user: the user to register for
    :param cursor: cursor object for executing command
    :param cnx: connection object for verifying change
    :return: count of users registered for the event
    """

    user_id = get_id_from_name(user, cursor)
    if user_id == -1:
        raise UserNotFoundError

    cursor.execute('select user_id from registration where user_id = %s and event_id = %s', (user_id, event_id))
    result = cursor.fetchall()

    if len(result) != 0:  # user already registered for event
        raise ExistingRegistrationError

    cursor.execute('insert into registration '
                   '(user_id, event_id) '
                   'values (%s, %s)', (user_id, event_id,))  # add new event
    cnx.commit()  # commit changes to database
    cursor.execute('select count(*) from registration where event_id = %s', (event_id,))        # Get registration count
    result = cursor.fetchall()

    return result


def sql_delete_registration(event_id, user, cursor, cnx):
    """
    Delete user registration for event based on title
    :param event_id: id of the event to delete registration for
    :param user: the user to delete registration for
    :param cursor: cursor object for executing command
    :param cnx: connection object for verifying change
    :return: count of users registered for the event
    """
    user_id = get_id_from_name(user, cursor)
    if user_id == -1:
        raise UserNotFoundError

    cursor.execute('delete from registration where '
                   'user_id = %s and event_id = %s', (user_id, event_id))  # delete user registration
    cnx.commit()    # commit changes to database
    cursor.execute('select count(*) from registration where event_id = %s', (event_id,))  # get count of registered user

    return cursor.fetchall()


def sql_delete_all_registrations(event_id, cursor, cnx):

    cursor.execute('delete from registration where '
                   'event_id = %s', (event_id,))
    cnx.commit()    # commit changes to database


def sql_get_team_size(event_id, cursor):
    """
    Gets the team size from event id
    :param event_id: event id to get team size for
    :param cursor: cursor object for executing command
    :return: team size of event
    """
    cursor.execute('select team_size from event where event_id = %s', (event_id,))
    result = cursor.fetchall()

    if len(result) == 0:  # event not found
        return -1

    return result[0][0]  # return event id


def sql_query_event(event_title, cursor):
    if event_title == "ALL":
        return sql_get_events(cursor)
    elif event_title == "FUTURE":
        return sql_get_events(cursor, False)
    try:
        event_id = get_id_from_title(event_title,cursor)
    except InvalidEventTitleError:
        return "Invalid Event Title"
    else:
        cursor.execute('select * from event where event_id = %s', (event_id,))
        return cursor.fetchall()


# TEAMS AND EMBEDED MESSAGES #


def create_embed_message(title, game_date, game_name, teams, ctx):
    """
    Creates an embeded message to send in Discord
    :param title: game title from event
    :param game_date: game date from event
    :param game_name: game name from event (convert from game_id first)
    :param teams: teams for event
    :param ctx: ctx for mess
    :return: embeded message ready to be sent in Discord containing event details
    """

    embed = discord.Embed(title="--------------------------------------------------\n" +
                                "Title: " + title + "\n" +
                                "Date: " + game_date.strftime('%m/%d/%y') + "\n" +
                                "Game: " + game_name + "\n" +
                                "--------------------------------------------------",
                          description="`Use reactions to join or leave the event`", color=0x0e4d98)
    embed.add_field(name="Team 1", value=convert_team_to_text(teams[0]), inline=True)
    embed.add_field(name="Team 2", value=convert_team_to_text(teams[1]), inline=True)

    return embed


def modify_embed_message_teams(embed, teams):
    """
    Modifies an embeded message to send in Discord
    :param embed: embeded message to modify
    :param teams: teams to include in embeded message
    :return: embeded message ready to be sent in Discord containing event details
    """
    embed.clear_fields()
    embed.add_field(name="Team 1", value=convert_team_to_text(teams[0]), inline=True)
    embed.add_field(name="Team 2", value=convert_team_to_text(teams[1]), inline=True)

    return embed


def create_blank_teams(team_size):
    """
    Creates a set of 2 blank teams
    :param team_size: size of team to be created
    :return: blank team array of size team_size
    """
    teams = [['-----'] * team_size] * 2

    return teams


def rebase_team(team, team_size):
    """
    Rebases player formatting so empty positions are at the end of the team
    :param team: team array to rebase
    :param team_size: total size of team to rebase
    :return: rebased team array
    """

    for i in range(team_size):
        if team[i] == '-----':  # If empty player position
            for j in range(team_size - i):  # Loop through remaining players
                display_name = team[i + j]
                if display_name != '-----':
                    team = remove_player_from_team(team, team_size, display_name, 0)
                    team[i + j - 1] = display_name

    return team


def add_player_to_team(team, display_name):
    """
    Adds a player to a team
    :param team: team array to add player to
    :param display_name: display_name of player to be added to team
    :return: team array if successful, -1 if unsuccessful (full team)
    """
    count = 0
    for player in team:
        if player == '-----':
            team[count] = display_name
            return team
        count += 1

    return -1


def remove_player_from_team(team, team_size, display_name, rebase):
    """
        Removes a player from a team
        :param team: team array to remove player from
        :param team_size: total size of team
        :param display_name: display name of player to be removed from a team
        :param rebase: 1 if we want to rebase teams after removing player, 0 if we don't
        :return: team array
        """
    count = 0
    for player in team:
        if player == display_name:
            team[count] = '-----'

            if rebase == 1:
                return rebase_team(team, team_size)

            return team
        count += 1

    return team


def is_player_on_team(team, display_name):
    """
    Gets if player is on a team or not
    :param team: team array to check if player is in
    :param display_name: display name of player to check if they belong to a team
    :return: 1 if player is on team, -1 if player isn't on team
    """
    for player in team:
        if player == display_name:
            return 1

    return -1


def get_team_player_count(team):
    """
    Gets the count of players in a given team
    :param team: team to get count for
    :return: count of players in team
    """
    count = 0
    for player in team:
        if player != '-----':
            count += 1

    return count


def convert_team_to_text(team):
    """
    Converts a team to text sendable in Discord
    :param team: team array to be converted to message text
    :return: text able to be messaged in Discord with team players
    """
    team_text = ''
    for player in team:
        team_text += player + "\n"

    return team_text


def get_teams_from_embed(embed, team_size):
    """
    Gets teams from embeded message
    :param embed: embeded message to decode teams from
    :param team_size: team size for event
    :return: two lists for Team 1 and Team 2 containing display_names for registered players
    """
    teams = create_blank_teams(team_size)  # Blank team arrays for Team 1 and Team 2
    for field in embed.fields:  # Only sets values for certain Embed values sent from bot
        if field.name == 'Team 1':
            teams[0] = str(field.value).split('\n')
        elif field.name == 'Team 2':
            teams[1] = str(field.value).split('\n')

    return teams    # Return team arrays


# ERRORS #


class Error(Exception):
    """Base class for exceptions in this module."""


class ExistingEventError(Error):
    """Trying to create an event that already exists."""


class ExistingRegistrationError(Error):
    """Trying to register for an event a player already belongs to."""


class EventNotFoundError(Error):
    """Trying to register for or change an event that does not exist."""


class DateFormatError(Error):
    """User supplied incorrectly formatted date"""


class TeamSizeError(Error):
    """User supplied incorrect team size (team_size <= 0)"""


class TeamFullError(Error):
    """Event team is already full"""
