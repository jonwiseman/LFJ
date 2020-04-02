import configparser
from discord.ext import commands
import mysql.connector
import user_queries


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

    # BOT COMMANDS #

    @client.command()
    async def exit(ctx):
        cursor.close()
        cnx.close()
        await client.logout()  # log the bot out

    @client.command()
    async def add_user(ctx, display_name, email, admin):
        await ctx.send(user_queries.add_user(str(ctx.author), display_name.split('#')[1], display_name, email, admin,
                                             cursor, cnx))

    @client.command()
    async def delete_user(ctx, display_name):
        await ctx.send(user_queries.delete_user(str(ctx.author), display_name, cursor, cnx))

    @client.command()
    async def set_email(ctx, display_name, email):
        await ctx.send(user_queries.set_email(str(ctx.author), display_name, email, cursor, cnx))

    @client.command()
    async def set_admin_status(ctx, display_name, status):
        await ctx.send(user_queries.set_admin_status(str(ctx.author), display_name, status, cursor, cnx))

    @client.command()
    async def query_user(ctx, user):
        await ctx.send(user_queries.query_user(user, cursor))

    # RUN THE BOT #
    client.run(token)


if __name__ == '__main__':
    main()
