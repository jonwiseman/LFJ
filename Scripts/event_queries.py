import configparser
import mysql.connector
import discord
import re


def main(argc, argv):
    config = configparser.ConfigParser()  # read and parse the config file
    config.read(r'..\configuration.conf')

    username = config['Database']['username']  # get details for signing in to database
    password = config['Database']['password']
    host = config['Database']['host']
    database = config['Database']['database']

    try:        # try connecting to the database
        cnx = mysql.connector.connect(user=username,
                                      password=password,
                                      host=host,
                                      database=database)
    except mysql.connector.Error:       # catch connection errors
        return 1
    else:       # if successful in connecting, create a cursor object
        cursor = cnx.cursor()

    command = argv[0]       # get the command entered by the user

    if command == 'create_event':
        title, date, game = parse_creation_message(argv[1])
        if title == 1 or date == 1 or game == 1:
            return 1

        create_event()


def parse_creation_message(message):
    title = re.search('Title: [A-Z]+([_]*[A-Z]*)*', message).group(0).split(' ')[1]
    date = re.search('Date: [0-9]+/[0-9]+/[0-9][0-9][0-9][0-9]', message).group(0).split(' ')[1]
    game = re.search('Game: [A-Z]+', message).group(0).split(' ')[1]

    if title is None or date is None or game is None:
        return (1, 1, 1)
    else:
        return (title, date, game)


def create_event():
    pass


if __name__ == '__main__':
    main(0, [])
