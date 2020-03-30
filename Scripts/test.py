import discord
import mysql.connector
import configparser
from LFJ import LFJ


def main():
    config = configparser.ConfigParser()  # read and parse the config file
    config.read(r'../configuration.conf')

    username = config['Database']['username']  # get details for signing in to database
    password = config['Database']['password']
    host = config['Database']['host']
    database = config['Database']['database']

    token = config['Discord']['token']  # get the bot's unique token for sign-in
    event_channel_name = config['Discord']['events_channel']  # text name of the event channel

    try:  # try connecting to the database
        cnx = mysql.connector.connect(user=username,
                                      password=password,
                                      host=host,
                                      database=database)
    except mysql.connector.Error:  # catch connection errors
        return 1
    else:  # if successful in connecting, create a cursor object
        cursor = cnx.cursor()

    client = LFJ(command_prefix='$', case_insensitive=True, event_channel=event_channel_name, cursor=cursor, cnx=cnx)
    client.add_command(LFJ.query_user)
    client.add_command(LFJ.add_user)
    client.add_command(LFJ.delete_user)
    client.add_command(LFJ.exit)
    client.run(token)


if __name__ == '__main__':
    main()
