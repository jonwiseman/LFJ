import configparser
import discord
import user_queries
import event_queries
import game_queries


def main():
    commands = {        # list of commands available for bot to use
        'help': give_help,

        'add_user': user_queries.main,
        'query_user': user_queries.main,
        'delete_user': user_queries.main,
        'set_email': user_queries.main,
        'set_admin': user_queries.main,
        'set_skill': user_queries.main,

        'add_game': game_queries.main,
        'query_game': game_queries.main,
        'delete_game': game_queries.main,
        'set_game_name': game_queries.main,
        'set_game_id': game_queries.main,

        'create_event': event_queries.main,
        'delete_event': event_queries.main,
        'get_events': event_queries.main,
        'query_event': event_queries.main
    }
    command_syntax = {
        'help': ['Display help.  Either list all commands or enter a specific command',
                 ('COMMAND', 0, 'A specific command for which to display help.  If not specified, return list of all '
                                'commands')],
        'add_user': ['Add a new user to the LFJ backend',
                     ('DISPLAY_NAME', 1, "User's display name"),
                     ('EMAIL', 1, "User's email"),
                     ('ADMIN', 1, "Admin status of new user")],
        'query_user': ["Get a specified user's information",
                       ('ARGUMENT', 1, "Either ALL or DISPLAY_NAME")],
        'delete_user': ["Delete a user from the LFJ backend",
                        ('DISPLAY_NAME', 1, "Display name of user to be deleted")],
        'set_email': ["Update a user's email",
                      ('DISPLAY_NAME', 1, "User's Display name"),
                      ('EMAIL', 1, "New user email")],
        'set_admin': ["Set a user's admin status",
                      ('DISPLAY_NAME', 1, "User's display name"),
                      ('TRUE/FALSE', 1, "New value of admin status")],
        'add_game': ["Add a game to the LFJ backend",
                     ('ID', 1, "Numeric ID for a game (check existing IDs and pick one that is not taken)"),
                     ('NAME', 1, "String name of the game")],
        'query_game': ["Get information about ALL games or one specific game",
                       ('ALL/NAME', 1, 'ALL to see all games; NAME to see a specific game')],
        'delete_game': ["Delete a game from the LFJ backend",
                        ('NAME', 1, "Name of game to be deleted")],
        'set_game_name': ["Edit a game's given name",
                          ('OLD_NAME', 1, "Old name of game"),
                          ('NEW_NAME', 1, "New name of game")],
        'set_game_id': ["Edit a game's ID",
                        ('NAME', 1, "Game's given name"),
                        ('NEW_ID', 1, "Game's new ID")],
        'set_skill': ["Set a user's game skill",
                      ('GAME', 1, 'Game name for updating skill'),
                      ('SKILL_LEVEL', 1, "Skill ranking for game being updated")],
        'create_event': ["Create a new event",
                         ('TITLE', 1, "Event's title"),
                         ('DATE', 1, "Event's date"),
                         ('GAME', 1, "Game to be played at event")],
        'delete_event': ["Delete a scheduled event",
                         ('TITLE', 1, "Title of event to be deleted")],
        'get_events': ["Get all events"],
        'query_event': ["Get information about a specific event",
                        ('NAME', 1, "Name of event to query information about")]
    }

    event_channel = None
    event_created = True

    config = configparser.ConfigParser()        # read and parse configuration file
    config.read(r'../configuration.conf')

    token = config['Discord']['token']      # get the bot's unique token for sign-in
    event_channel_name = config['Discord']['events_channel']     # text name of the event channel

    client = discord.Client()       # create the bot client

    @client.event
    async def on_ready():
        """
        on_ready() is called when the bot is signed in to Discord and ready to send/receive event notifications
        :return: none; print ready status to console
        """
        global event_channel
        print('We have logged in as {0.user}'.format(client))
        for channel in client.get_all_channels():
            if str(channel.name) == event_channel_name:
                event_channel = channel

        if event_channel is None:       # server does not have a dedicated events channel
            print("ERROR: Could not find event channel")
            await client.logout()

    @client.event
    async def on_message(message):
        """
        on_message() is called when a message is sent in any channel that the bot is part of.  This includes messages
        sent from the bot itself.
        :param message: the message object that was sent
        :return: the bot will parse the message; there are two options: a response message is sent or no message is sent
        """
        global event_channel
        global event_created
        new_event_message = None

        if message.author == client.user:       # if the bot sent the message
            if message.channel == event_channel and not event_created:        # creating a new event
                new_event_message = message

                result = commands['create_event'](2, ['create_event', new_event_message])
                event_created = True

                if result == 1:
                    await message.channel.send("Error executing command.  Please consult syntax")
                    return

                return
            else:
                return
        if message.content.startswith('exit'):      # received the exit command
            await client.logout()       # log the bot out
            return      # return and end the program
        if len(message.mentions) == 0:      # if there are NO mentions, ignore the message
            return
        if not check_mentions(message.mentions[0], client):     # if the bot was not mentioned, do nothing
            return

        tokens = message.content.split(' ')[1:]     # get tokens
        command = tokens[0]     # according to syntax, next token is the command

        if command == 'create_event':       # send out new event message
            if len(tokens) != 4:
                await message.channel.send("Error executing command.  Please consult syntax")
                return
            query_command = ['query_game', tokens[-1], message.author]
            game_result = commands['query_game'](len(query_command), query_command)

            event_query_command = ['query_event', tokens[1], message.author]
            event_exists = commands['query_event'](len(event_query_command), event_query_command)

            if len(game_result) == 0 or len(event_exists) != 0:
                result = 1      # set an error flag
            else:
                event_created = False
                await event_channel.send(event_message_creator(tokens[1:]))
                return
        elif command == 'help':
            result = commands['help'](tokens, commands, command_syntax)
        elif command not in commands:     # if the command is not recognized, then notify the sender
            await message.channel.send("Invalid command")
            return
        else:
            tokens.append(message.author)  # get the sending user's information and pass it as an argument
            result = commands[command](len(tokens), tokens)  # handle the command according to command dictionary

        if result == 1:     # if there was an error executing the command, notify the user
            await message.channel.send("Error executing command.  Please consult syntax")
            return

        if type(result) is str:
            await message.channel.send(result)
        else:
            if len(result) == 0:
                await message.channel.send(result)
            else:
                try:
                    send = "\n".join(result)
                except TypeError:
                    await message.channel.send(result)
                else:  # if successful in connecting, create a cursor object
                    await message.channel.send(send)

    client.run(token)       # start the bot based on its sign-in token


