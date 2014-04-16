from querybuilder.logger import Logger, LogManager
from querybuilder.query import Query
from querybuilder.tests.models import Account
from querybuilder.tests.query_tests import QueryTestCase


class LoggerTest(QueryTestCase):
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
