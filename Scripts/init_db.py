import configparser
import mysql.connector


def main():
    command_list = {
        'add_user': add_user,
        'delete_user': delete_user,
        'add_game': add_game,
        'delete_game': delete_game,
        'query_table': query_table
    }

    config = configparser.ConfigParser()  # read and parse the config file
    config.read(r'../configuration.conf')

    username = config['Database']['username']  # get details for signing in to database
    password = config['Database']['password']
    host = config['Database']['host']
    database = config['Database']['database']

    try:  # try connecting to the database
        cnx = mysql.connector.connect(user=username,
                                      password=password,
                                      host=host,
                                      database=database)
    except mysql.connector.Error:  # catch connection errors
        return 1
    else:  # if successful in connecting, create a cursor object
        cursor = cnx.cursor()

    response = str(input(">"))
    while response != 'exit':
        if response in command_list:
            print(command_list[response](cursor, cnx))
        response = str(input(">"))

    cursor.close()
    cnx.close()


def add_user(cursor, cnx):
    data_insert = {  # prepare data for insertion into database
        'user_id': str(input("Enter user's name: ")),  # get the integer ID from the display name
        'display_name': str(input("Enter user's display name: ")),  # display name passed by user
        'e_mail': str(input("Enter user's e-mail: ")),  # e-mail entered by user
        'admin': int(input("Enter user's admin status: "))  # admin status entered by user
    }

    cursor.execute('insert into user '
                   '(user_id, display_name, e_mail, admin) '
                   'values (%(user_id)s, %(display_name)s, %(e_mail)s, %(admin)s)', data_insert)  # add new user
    cnx.commit()  # commit changes to database

    cursor.execute('select * from user')  # get new user table
    return cursor.fetchall()


def delete_user(cursor, cnx):
    display_name = str(input("Enter display name: "))
    cursor.execute('delete from user where display_name = %s', (display_name,))  # execute deletion query
    cnx.commit()  # commit changes to database
    cursor.execute('select * from user')  # get new user table
    return cursor.fetchall()


def add_game(cursor, cnx):
    data_insert = {  # prepare data for insertion into database
        'game_id': int(input("Enter game's ID: ")),
        'game_name': str(input("Enter game's name: "))
    }

    cursor.execute('insert into game '
                   '(game_id, name) '
                   'values (%(game_id)s, %(game_name)s)', data_insert)  # add new game
    cnx.commit()  # commit changes to database

    cursor.execute('select * from game')  # get new game table
    return cursor.fetchall()


def query_table(cursor, cnx):
    table_name = input("Enter table's name: ")
    if table_name == 'user':
        cursor.execute('select * from user')
    if table_name == 'game':
        cursor.execute('select * from game')
    if table_name == 'event':
        cursor.execute('select * from event')

    return cursor.fetchall()


if __name__ == '__main__':
    main()
