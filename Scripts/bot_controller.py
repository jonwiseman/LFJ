import configparser
import discord
import user_queries


def main():
    commands = {
        'add_user': user_queries.main,
        'query_user': user_queries.main,
        'delete_user': user_queries.main
    }

    config = configparser.ConfigParser()
    config.read(r'..\configuration.conf')

    token = config['Discord']['token']

    client = discord.Client()

    @client.event
    async def on_ready():
        print('We have logged in as {0.user}'.format(client))

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
        if message.content.startswith('exit'):
            await client.logout()
            return
        if not check_mentions(message.mentions[0], client):
            return

        tokens = message.content.split(' ')[1:]     # get tokens
        command = tokens[0]     # according to syntax, next token is the command

        if command not in commands:
            await message.channel.send("Invalid command")
            return

        result = commands[command](len(tokens), tokens)

        if result == 1:
            await message.channel.send("Error executing command.  Please consult syntax")
            return

        await message.channel.send(result)

    client.run(token)


def check_mentions(first_mention, client):
    return str(first_mention) == str(client.user)


if __name__ == '__main__':
    main()
