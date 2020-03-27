import configparser
import mysql.connector
import discord


def main(argc, argv):
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

    command = argv[0]  # get the command entered by the user

    if command == 'add_game':
        if argc != 4:
            return 1
        data_insert = {
            'game_id': argv[1],
            'name': argv[2]
        }
        return add_game(str(argv[-1]), data_insert, cursor, cnx)
    elif command == 'query_game':
        if argc != 3:
            return 1
        return query_game(argv[-2], cursor)
    elif command == 'delete_game':
        if argc != 3:
            return 1
        return delete_game(str(argv[-1]), argv[-2], cursor, cnx)
    elif command == 'set_game_name':
        if argc != 4:
            return 1
        return edit_name(str(argv[-1]), argv[-3], argv[-2], cursor, cnx)
    elif command == 'set_game_id':
        if argc != 4:
            return 1
        return edit_id(str(argv[-1]), argv[1], argv[-2], cursor, cnx)
    else:
        return 1


def add_game(auth_user, data_insert, cursor, cnx):
    admin_status = check_admin_status(auth_user, cursor)  # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

    cursor.execute('insert into game '
                   '(game_id, name) '
                   'values (%(game_id)s, %(name)s)', data_insert)  # add new user
    cnx.commit()  # commit changes to database

    cursor.execute('select * from game')  # get new user table
    return cursor.fetchall()


def query_game(argument, cursor):
    if argument == 'ALL':
        cursor.execute('select * from game')
        return cursor.fetchall()
    else:
        cursor.execute('select * from game where name = %s', (argument,))
        return cursor.fetchall()


def delete_game(auth_user, name, cursor, cnx):
    admin_status = check_admin_status(auth_user, cursor)  # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

    cursor.execute('delete from game where name = %s', (name,))  # execute deletion query
    cnx.commit()  # commit changes to database
    cursor.execute('select * from game')  # get new user table
    return cursor.fetchall()


def edit_name(auth_user, old_name, new_name, cursor, cnx):
    admin_status = check_admin_status(auth_user, cursor)  # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

    cursor.execute('update game '
                   'set name = %s '
                   'where name = %s', (new_name, old_name))  # change the game table with new email
    cnx.commit()  # commit changes to user table
    cursor.execute('select * from game')  # get new user table
    return cursor.fetchall()


def edit_id(auth_user, name, id, cursor, cnx):
    admin_status = check_admin_status(auth_user, cursor)  # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

    cursor.execute('update game '
                   'set game_id = %s '
                   'where name = %s', (id, name))  # change the game table with new email
    cnx.commit()  # commit changes to user table
    cursor.execute('select * from game')  # get new user table
    return cursor.fetchall()


def check_admin_status(display_name, cursor):
    """
    Check to see if a given user is an admin.  Only admins can change the database.
    :param display_name: display name of requesting user
    :param cursor: cursor object for executing search query
    :return: -1 if user does not exist, 0 if the user is not an admin, or 1 if the user is an admin
    """
    cursor.execute('select admin from user where display_name = %s', (display_name,))
    result = cursor.fetchall()

    if len(result) == 0:    # user not found
        return -1

    return result[0][0]     # return 0 or 1


if __name__ == '__main__':
    main(0, [])