import unittest
import mysql.connector
import configparser
from backend.lib import game_queries as gq
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
        self.email = config['Testing']['email']
        self.admin = int(config['Testing']['admin'])

        self.new_game_id = 69420
        self.new_game_name = "a fake game"

        self.new_user = "test#69420"

    def test_add_game(self):
        with self.assertRaises(AdminPermissionError):       # user without permission editing database
            gq.sql_add_game(self.new_user, self.new_game_id, self.new_game_name, self.cursor, self.cnx)

        with self.assertRaises(mysql.connector.errors.IntegrityError):
            gq.sql_add_game(self.display_name, 1,
                            self.new_game_name, self.cursor, self.cnx)

        self.assertEqual(gq.sql_add_game(self.display_name, self.new_game_id,
                                         self.new_game_name, self.cursor, self.cnx),
                         [(self.new_game_id, self.new_game_name)])      # test adding to database

        with self.assertRaises(gq.ExistingGameError):       # adding a duplicate game
            gq.sql_add_game(self.display_name, self.new_game_id,
                            self.new_game_name, self.cursor, self.cnx)

    def test_delete_game(self):
        with self.assertRaises(AdminPermissionError):       # user without permission editing database
            gq.sql_delete_game(self.new_user, self.new_game_name, self.cursor, self.cnx)

        with self.assertRaises(gq.GameNotFoundError):       # deleting a game that does not exist
            gq.sql_delete_game(self.display_name, self.new_game_name, self.cursor, self.cnx)

        self.assertEqual(gq.sql_add_game(self.display_name, self.new_game_id,
                                         self.new_game_name, self.cursor, self.cnx),
                         [(self.new_game_id, self.new_game_name)])  # safe add new game

        self.assertEqual(gq.sql_delete_game(self.display_name, self.new_game_name, self.cursor, self.cnx),
                         [(0, 'League of Legends'), (1, 'CSGO'), (2, 'Rocket League')])

    def test_edit_name(self):
        with self.assertRaises(AdminPermissionError):       # user without permission editing database
            gq.sql_edit_name(self.new_user, self.new_game_name, "a faker game", self.cursor, self.cnx)

        with self.assertRaises(gq.GameNotFoundError):
            gq.sql_edit_name(self.display_name, self.new_game_name, "a faker game", self.cursor, self.cnx)

        self.assertEqual(gq.sql_add_game(self.display_name, self.new_game_id,
                                         self.new_game_name, self.cursor, self.cnx),
                         [(self.new_game_id, self.new_game_name)])  # safe add new game

        with self.assertRaises(gq.ExistingGameError):
            gq.sql_edit_name(self.display_name, self.new_game_name, "CSGO", self.cursor, self.cnx)

        self.assertEqual(gq.sql_edit_name(self.display_name, self.new_game_name, "a faker game", self.cursor,
                                          self.cnx),
                         [(69420, "a faker game")])

    def test_edit_id(self):
        with self.assertRaises(AdminPermissionError):       # user without permission editing database
            gq.sql_edit_id(self.new_user, self.new_game_name, self.new_game_id + 1, self.cursor, self.cnx)

        with self.assertRaises(gq.GameNotFoundError):       # editing a non-existent game
            gq.sql_edit_id(self.display_name, self.new_game_name, self.new_game_id + 1, self.cursor, self.cnx)

        self.assertEqual(gq.sql_add_game(self.display_name, self.new_game_id,
                                         self.new_game_name, self.cursor, self.cnx),
                         [(self.new_game_id, self.new_game_name)])  # safe add new game

        with self.assertRaises(mysql.connector.errors.IntegrityError):      # changing ID into an existing ID
            gq.sql_edit_id(self.display_name, self.new_game_name, 1, self.cursor, self.cnx)

        self.assertEqual(gq.sql_edit_id(self.display_name, self.new_game_name, self.new_game_id + 1,
                                        self.cursor, self.cnx),
                         [(self.new_game_id + 1, self.new_game_name)])

    def test_query_game(self):
        self.assertEqual(gq.sql_query_game(self.new_game_name, self.cursor), [])

        self.assertEqual(gq.sql_add_game(self.display_name, self.new_game_id,
                                         self.new_game_name, self.cursor, self.cnx),
                         [(self.new_game_id, self.new_game_name)])      # safe add new game

        self.assertEqual(gq.sql_query_game(self.new_game_name, self.cursor),
                         [(self.new_game_id, self.new_game_name)])

        self.assertEqual(gq.sql_query_game('alL', self.cursor),
                         [(0, 'League of Legends'), (1, 'CSGO'),
                          (2, 'Rocket League'), (self.new_game_id, self.new_game_name)])

    def tearDown(self):
        self.cursor.execute('delete from game where game_id = %s', (self.new_game_id,))  # execute deletion query
        self.cursor.execute('delete from game where game_id = %s', (self.new_game_id + 1,))  # execute deletion query
        self.cnx.commit()  # commit changes to database
        self.cnx.close()
        self.cursor.close()


if __name__ == '__main__':
    unittest.main()
