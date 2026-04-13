"""PyMySQL como MySQLdb (sin mysqlclient). Django 6 exige version_info >= (2, 2, 1)."""
import pymysql

pymysql.install_as_MySQLdb()

import MySQLdb  # noqa: E402

MySQLdb.version_info = (2, 2, 7, "final", 0)