def check_mentions(first_mention, client):
    """
    Check the users mentioned in a message to see if @LFJ is included.  Returns True only if the user was the first
    mention in the message.
    :param first_mention: the user object corresponding to the first mention in the message
    :param client: the client object (i.e. the bot); for checking against first_mention
    :return: True if the first mention is the bot; False otherwise
    """
    return str(first_mention) == str(client.user)


def give_help(tokens, commands, command_syntax):
    n_tokens = len(tokens)
    if n_tokens == 1:
        return commands.keys()
    elif n_tokens == 2:
        command = tokens[-1]
        if command not in commands:
            return "This command does not exist."
        else:
            return format_help(command_syntax[command])
    else:
        return 1


def format_help(command_description):
    if len(command_description) == 1:
        return command_description[0]

    descr = [command_description[0]]
    params = []
    for param in command_description[1:]:
        params.append(create_param_line(param))

    descr.extend(params)

    return descr


def create_param_line(param_tuple):
    name = param_tuple[0]
    descr = param_tuple[2]
    return f"{name}: {descr}"


def event_message_creator(message):
    return f'--------------------------------------------------\n' \
        f'Title: {message[0]}\n' \
        f'Date: {message[1]}\n' \
        f'Game: {message[2]}\n' \
        f'--------------------------------------------------'


if __name__ == '__main__':
    main()
