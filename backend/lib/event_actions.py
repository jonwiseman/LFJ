from discord.ext import commands
from backend.lib.event_queries import sql_create_registration, get_team_player_count, sql_get_team_size, \
    get_teams_from_embed, add_player_to_team, modify_embed_message_teams, sql_delete_registration, \
    remove_player_from_team, ExistingRegistrationError
from backend.lib.user_queries import UserNotFoundError
from discord.errors import Forbidden


class EventActions(commands.Cog):
    def __init__(self, bot, cursor, cnx, event_channel_id):
        self.bot = bot
        self.cursor = cursor
        self.cnx = cnx
        self.event_channel_id = event_channel_id

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Test if human sender and if reaction occurred in event channel
        if payload.user_id != self.bot.user.id and payload.channel_id == self.event_channel_id:
            channel = self.bot.get_channel(payload.channel_id)
            msg = await channel.fetch_message(payload.message_id)
            user = self.bot.get_user(payload.user_id)

            if payload.emoji.name == '☑':
                try:
                    sql_create_registration(payload.message_id, str(user), self.cursor, self.cnx)
                except UserNotFoundError:
                    # Do nothing here
                    pass
                except ExistingRegistrationError:
                    # Do nothing here
                    pass
                except Forbidden:
                    pass
                else:   # Attempt to add user to team
                    team_size = sql_get_team_size(payload.message_id, self.cursor)  # Get size of teams from event
                    teams = get_teams_from_embed(msg.embeds[0], team_size)  # Get teams of event

                    if get_team_player_count(teams[0]) <= get_team_player_count(teams[1]):
                        teams[0] = add_player_to_team(teams[0], str(user))  # Attempt to add player to team
                        if teams[0] == -1:  # Teams are full
                            return
                    else:
                        teams[1] = add_player_to_team(teams[1], str(user))  # Add player to second team

                    # Update teams in event channel
                    embed = modify_embed_message_teams(msg.embeds[0], teams)
                    await msg.edit(embed=embed)

            elif payload.emoji.name == '🇽':
                try:
                    sql_delete_registration(payload.message_id, str(user), self.cursor, self.cnx)
                except UserNotFoundError:
                    # Do nothing here
                    pass
                except Forbidden:
                    pass
                else:
                    event_channel = self.bot.get_channel(self.event_channel_id)  # Get event channel
                    msg = await event_channel.fetch_message(payload.message_id)  # Get event message

                    team_size = sql_get_team_size(payload.message_id, self.cursor)  # Get size of teams from event
                    teams = get_teams_from_embed(msg.embeds[0], team_size)  # Get teams of event

                    # Remove player from team, if error we return
                    tempTeam0 = remove_player_from_team(teams[0], str(user))
                    tempTeam1 = remove_player_from_team(teams[1], str(user))

                    if tempTeam0 == -1 and tempTeam1 == -1:
                        # Do nothing here
                        pass
                    else:
                        if tempTeam0 != -1:
                            teams[0] = tempTeam0
                        else:
                            teams[1] = tempTeam1
                    embed = modify_embed_message_teams(msg.embeds[0], teams)
                    await msg.edit(embed=embed)

            try:
                await msg.remove_reaction(payload.emoji, user)
            except Forbidden:
                pass
