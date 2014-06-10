from django.db import connection


class LogManager(object):

    loggers = {}
    debug = False

    @staticmethod
    def reset():
        LogManager.loggers = {}
        LogManager.debug = False
        connection.queries[:] = []

    @staticmethod
    def add_logger(logger):
        LogManager.enable_logging()
        LogManager.loggers[logger.name] = logger

    @staticmethod
    def get_logger(name=None):
        if name in LogManager.loggers:
            return LogManager.loggers[name]
        return Logger(name)

    @staticmethod
    def enable_logging():
        LogManager.debug = True

    @staticmethod
    def disable_logging():
        LogManager.debug = False


class Logger(object):

    def __init__(self, name=None):
        if name is None:
            name = 'default'
        self.name = name
        self.query_index = None
        self.queries = []
        LogManager.add_logger(self)
        print LogManager.loggers

    def start_logging(self):
        self.query_index = len(connection.queries)

    def update_log(self):
        num_queries = len(connection.queries)
        if self.query_index is not None and num_queries > self.query_index and LogManager.debug:
            self.queries.extend(connection.queries[self.query_index:])
        self.query_index = num_queries

    def get_log(self):
        self.update_log()
        return self.queries

    def stop_logging(self):
        self.update_log()
        self.query_index = None

    def clear_log(self):
        self.queries = []
        if self.query_index is not None:
            self.query_index = len(connection.queries)

    def count(self):
        self.update_log()
        return len(self.queries)
