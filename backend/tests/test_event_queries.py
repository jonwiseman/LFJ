import unittest
import mysql.connector
import configparser
from backend.lib import event_queries as eq
from backend.lib.helper_commands import AdminPermissionError
from backend.lib.game_queries import get_game_id
import time
import datetime


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

        self.new_user = 'test#69420'
        event_date = '04/09/2020'
        self.data_insert = {'event_id': 1,
                            'date': datetime.date.fromtimestamp
                            (int(time.mktime(time.strptime(event_date, '%m/%d/%Y')))),
                            'game_id': 1,
                            'title': 'a test event',
                            'team_size': 5}

    def test_create_event(self):
        with self.assertRaises(eq.DateFormatError):     # check date formatting
            eq.check_date_format('04.09.2020')

        with self.assertRaises(eq.GameNotFoundError):       # check invalid game names
            get_game_id('a fake game', self.cursor)

        self.assertEqual(eq.sql_create_event(self.data_insert, self.cursor, self.cnx),
                         [(self.data_insert['event_id'], datetime.date(2020, 4, 9), 1, 'a test event', 5)])

        with self.assertRaises(eq.ExistingEventError):      # check duplicating titles
            eq.sql_create_event(self.data_insert, self.cursor, self.cnx)

    def test_delete_event(self):
        with self.assertRaises(AdminPermissionError):       # check unauthorized user changing database
            eq.sql_delete_event(self.new_user, self.data_insert['event_id'], self.cursor, self.cnx)

        with self.assertRaises(eq.EventNotFoundError):      # deleting a non-existent event
            eq.sql_delete_event(self.display_name, 2, self.cursor, self.cnx)

        self.assertEqual(eq.sql_create_event(self.data_insert, self.cursor, self.cnx),
                         [(self.data_insert['event_id'], datetime.date(2020, 4, 9), 1, 'a test event', 5)])

        self.assertEqual(eq.sql_delete_event(self.display_name, self.data_insert['event_id'], self.cursor, self.cnx),
                         [])

    def test_query_event(self):
        self.assertEqual(eq.sql_create_event(self.data_insert, self.cursor, self.cnx),
                         [(self.data_insert['event_id'], datetime.date(2020, 4, 9), 1, 'a test event', 5)])

        self.assertEqual(eq.sql_query_event(self.data_insert['event_id'], self.cursor),
                         [(self.data_insert['event_id'], datetime.date(2020, 4, 9), 1, 'a test event', 5)])
    def tearDown(self):
        self.cursor.execute('delete from event where title = %s', (self.data_insert['title'],))
        self.cnx.commit()  # commit changes to database
        self.cnx.close()
        self.cursor.close()


if __name__ == '__main__':
    unittest.main()
