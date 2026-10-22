#!/usr/bin/env python3
"""Safe CLI for the UselessPope CONFIG / STATS tables.

Reads credentials from ~/.UselessPope-Broker.ini (section [database]) like
python/config.py does, but uses parameterized queries instead of string
interpolation.

Usage:
  db_query.py get <key>                 # CONFIG value (prints "" if missing)
  db_query.py set <key> <value>         # CONFIG upsert (update or insert)
  db_query.py get-stat <key>            # STATS value
  db_query.py set-stat <key> <value>    # STATS upsert
  db_query.py list                      # dump CONFIG table
  db_query.py list-stats                # dump STATS table

Exit code is 0 on success, 1 on error or missing key (get/get-stat).
"""
import configparser
import os
import sys
from pathlib import Path

INI = os.path.join(os.getenv("HOME", ""), ".UselessPope-Broker.ini")
HIST_USER = "papst"


def load_ini():
    if not Path(INI).exists():
        raise SystemExit("missing ini file: {}".format(INI))
    parser = configparser.ConfigParser()
    parser.read(INI)
    try:
        return {
            "user": parser.get("database", "username"),
            "passwd": parser.get("database", "password"),
            "db": parser.get("database", "instance"),
        }
    except (configparser.NoSectionError, configparser.NoOptionError) as exc:
        raise SystemExit("invalid ini file {}: {}".format(INI, exc))


def connect():
    try:
        import MySQLdb
    except ImportError as exc:
        raise SystemExit("MySQLdb is not installed: {}".format(exc))
    creds = load_ini()
    return MySQLdb.connect(host="localhost", **creds)


def get_one(conn, table, key):
    with conn.cursor() as cur:
        cur.execute("SELECT `value` FROM `{}` WHERE `key` = %s".format(table), (key,))
        row = cur.fetchone()
    conn.commit()
    return None if row is None else row[0]


def upsert(conn, table, key, value):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM `{}` WHERE `key` = %s".format(table), (key,))
        exists = cur.fetchone()[0] > 0
        if exists:
            cur.execute(
                "UPDATE `{}` SET `value` = %s, `hist_ae_zeit` = CURRENT_TIMESTAMP(), "
                "`hist_ae_user` = %s WHERE `key` = %s".format(table),
                (value, HIST_USER, key),
            )
        else:
            cur.execute(
                "INSERT INTO `{}` (`key`, `value`, `hist_an_user`, `hist_ae_user`, "
                "`hist_lo_user`) VALUES (%s, %s, %s, %s, %s)".format(table),
                (key, value, HIST_USER, HIST_USER, HIST_USER),
            )
    conn.commit()


def dump(conn, table):
    with conn.cursor() as cur:
        cur.execute("SELECT `key`, `value` FROM `{}` ORDER BY `key`".format(table))
        for key, value in cur.fetchall():
            print("{}\t{}".format(key, value))
    conn.commit()


def main(argv):
    if len(argv) < 1:
        print(__doc__)
        return 2

    cmd = argv[0]

    if cmd == "get":
        if len(argv) != 2:
            return usage()
        conn = connect()
        value = get_one(conn, "CONFIG", argv[1])
        conn.close()
        if value is None:
            sys.stderr.write("CONFIG key not found: {}\n".format(argv[1]))
            return 1
        print(value)
        return 0

    if cmd == "set":
        if len(argv) != 3:
            return usage()
        conn = connect()
        upsert(conn, "CONFIG", argv[1], argv[2])
        conn.close()
        return 0

    if cmd == "get-stat":
        if len(argv) != 2:
            return usage()
        conn = connect()
        value = get_one(conn, "STATS", argv[1])
        conn.close()
        if value is None:
            sys.stderr.write("STATS key not found: {}\n".format(argv[1]))
            return 1
        print(value)
        return 0

    if cmd == "set-stat":
        if len(argv) != 3:
            return usage()
        conn = connect()
        upsert(conn, "STATS", argv[1], argv[2])
        conn.close()
        return 0

    if cmd == "list":
        conn = connect()
        dump(conn, "CONFIG")
        conn.close()
        return 0

    if cmd == "list-stats":
        conn = connect()
        dump(conn, "STATS")
        conn.close()
        return 0

    return usage()


def usage():
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
