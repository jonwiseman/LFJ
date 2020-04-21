from discord.ext import commands
from discord import File as dFile
from backend.lib.helper_commands import check_admin_status, AdminPermissionError
from urllib import request
from io import BytesIO


class PerformanceQueries(commands.Cog):
    def __init__(self, bot, cursor, cnx):
        self.bot = bot
        self.cursor = cursor
        self.cnx = cnx

    @commands.command()
    async def perf_update(self, ctx):
        """
               Update Performance
               :return: number of records updated
        """
        user = str(ctx.author)
        try:
            check_admin_status(user, True, self.cursor)
            if len(ctx.message.attachments) > 0:
                file_url = ctx.message.attachments[0].url
                if file_url[-3:].lower() == 'csv':
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) '
                                             'Chrome/41.0.2228.0 Safari/537.3'}
                    req = request.Request(url=file_url, headers=headers)
                    file_pointer = request.urlopen(req)
                    file = file_pointer.readlines()
                    if file[0].index(b'user_id,event_id,kills,deaths,win,length,win_score,lose_score') > -1:
                        records = csv2dicts(file)
                        inserts, updates = 0, 0
                        for record in records:
                            u = sql_perf_update(record, self.cursor, self.cnx)
                            if u:
                                updates = updates+1
                            else:
                                inserts = inserts+1
                        msg = "%s records were updated, %s new records were inserted" % (updates, inserts)
                        await ctx.send(msg)
                    else:
                        await ctx.send("File has no header")
                else:
                    await ctx.send("File attached is not a csv")
            else:
                await ctx.send("No file attached")
        except AdminPermissionError:
            await ctx.send("You do not have the necessary permissions")

    @commands.command()
    async def perf_template(self, ctx, event_name):
        event_id = get_event_id(self.cursor, event_name)
        registered = sql_get_registrations(self.cursor, event_id)
        header = 'display_name,user_id,event_id,kills,deaths,win,length,win_score,lose_score\r\n'
        filname = event_name + ".csv"
        fil = BytesIO()
        fil.write(bytes(header, "utf-8"))
        for u in registered:
            fil.write(bytes("%s,%s,%s,,,,,,\r\n" % (u[0], u[1], event_id), "utf-8"))
        fil.seek(0)
        await ctx.send(file=dFile(fil, filname))
        fil.close()


def sql_perf_update(data_insert, cursor, cnx):
    cursor.execute('select count(*) from performance '
                   'where event_id = %(event_id)s and user_id = %(user_id)s', data_insert)
    qty = cursor.fetchall()
    u = False
    if qty[0][0] == 0:
        cursor.execute('insert into performance '
                       '(event_id, user_id, kills, deaths, win, length, win_score, lose_score) '
                       'values (%(event_id)s, %(user_id)s, %(kills)s, %(deaths)s, %(win)s, %(length)s, '
                       '%(win_score)s, %(lose_score)s)', data_insert)
    else:
        cursor.execute('update performance '
                       'set kills = %(kills)s, deaths=%(deaths)s, win=%(win)s, length=%(length)s, '
                       'win_score = %(win_score)s, lose_score=%(lose_score)s '
                       'where event_id = %(event_id)s and user_id = %(user_id)s', data_insert)
        u = True
    cnx.commit()  # commit changes to database
    return u


def get_event_id(cursor,title):
    cursor.execute('select event_id from event where title = %s', (title,))
    return cursor.fetchall()[0][0]


def sql_get_registrations(cursor, event):
    cursor.execute('select user.display_name, registration.user_id from registration inner join user '
                   'on user.user_id  = registration.user_id where event_id = %s', (event,))
    return cursor.fetchall()


def csv2dicts(csvlist):
    head = csvlist[0]
    head = head.decode().strip('\n').strip('\r').split(',')
    dicts = []
    for line in csvlist[1:]:
        line = line.decode().strip('\n').strip('\r').split(',')
        line = [int(x) if x.isnumeric() else x for x in line]
        dicts.append(dict(zip(head, line)))
    return dicts

