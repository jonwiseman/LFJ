import re
import time
from datetime import date

import discord
from discord.ext import commands
from backend.lib.game_queries import get_game_id
from backend.lib.helper_commands import check_admin_status, get_id_from_name, get_name_from_id, \
    get_id_from_title, get_game_name, AdminPermissionError, GameNotFoundError
from mysql.connector.errors import IntegrityError


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
        #param ctx:
        :param event_title: title of event
        :param event_date: date of event (formatted DD/MM/YYYY)
        :param game_name: title of game to be played\
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

            message = sql_create_event(data_insert, self.cursor, self.cnx)
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
            msg = await event_channel.send(embed=message)
            sql_update_event_id(msg.id, event_title, self.cursor, self.cnx)

    @commands.command()
    async def delete_event(self, ctx, title):
        """
        Delete an event
        :param ctx:
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
        :param ctx:
        :return: list of all scheduled events
        """
        await ctx.send(sql_get_events(self.cursor))

    @commands.command()
    async def create_registration(self, ctx, event_title):
        """
        Register for an event
        :param ctx:
        :param event_title: event's title
        :return: new count of event registrations
        """
        event_id = get_id_from_title(event_title, self.cursor)
        if event_id == -1:
            await ctx.send("Error: no event with name \'" + event_title + "\' found")
            return  # If no event found, return with error

        reply = sql_create_registration(str(event_id), str(ctx.author), self.cursor, self.cnx)

        if "Error" not in reply:
            event_channel = self.bot.get_channel(self.event_channel_id) # Get event channel
            msg = await event_channel.fetch_message(event_id)   # Get event message

            team_size = sql_get_team_size(event_id, self.cursor)    # Get size of teams from event
            teams = get_teams_from_embed(msg.embeds[0], team_size)  # Get teams of event

            # Place player in team, if error we return
            if get_team_player_count(teams[0]) <= get_team_player_count(teams[1]):
                teams[0] = add_player_to_team(teams[0], str(ctx.author))
                if teams[0] == -1:
                    await ctx.send("Error: can't add user to team, teams are full")
                    return
            else:
                teams[1] = add_player_to_team(teams[1], ctx.author)

            # Update teams in event channel
            embed = modify_embed_message_teams(msg.embeds[0], teams)
            await msg.edit(embed=embed)

        await ctx.send(reply)   # Base error case for command

    @commands.command()
    async def delete_registration(self, ctx, event_name):
        """
        Cancel a registration
        :param ctx:
        :param event_name: name of event to cancel registration for
        :return: new count of event registrations
        """
        await ctx.send(sql_delete_registration(event_name, str(ctx.author), self.cursor, self.cnx))

    @commands.command()
    async def query_event(self, ctx, event_name):
        """
        Inspect an event
        :param ctx:
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
    if len(sql_query_event(data_insert['title'], cursor)) > 0:
        raise ExistingEventError

    if int(data_insert['team_size']) <= 0:
        raise TeamSizeError

    team_size = int(data_insert['team_size'])
    teams = create_blank_teams(team_size)

    embed = create_embed_message(data_insert['title'], data_insert['date'],
                                 get_game_name(data_insert['game_id'], cursor), teams) # Created embeded message

    cursor.execute('insert into event '
                   '(event_id, date, game_id, title, team_size) '
                   'values (%(event_id)s, %(date)s, %(game_id)s, %(title)s, %(team_size)s)', data_insert)    # add new event
    cnx.commit()  # commit changes to database

    return embed    # return embed message to send via events channel


def sql_update_event_id(event_id, title, cursor, cnx):
    cursor.execute('update event '
                   'set event_id = %s '
                   'where title = %s', (event_id, title))
    cnx.commit()  # commit changes to user table


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
        return "Error: unable to locate user in database"

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
    user_id = get_id_from_name(user, cursor)
    if user_id == -1:
        return -1

    event_id = get_id_from_title(title, cursor)
    if event_id == -1:
        return -1  # If no event found, return error

    cursor.execute('delete from registration where '
                   'user_id = %s and event_id = %s', (user_id, event_id,))  # delete user registration
    cnx.commit()  # commit changes to database
    cursor.execute('select count(*) from registration where event_id = %s', (event_id,))  # get count of registered user
    return cursor.fetchall()


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


def update_event_registration(event_id, cursor, cnx):
    cursor.execute('select user_id from registration where event_id = %s', (event_id,)) # Get user_ids
    result = cursor.fetchall()

    display_names = []
    for user_id in result:
        display_names.append(get_name_from_id(user_id, cursor)) # Places all display_names in list

    #embed = discord.Embed.from_data(embedFromMessage)


def sql_query_event(title, cursor):
    cursor.execute('select * from event where title = %s', (title,))
    return cursor.fetchall()


# TEAMS AND EMBEDED MESSAGES #


def create_embed_message(title, game_date, game_name, teams):
    """
    Creates an embeded message to send in Discord
    :param title: game title from event
    :param game_date: game date from event
    :param game_name: game name from event (convert from game_id first)
    :param teams: teams for event
    :return: embeded message ready to be sent in Discord containing event details
    """
    embed = discord.Embed(title="--------------------------------------------------\n" +
                                "Title: " + title + "\n" +
                                "Date: " + game_date.strftime('%m/%d/%y') + "\n" +
                                "Game: " + game_name + "\n" +
                                "--------------------------------------------------"
                          , description="Desc", color=0x0e4d98)
    embed.add_field(name="Team 1", value=convert_team_to_text(teams[0]), inline=True)
    embed.add_field(name="Team 2", value=convert_team_to_text(teams[1]), inline=True)

    return embed


def modify_embed_message_teams(embed, teams):
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


class EventNotFoundError(Error):
    """Trying to register for or change an event that does not exist."""


class DateFormatError(Error):
    """User supplied incorrectly formatted date"""


class TeamSizeError(Error):
    """User supplied incorrect team size (team_size <= 0)"""


class TeamFullError(Error):
    """Event team is already full"""
