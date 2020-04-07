import unittest
import mysql.connector
import configparser
from backend.lib import user_queries as uq
from backend.lib.helper_commands import AdminPermissionError


class UserTestCase(unittest.TestCase):
    def setUp(self):
        config = configparser.ConfigParser()  # read and parse configuration file
        config.read(r'test_configuration.conf')

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
        self.email = config['Testing']['email']
        self.admin = int(config['Testing']['admin'])

        self.new_user = "test#69420"
        self.new_id = 69420
        self.new_user_email = "test@test.com"
        self.new_user_admin = 0

    def test_add_user(self):
        with self.assertRaises(AdminPermissionError):       # non-existing user trying to add to database
            uq.sql_add_user(self.new_user, self.new_id,
                            self.new_user, self.new_user_email,
                            self.new_user_admin, self.cursor, self.cnx)

        self.assertEqual(uq.sql_add_user(self.display_name, self.new_id,
                                         self.new_user, self.new_user_email,
                                         self.new_user_admin, self.cursor, self.cnx),
                         [(69420, 'test#69420', 'test@test.com', 0)])       # adding a new user

        with self.assertRaises(uq.ExistingUserError):       # adding an existing user
            uq.sql_add_user(self.display_name, self.new_id,
                            self.new_user, self.new_user_email,
                            self.new_user_admin, self.cursor, self.cnx)

        with self.assertRaises(AdminPermissionError):       # non-admin trying to add to database
            uq.sql_add_user(self.new_user, 42069,
                            'another_test', 'test@test.com',
                            0, self.cursor, self.cnx)

    def test_query_user(self):
        self.assertEqual(uq.sql_query_user(self.display_name, self.cursor),
                         [(self.id, self.display_name, self.email, self.admin)])        # querying a specific user
        self.assertEqual(uq.sql_query_user('ALL', self.cursor),
                         [(self.id, self.display_name, self.email, self.admin)])        # querying all users
        self.assertEqual(uq.sql_query_user('all', self.cursor),
                         [(self.id, self.display_name, self.email, self.admin)])        # checking case sensitivity

    def test_set_email(self):
        with self.assertRaises(AdminPermissionError):       # non-existent user trying to modify database
            uq.sql_set_admin_status(self.new_user, self.new_user, 'true', self.cursor, self.cnx)

        self.assertEqual(uq.sql_add_user(self.display_name, self.new_id,
                                         self.new_user, self.new_user_email,
                                         self.new_user_admin, self.cursor, self.cnx),
                         [(69420, 'test#69420', 'test@test.com', 0)])       # safe add new user

        with self.assertRaises(AdminPermissionError):       # new user trying to change emails
            uq.sql_set_email(self.new_user, self.new_user, 'new_email@test.com', self.cursor, self.cnx)

        self.assertEqual(uq.sql_set_email(self.display_name, self.new_user,
                                          'new_email@test.com', self.cursor, self.cnx),
                         [(69420, 'test#69420', 'new_email@test.com', 0)])      # an admin is changing an email

    def test_set_admin_status(self):
        with self.assertRaises(AdminPermissionError):       # non-existent user trying to change database
            uq.sql_set_admin_status(self.new_user, self.new_user, 'true', self.cursor, self.cnx)

        self.assertEqual(uq.sql_add_user(self.display_name, self.new_id,
                                         self.new_user, self.new_user_email,
                                         self.new_user_admin, self.cursor, self.cnx),
                         [(69420, 'test#69420', 'test@test.com', 0)])       # safe add new user

        with self.assertRaises(AdminPermissionError):       # non-admin trying to set admin status
            uq.sql_set_admin_status(self.new_user, self.new_user, 'true', self.cursor, self.cnx)

        self.assertEqual(uq.sql_set_admin_status(self.display_name, self.new_user, 'true', self.cursor, self.cnx),
                         [(69420, 'test#69420', 'test@test.com', 1)])       # admin updating admin status

    def test_delete_user(self):
        with self.assertRaises(AdminPermissionError):       # non-existent user trying to change database
            uq.sql_delete_user(self.new_user, self.display_name, self.cursor, self.cnx)

        self.assertEqual(uq.sql_add_user(self.display_name, self.new_id,
                                         self.new_user, self.new_user_email,
                                         self.new_user_admin, self.cursor, self.cnx),
                         [(69420, 'test#69420', 'test@test.com', 0)])       # safe add new non-admin user

        with self.assertRaises(AdminPermissionError):       # non-admin trying to delete an admin
            uq.sql_delete_user(self.new_user, self.display_name, self.cursor, self.cnx)

        self.assertEqual(uq.sql_set_admin_status(self.display_name, self.new_user, 'true', self.cursor, self.cnx),
                         [(69420, 'test#69420', 'test@test.com', 1)])  # safe give admin status

        with self.assertRaises(AdminPermissionError):       # admin trying to delete an admin
            uq.sql_delete_user(self.new_user, self.display_name, self.cursor, self.cnx)

        self.assertEqual(uq.sql_set_admin_status(self.display_name, self.new_user, 'false', self.cursor, self.cnx),
                         [(69420, 'test#69420', 'test@test.com', 0)])  # safe remove admin status

        self.assertEqual(uq.sql_delete_user(self.display_name, self.new_user, self.cursor, self.cnx),
                         [(self.id, self.display_name, self.email, self.admin)])

    def tearDown(self):
        self.cursor.execute('delete from user where display_name = %s', (self.new_user,))  # execute deletion query
        self.cnx.commit()  # commit changes to database
        self.cnx.close()
        self.cursor.close()


if __name__ == '__main__':
    unittest.main()
