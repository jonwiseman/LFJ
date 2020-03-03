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
        if argc > 2:
            return 1
        return query_user(argv[1], cursor)

    cnx.close()


def query_user(argument, cursor):
    if argument == 'ALL':
        cursor.execute('select * from user')
        return cursor.fetchall()
    else:
        cursor.execute('select * from user where user_id = %s', (argument,))
        return cursor.fetchall()


def delete_user():
    pass


def add_user():
    pass


if __name__ == '__main__':
    main(0, [])
