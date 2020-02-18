import configparser
import discord


def main():
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

        if message.content.startswith('$hello'):
            await message.channel.send('Hello!')

    client.run(token)


if __name__ == '__main__':
    main()
