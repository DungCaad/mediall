import time

import MySQLdb
from django.db.backends.mysql.base import DatabaseWrapper as MySQLDatabaseWrapper


RETRYABLE_MYSQL_ERROR_CODES = {2002, 2003, 2006, 2013}
MYSQL_CONNECT_RETRY_DELAYS = (0, 0.5, 1.5)


def connect_with_retry(connect, delays=MYSQL_CONNECT_RETRY_DELAYS):
    for attempt, delay in enumerate(delays):
        if delay:
            time.sleep(delay)
        try:
            return connect()
        except MySQLdb.OperationalError as error:
            error_code = error.args[0] if error.args else None
            if error_code not in RETRYABLE_MYSQL_ERROR_CODES or attempt == len(delays) - 1:
                raise


class DatabaseWrapper(MySQLDatabaseWrapper):
    def get_new_connection(self, conn_params):
        return connect_with_retry(lambda: super(DatabaseWrapper, self).get_new_connection(conn_params))
