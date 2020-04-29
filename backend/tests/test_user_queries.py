import unittest
import mysql.connector
import configparser
from backend.lib import user_queries as uq
from backend.lib.helper_commands import AdminPermissionError


class UserTestCase(unittest.TestCase):
    def setUp(self):
        config = configparser.ConfigParser()  # read and parse configuration file
        config.read(r'backend/tests/test_configuration.conf')

        username = config['Database']['username']  # get details for signing in to database
        password = config['Database']['password']
        host = config['Database']['host']
        database = config['Database']['database']

        try:        # for CI testing
            self.cnx = mysql.connector.connect(user=username,
                                           password=password,
                                           host=host,
                                           database=database)  # connect to the database
        except mysql.connector.errors.DatabaseError:        # for local testing
            config.read(r'configuration.conf')

            username = config['Database']['username']  # get details for signing in to database
            password = config['Database']['password']
            host = config['Database']['host']
            database = config['Database']['database']

            self.cnx = mysql.connector.connect(user=username,
                                               password=password,
                                               host=host,
                                               database=database)  # connect to the database

        self.cursor = self.cnx.cursor()  # create cursor object for executing queries

        self.display_name = config['Testing']['display_name']
        self.id = int(config['Testing']['id'])
        self.admin = int(config['Testing']['admin'])

        self.new_user = "test#69420"
        self.new_id = 69420
        self.new_user_admin = 'false'

    def test_add_user(self):
        with self.assertRaises(AdminPermissionError):       # non-existing user trying to add to database
            uq.sql_add_user(self.new_id, self.new_id,
                            self.new_user, self.new_user_admin, self.cursor, self.cnx)

        self.assertEqual(uq.sql_add_user(self.id, self.new_id,
                                         self.new_user, self.new_user_admin, self.cursor, self.cnx),
                         [(69420, 'test#69420', 0)])       # adding a new user

        with self.assertRaises(uq.ExistingUserError):       # adding an existing user
            uq.sql_add_user(self.id, self.new_id,
                            self.new_user, self.new_user_admin, self.cursor, self.cnx)

        with self.assertRaises(AdminPermissionError):       # non-admin trying to add to database
            uq.sql_add_user(self.new_id, 42069, 'another_test', 0, self.cursor, self.cnx)

    def test_query_user(self):
        self.assertEqual(uq.sql_query_user(self.id, self.cursor),
                         [(self.id, self.display_name, self.admin)])        # querying a specific user
        self.assertEqual(uq.sql_query_user('ALL', self.cursor),
                         [(self.id, self.display_name, self.admin)])        # querying all users
        self.assertEqual(uq.sql_query_user('all', self.cursor),
                         [(self.id, self.display_name, self.admin)])        # checking case sensitivity

    def test_set_admin_status(self):
        with self.assertRaises(AdminPermissionError):       # non-existent user trying to change database
            uq.sql_set_admin_status(self.new_id, self.new_id, 'true', self.cursor, self.cnx)

        self.assertEqual(uq.sql_add_user(self.id, self.new_id, self.new_user,
                                         self.new_user_admin, self.cursor, self.cnx),
                         [(69420, 'test#69420', 0)])       # safe add new user

        with self.assertRaises(AdminPermissionError):       # non-admin trying to set admin status
            uq.sql_set_admin_status(self.new_id, self.new_id, 'true', self.cursor, self.cnx)

        self.assertEqual(uq.sql_set_admin_status(self.id, self.new_id, 'true', self.cursor, self.cnx),
                         [(69420, 'test#69420', 1)])       # admin updating admin status

    def test_delete_user(self):
        with self.assertRaises(AdminPermissionError):       # non-existent user trying to change database
            uq.sql_delete_user(self.new_id, self.id, self.cursor, self.cnx)

        self.assertEqual(uq.sql_add_user(self.id, self.new_id, self.new_user,
                                         self.new_user_admin, self.cursor, self.cnx),
                         [(69420, 'test#69420', 0)])       # safe add new non-admin user

        with self.assertRaises(AdminPermissionError):       # non-admin trying to delete an admin
            uq.sql_delete_user(self.new_id, self.id, self.cursor, self.cnx)

        self.assertEqual(uq.sql_set_admin_status(self.id, self.new_id, 'true', self.cursor, self.cnx),
                         [(69420, 'test#69420', 1)])  # safe give admin status

        with self.assertRaises(AdminPermissionError):       # admin trying to delete an admin
            uq.sql_delete_user(self.new_id, self.id, self.cursor, self.cnx)

        self.assertEqual(uq.sql_set_admin_status(self.id, self.new_id, 'false', self.cursor, self.cnx),
                         [(69420, 'test#69420', 0)])  # safe remove admin status

        self.assertEqual(uq.sql_delete_user(self.id, self.new_id, self.cursor, self.cnx),
                         [(self.id, self.display_name, self.admin)])

    def tearDown(self):
        self.cursor.execute('delete from user where user_id = %s', (self.new_id,))  # execute deletion query
        self.cnx.commit()  # commit changes to database
        self.cnx.close()
        self.cursor.close()


if __name__ == '__main__':
    unittest.main()
