from django.conf import settings
from django.db import connection


class LogManager(object):

    loggers = {}

    @staticmethod
    def add_logger(logger):
        LogManager.enable_logging()
        LogManager.loggers[logger.name] = logger

    @staticmethod
    def get_logger(name):
        if name in LogManager.loggers:
            return LogManager.loggers[name]
        return Logger(name)

    @staticmethod
    def enable_logging():
        settings.DEBUG = True

    @staticmethod
    def disable_logging():
        settings.DEBUG = False


class Logger(object):

    def __init__(self, name):
        self.name = name
        self.query_index = None
        self.queries = []
        LogManager.add_logger(self)

    def start_logging(self):
        self.query_index = len(connection.queries)

    def get_log(self):
        self.update_log()
        return self.queries

    def update_log(self):
        num_queries = len(connection.queries)
        if self.query_index is not None and num_queries > self.query_index:
            self.queries += connection.queries[self.query_index:]
            self.query_index = num_queries

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
