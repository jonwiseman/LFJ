import configparser
from discord.ext import commands
import mysql.connector
from user_queries import UserQueries
from game_queries import GameQueries


def main():
    event_channel = None
    event_created = True

    config = configparser.ConfigParser()        # read and parse configuration file
    config.read(r'../configuration.conf')

    token = config['Discord']['token']      # get the bot's unique token for sign-in
    event_channel_name = config['Discord']['events_channel']     # text name of the event channel

    username = config['Database']['username']       # get details for signing in to database
    password = config['Database']['password']
    host = config['Database']['host']
    database = config['Database']['database']

    cnx = mysql.connector.connect(user=username,
                                  password=password,
                                  host=host,
                                  database=database)        # connect to the database
    cursor = cnx.cursor()       # create cursor object for executing queries

    client = commands.Bot(command_prefix='$', case_insensitive=True)       # create the bot client

    # BOT EVENTS #

    @client.event
    async def on_ready():
        """
        on_ready() is called when the bot is signed in to Discord and ready to send/receive event notifications
        :return: none; print ready status to console
        """
        global event_channel
        global event_created
        print('We have logged in as {0.user}'.format(client))
        for channel in client.get_all_channels():
            if str(channel.name) == event_channel_name:
                event_channel = channel

        if event_channel is None:  # server does not have a dedicated events channel
            print("ERROR: Could not find event channel")
            await client.logout()

        event_created = True

    # EXIT COMMAND #

    @client.command(name='exit')
    async def bot_exit(ctx):
        """
        Prompt bot to logout
        :return: none
        """
        cursor.close()
        cnx.close()
        await client.logout()  # log the bot out

    # RUN THE BOT #
    client.add_cog(UserQueries(client, cursor, cnx))
    client.add_cog(GameQueries(client, cursor, cnx))
    client.run(token)


if __name__ == '__main__':
    main()
