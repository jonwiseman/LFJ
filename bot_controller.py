import configparser
from discord.ext import commands
import mysql.connector
from backend.lib.user_queries import UserQueries
from backend.lib.game_queries import GameQueries
from backend.lib.event_queries import EventQueries
from backend.lib.helper_commands import HelperCommands


def main():
    config = configparser.ConfigParser()        # read and parse configuration file
    config.read(r'configuration.conf')

    token = config['Discord']['token']      # get the bot's unique token for sign-in
    event_channel_id = int(config['Discord']['event_channel_id'])     # id of the event channel
    command_prefix = config['Discord']['prefix']

    username = config['Database']['username']       # get details for signing in to database
    password = config['Database']['password']
    host = config['Database']['host']
    database = config['Database']['database']

    cnx = mysql.connector.connect(user=username,
                                  password=password,
                                  host=host,
                                  database=database)        # connect to the database
    cursor = cnx.cursor()       # create cursor object for executing queries

    client = commands.Bot(command_prefix=command_prefix, case_insensitive=True)       # create the bot client

    # BOT EVENTS #

    @client.event
    async def on_ready():
        """
        on_ready() is called when the bot is signed in to Discord and ready to send/receive event notifications
        :return: none; print ready status to console
        """
        print('We have logged in as {0.user}'.format(client))

    # RUN THE BOT #
    client.add_cog(HelperCommands(client, cursor, cnx))
    client.add_cog(UserQueries(client, cursor, cnx))
    client.add_cog(GameQueries(client, cursor, cnx))
    client.add_cog(EventQueries(client, cursor, cnx, event_channel_id))
    client.run(token)


if __name__ == '__main__':
    main()
