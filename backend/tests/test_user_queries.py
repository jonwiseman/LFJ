import unittest
import mysql.connector
import configparser
from backend.lib import user_queries as uq


class UserTestCase(unittest.TestCase):
    def setUp(self):
        config = configparser.ConfigParser()  # read and parse configuration file
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

        self.display_name = "jon_wiseman#8494"
        self.id = 8494
        self.email = "wisemanj@etown.edu"
        self.admin = 1

        self.new_user = "test#69420"
        self.new_id = 69420
        self.new_user_email = "test@test.com"
        self.new_user_admin = 0

    def test_add_user(self):
        self.assertEqual(uq.sql_add_user(self.display_name, self.new_id,
                                         self.new_user, self.new_user_email,
                                         self.new_user_admin, self.cursor, self.cnx),
                         [(69420, 'test#69420', 'test@test.com', 0)])
        with self.assertRaises(uq.ExistingUserError):
            uq.sql_add_user(self.display_name, self.new_id,
                            self.new_user, self.new_user_email,
                            self.new_user_admin, self.cursor, self.cnx)

    def tearDown(self):
        self.cnx.close()
        self.cursor.close()


if __name__ == '__main__':
    unittest.main()
