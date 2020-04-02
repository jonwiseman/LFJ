def query_user(argument, cursor):
    """
    Query information from the user table.
    :param argument: either ALL (for a select * from user query) or a display name (for getting information about a
    specific user).
    :param cursor: cursor to execute queries
    :return: The result of the select statement
    """
    if argument.upper() == 'ALL':
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


def add_user(auth_user, id, display_name, email, is_admin, cursor, cnx):
    """
    Add a user to the user table.
    :param auth_user: user authorizing add
    :param id: numeric id of user
    :param display_name: display name of user
    :param email: email of user
    :param is_admin: admin status of new user
    :param cursor: cursor for executing query
    :param cnx: connection object for committing change
    :return: the new table after insertion or an error flag
    """
    admin_status = check_admin_status(auth_user, cursor)        # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:      # authorizing user does not exist or does not have permission
        return 1

    cursor.execute('insert into user '
                   '(user_id, display_name, e_mail, admin) '
                   'values (%s, %s, %s, %s)', (id, display_name, email, is_admin))
    cnx.commit()        # commit changes to database

    cursor.execute('select * from user')        # get new user table
    return cursor.fetchall()


def set_email(auth_user, display_name, email, cursor, cnx):
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


def set_admin_status(auth_user, display_name, new_status, cursor, cnx):
    """
    Update the admin status associated with a user.
    :param auth_user: user authorizing change
    :param display_name: display name of user whose admin status will be changed
    :param new_status: true or false depending on admin status being set
    :param cursor: cursor object to execute query
    :param cnx: connection object to commit changes
    :return: the new table after updating the user table
    """
    admin_status = check_admin_status(auth_user, cursor)  # see if the authorizing user is an admin
    if admin_status == -1 or admin_status == 0:  # authorizing user does not exist or does not have permission
        return 1

    if not (new_status == 'true' or new_status == 'false'):  # syntax for setting admin status is not true or false
        return 1

    cursor.execute('update user '
                   'set admin = %s '
                   'where display_name = %s', (1 if new_status == "true" else 0, display_name))
    cnx.commit()        # commit changes to user table
    cursor.execute('select * from user')        # get new user table
    return cursor.fetchall()


def set_membership(auth_user, game_name, skill_level, cursor, cnx):
    """
    Sets a users membership with a particular game
    :param auth_user: user authorizing change
    :param game_name: name of game user wants to set skill_level for
    :param skill_level: the level of skill the user holds in a game
    :param cursor: cursor object for executing queries
    :param cnx: connection object to commit changes
    :return: 1 if there is an error, response text if successful
    """
    user_id = get_user_id(auth_user, cursor)    # gets user_id from display_name

    if user_id == -1:   # user not found
        return 1

    game_id = get_game_id(game_name, cursor)    # gets game_id from game_name

    if game_id == -1:   # game not found
        return 1

    if check_membership(user_id, game_id, cursor) == -1:    # user does not hold membership of game
        cursor.execute('insert into membership '
                       '(user_id, game_id, skill_level) '
                       'values (%s, %s, %s)', (user_id, game_id, skill_level))
    else:
        cursor.execute('update membership '
                       'set skill_level = %s '
                       'where skill_level = %s', skill_level)
    cnx.commit()    # commit changes to membership table

    return "Successfully updated your skill level to " + skill_level + " for " + game_id


# HELPER FUNCTIONS #


def check_admin_status(display_name, cursor):
    """
    Check to see if a given user is an admin.  Only admins can change the database.
    :param display_name: display name of requesting user
    :param cursor: cursor object for executing search query
    :return: -1 if user does not exist, 0 if the user is not an admin, or 1 if the user is an admin
    """
    cursor.execute('select admin from user where display_name = %s', (display_name, ))
    result = cursor.fetchall()

    if len(result) == 0:    # user not found
        return -1

    return result[0][0]     # return 0 or 1


def check_membership(user_id, game_id, cursor):
    """
    Check to see if a given user has membership to a game
    :param user_id: user id to check
    :param game_id: game id to check
    :param cursor: cursor object for executing search query
    :return: -1 if membership does not exist, 1 if user has membership to given game
    """
    cursor.execute('select user_id from membership where user_id = %s and game_id = %s', (user_id, game_id))
    result = cursor.fetchall()

    if len(result) == 0:    # user not found
        return -1

    return result[0][0]     # return user id


def get_user_id(display_name, cursor):
    """
    Gets a user id from display name of a user
    :param display_name: display name of user whose id will be gotten
    :param cursor: cursor object for executing search query
    :return: -1 if user does not exist, user_id if user is found
    """
    cursor.execute('select user_id from user where display_name = %s', display_name)
    result = cursor.fetchall()

    if len(result) == 0:    # user not found
        return -1

    return result[0][0]     # return user id


def get_game_id(game_name, cursor):
    """
    Gets a game id from game name
    :param game_name: name of a game to get id for
    :param cursor: cursor object for executing search query
    :return: -1 if game does not exist, game_id if game is found
    """
    cursor.execute('select game_id from game where name = %s', game_name.lower())
    result = cursor.fetchall()

    if len(result) == 0:    # game not found
        return -1

    return result[0][0]     # return game id
