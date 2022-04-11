import os
import string
import random
import subprocess
from enum import Enum, auto
import sqlite3


def run_code(code: str):
    """Runs code in a subprocess"""
    filename = ''.join(random.choices(string.ascii_letters, k=10))
    filename = f'codes/{filename}.py'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(code)

    process = subprocess.Popen(
        ['python', filename],
        stdout=subprocess.PIPE,
    )
    process.wait()
    stdout = process.stdout.read()
    print(stdout)

    os.remove(filename)
    return stdout.decode()


class DBAction(Enum):
    fetchone = auto()
    fetchall = auto()
    commit = auto()


def db_action(sql: str, args: tuple, action: DBAction):
    """Runs a query on the database"""
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()

    cursor.execute(sql, args)
    if action == DBAction.fetchone:
        result = cursor.fetchone()
    elif action == DBAction.fetchall:
        result = cursor.fetchall()
    elif action == DBAction.commit:
        conn.commit()
        result = cursor.lastrowid

    cursor.close()
    conn.close()

    return result
