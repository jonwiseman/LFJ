import configparser
import discord
import user_queries


def main():
    commands = {        # list of commands available for bot to use
        'add_user': user_queries.main,
        'query_user': user_queries.main,
        'delete_user': user_queries.main,
        'update_user': user_queries.main
    }

    config = configparser.ConfigParser()        # read and parse configuration file
    config.read(r'..\configuration.conf')

    token = config['Discord']['token']      # get the bot's unique token for sign-in

    client = discord.Client()       # create the bot client

    @client.event
    async def on_ready():
        """
        on_ready() is called when the bot is signed in to Discord and ready to send/receive event notifications
        :return: none; print ready status to console
        """
        print('We have logged in as {0.user}'.format(client))

    @client.event
    async def on_message(message):
        """
        on_message() is called when a message is sent in any channel that the bot is part of.  This includes messages
        sent from the bot itself.
        :param message: the message object that was sent
        :return: the bot will parse the message; there are two options: a response message is sent or no message is sent
        """
        if message.author == client.user:       # if the bot sent the message, then no action is taken
            return
        if message.content.startswith('exit'):      # received the exit command
            await client.logout()       # log the bot out
            return      # return and end the program
        if not check_mentions(message.mentions[0], client):     # if the bot was not mentioned, do nothing
            return

        tokens = message.content.split(' ')[1:]     # get tokens
        command = tokens[0]     # according to syntax, next token is the command

        if command not in commands:     # if the command is not recognized, then notify the sender
            await message.channel.send("Invalid command")
            return

        tokens.append(message.author)       # get the sending user's information and pass it as an argument
        result = commands[command](len(tokens), tokens)     # handle the command according to command dictionary

        if result == 1:     # if there was an error executing the command, notify the user
            await message.channel.send("Error executing command.  Please consult syntax")
            return

        await message.channel.send(result)      # if there were no errors, then send the appropriate response

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


if __name__ == '__main__':
    main()
