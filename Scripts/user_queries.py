import configparser
import mysql.connector


def main(argc, argv):
    config = configparser.ConfigParser()        # read and parse the config file
    config.read(r'../configuration.conf')

    username = config['Database']['username']       # get details for signing in to database
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
    if command == 'query_user':
        if argc > 3:        # syntax dictates 2 arguments (command, ALL/USER); third argument is the user who requested
            return 1
        return query_user(argv[1], cursor)
    elif command == 'add_user':
        if argc != 5:       # syntax dictates 4 arguments (command, user id, display name, admin status)
            return 1
        data_insert = {     # prepare data for insertion into database
            'user_id': argv[1].split('#')[1],       # get the integer ID from the display name
            'display_name': argv[1],        # display name passed by user
            'e_mail': argv[2],      # e-mail entered by user
            'admin': argv[3]        # admin status entered by user
        }
        return add_user(str(argv[-1]), data_insert, cursor, cnx)
    elif command == 'delete_user':
        if argc != 3:       # syntax dictates 2 arguments (command, display name)
            return 1
        return delete_user(str(argv[-1]), argv[1], cursor, cnx)
    elif command == 'update_user':
        if argc != 4:       # syntax dictates 3 arguments (command, display name, new email)
            return 1
        return update_user(str(argv[-1]), argv[1], argv[2], cursor, cnx)

    cnx.close()     # close the connection to the database


def query_user(argument, cursor):
    """
    Query information from the user table.
    :param argument: either ALL (for a select * from user query) or a display name (for getting information about a
    specific user).
    :param cursor: cursor to execute queries
    :return: The result of the select statement
    """
    if argument == 'ALL':
        cursor.execute('select * from user')
        return cursor.fetchall()
    else:
        cursor.execute('select * from user where display_name = %s', (argument,))
        return cursor.fetchall()


def delete_user(auth_user, display_name, cursor, cnx):
    """
    Delete a row from the user table based on display name.
    :param auth_user: user who is authorizing the delete
    :param display_name: display name of the user to be deleted
    :param cursor: cursor object for executing query
    :param cnx: connection object for committing changes
    :return: the new table after deletion or an error flag
    """
    admin_status = check_admin_status(auth_user, cursor)        # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

    delete_admin = check_admin_status(display_name, cursor)     # see if the user to be deleted is an admin
    if delete_admin == -1 or delete_admin == 1:     # trying to delete a non-existant user or another admin
        return 1

    cursor.execute('delete from user where display_name = %s', (display_name,))     # execute deletion query
    cnx.commit()        # commit changes to database
    cursor.execute('select * from user')        # get new user table
    return cursor.fetchall()


def add_user(auth_user, data_insert, cursor, cnx):
    """
    Add a user to the user table.
    :param auth_user: user authorizing add
    :param data_insert: dictionary of data to be inserted (user id, display name, email, and admin status)
    :param cursor: cursor for executing query
    :param cnx: connection object for committing change
    :return: the new table after insertion or an error flag
    """
    admin_status = check_admin_status(auth_user, cursor)        # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:      # authorizing user does not exist or does not have permission
        return 1

    cursor.execute('insert into user '
                   '(user_id, display_name, e_mail, admin) '
                   'values (%(user_id)s, %(display_name)s, %(e_mail)s, %(admin)s)', data_insert)        # add new user
    cnx.commit()        # commit changes to database

    cursor.execute('select * from user')        # get new user table
    return cursor.fetchall()


def update_user(auth_user, display_name, email, cursor, cnx):
    """
    Update the email associated with a user.
    :param auth_user: user authorizing change
    :param display_name: display name of user whose email will be changed
    :param email: new email for user
    :param cursor: cursor object to execute query
    :param cnx: connection object to commit changes
    :return: the new table after updating the user table
    """
    admin_status = check_admin_status(auth_user, cursor)        # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

    cursor.execute('update user '
                   'set e_mail = %s '
                   'where display_name = %s', (email, display_name))        # change the user table with new email
    cnx.commit()        # commit changes to user table
    cursor.execute('select * from user')        # get new user table
    return cursor.fetchall()


def check_admin_status(display_name, cursor):
    """
    Check to see if a given user is an admin.  Only admins can change the database.
    :param display_name: display name of requesting user
    :param cursor: cursor object for executing search query
    :return: 0 if the user is not an admin (or does not exist) or 1 if the user is an admin
    """
    cursor.execute('select admin from user where display_name = %s', (display_name,))
    result = cursor.fetchall()

    if len(result) == 0:        # user not found
        return -1

    return result[0][0]     # return 0 or 1


if __name__ == '__main__':
    main(0, [])
