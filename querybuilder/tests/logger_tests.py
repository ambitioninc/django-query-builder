from django.db import connection
from django.test.utils import override_settings

from querybuilder.logger import Logger, LogManager
from querybuilder.query import Query
from querybuilder.tests.base import QuerybuilderTestCase
from querybuilder.tests.models import Account


@override_settings(DEBUG=True)
class LogManagerTest(QuerybuilderTestCase):
    """
    Includes functions to test the LogManager
    """
    def test_log_manager(self):
        self.assertEqual(len(LogManager.loggers.items()), 0, 'Incorrect number of loggers')
        logger_one = LogManager.get_logger('one')
        self.assertEqual(len(LogManager.loggers), 1, 'Incorrect number of loggers')
        logger_one = LogManager.get_logger('one')
        self.assertEqual(len(LogManager.loggers), 1, 'Incorrect number of loggers')
        LogManager.get_logger('two')
        self.assertEqual(len(LogManager.loggers), 2, 'Incorrect number of loggers')

        logger_one.start_logging()
        query = Query().from_table(Account)
        query.select()

        self.assertEqual(logger_one.count(), 1, 'Incorrect number of queries')
        LogManager.disable_logging()
        query.select()
        self.assertEqual(logger_one.count(), 1, 'Incorrect number of queries')
        LogManager.enable_logging()
        query.select()
        self.assertEqual(logger_one.count(), 2, 'Incorrect number of queries')


@override_settings(DEBUG=True)
class LoggerTest(QuerybuilderTestCase):
    """
    Includes functions to test the Logger
    """
    def setUp(self):
        super(LoggerTest, self).setUp()
        LogManager.reset()

    def test_init(self):
        """
        Tests the init method
        """
        logger = Logger()
        self.assertEqual('default', logger.name)
        self.assertIsNone(logger.query_index)
        self.assertEqual(0, len(logger.queries))
        self.assertEqual(1, len(LogManager.loggers))

        logger = Logger('custom_name')
        self.assertEqual('custom_name', logger.name)
        self.assertEqual(2, len(LogManager.loggers))

    def test_start_logging(self):
        """
        Verifies that the query index gets updated
        """
        logger = Logger()

        query = Query().from_table(Account)
        query.select()
        query.select()
        logger.start_logging()
        self.assertEqual(logger.query_index, len(connection.queries))

    def test_count(self):
        """
        Verifies that the correct number of queries is returned
        """
        logger = Logger()
        logger.start_logging()

        query = Query().from_table(Account)
        query.select()
        query.select()
        self.assertEqual(2, logger.count())
        query.select()
        self.assertEqual(3, logger.count())

    def test_stop_logging(self):
        """
        Verifies that the logger stops caring about queries
        """
        logger = Logger()
        logger.start_logging()

        query = Query().from_table(Account)
        query.select()
        query.select()

        self.assertEqual(2, logger.count())

        logger.stop_logging()
        query.select()
        query.select()
        self.assertEqual(2, logger.count())

        logger.start_logging()
        query.select()
        self.assertEqual(3, logger.count())

    def test_get_log(self):
        """
        Verifies that queries get returned
        """
        pass

    def test_update_log(self):
        """
        Verifies that the log gets updated properly
        """
        pass

    def test_logger(self):
        logger_one = Logger('one')
        logger_two = Logger('two')

        logger_one.start_logging()
        query = Query().from_table(Account)
        query.select()

        self.assertEqual(logger_one.count(), 1, 'Incorrect number of queries')

        query.select()
        logger_two.start_logging()
        query.select()
        logger_one.stop_logging()
        query.select()

        self.assertEqual(logger_one.count(), 3, 'Incorrect number of queries')
        self.assertEqual(logger_two.count(), 2, 'Incorrect number of queries')

        query.select()
        logger_one.start_logging()
        query.select()

        self.assertEqual(logger_one.count(), 4, 'Incorrect number of queries')
        self.assertEqual(logger_two.count(), 4, 'Incorrect number of queries')

        query.select()
        logger_two.clear_log()
        query.select()

        self.assertEqual(logger_one.count(), 6, 'Incorrect number of queries')
        self.assertEqual(logger_two.count(), 1, 'Incorrect number of queries')

    def test_clear_log(self):
        """
        Makes sure queries are cleared
        """
        logger_one = Logger('one')
        logger_one.start_logging()
        query = Query().from_table(Account)

        # run a query and update the logger's query list
        query.select()
        logger_one.update_log()

        # there should be one query
        self.assertEqual(logger_one.count(), 1)

        # increment the connection query count
        query.select()

        # clear the log
        logger_one.clear_log()

        # make sure no queries
        self.assertEqual(0, len(logger_one.queries))

    def test_clear_log_no_index(self):
        """
        Makes sure that the query index doesn't change
        """
        logger_one = Logger('one')

        query = Query().from_table(Account)
        query.select()

        self.assertIsNone(logger_one.query_index)

        # clear the log
        logger_one.clear_log()

        # make sure no query index
        self.assertIsNone(logger_one.query_index)
