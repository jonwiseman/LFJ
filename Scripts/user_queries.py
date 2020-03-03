import configparser
import mysql.connector


def main(argc, argv):
    config = configparser.ConfigParser()
    config.read(r'..\configuration.conf')

    username = config['Database']['username']
    password = config['Database']['password']
    host = config['Database']['host']
    database = config['Database']['database']

    try:
        cnx = mysql.connector.connect(user=username,
                                      password=password,
                                      host=host,
                                      database=database)
    except mysql.connector.Error:
        return 1
    else:
        cursor = cnx.cursor()

    command = argv[0]
    if command == 'query_user':
        if argc > 3:
            return 1
        return query_user(argv[1], cursor)
    elif command == 'add_user':
        if argc != 5:
            return 1
        data_insert = {
            'user_id': argv[1].split('#')[1],
            'display_name': argv[1],
            'e_mail': argv[2],
            'admin': argv[3]
        }
        return add_user(str(argv[-1]), data_insert, cursor, cnx)
    elif command == 'delete_user':
        if argc != 3:
            return 1
        return delete_user(str(argv[-1]), argv[1], cursor, cnx)
    elif command == 'update_user':
        if argc != 4:
            return 1
        return update_user(str(argv[-1]), argv[1], argv[2], cursor, cnx)

    cnx.close()


def query_user(argument, cursor):
    if argument == 'ALL':
        cursor.execute('select * from user')
        return cursor.fetchall()
    else:
        cursor.execute('select * from user where display_name = %s', (argument,))
        return cursor.fetchall()


def delete_user(auth_user, display_name, cursor, cnx):
    admin_status = check_admin_status(auth_user, cursor)
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

    delete_admin = check_admin_status(display_name, cursor)
    if delete_admin == -1 or delete_admin == 1:     # trying to delete a non-existant user or another admin
        return 1

    cursor.execute('delete from user where display_name = %s', (display_name,))
    cnx.commit()
    cursor.execute('select * from user')
    return cursor.fetchall()


def add_user(auth_user, data_insert, cursor, cnx):
    admin_status = check_admin_status(auth_user, cursor)
    if admin_status == -1 or admin_status == 0:      # authorizing user does not exist or does not have permission
        return 1

    cursor.execute('insert into user '
                   '(user_id, display_name, e_mail, admin) '
                   'values (%(user_id)s, %(display_name)s, %(e_mail)s, %(admin)s)', data_insert)
    cnx.commit()

    cursor.execute('select * from user')
    return cursor.fetchall()


def update_user(auth_user, display_name, email, cursor, cnx):
    admin_status = check_admin_status(auth_user, cursor)
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

    cursor.execute('update user '
                   'set e_mail = %s '
                   'where display_name = %s', (email, display_name))
    cnx.commit()
    cursor.execute('select * from user')
    return cursor.fetchall()


def check_admin_status(display_name, cursor):
    cursor.execute('select admin from user where display_name = %s', (display_name,))
    result = cursor.fetchall()

    if len(result) == 0:        # user not found
        return -1

    return result[0][0]     # return 0 or 1


if __name__ == '__main__':
    main(0, [])
