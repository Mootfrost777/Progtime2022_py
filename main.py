from enum import Enum, auto

import uvicorn
from fastapi import FastAPI, Body
import sqlite3

app = FastAPI()


class DBAction(Enum):
    fetchone = auto()
    fetchall = auto()
    commit = auto()


def db_action(sql: str, args: tuple, action: DBAction):
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()

    cursor.execute(sql, args)
    if action == DBAction.fetchone:
        result = cursor.fetchone()
    elif action == DBAction.fetchall:
        result = cursor.fetchall()
    elif action == DBAction.commit:
        conn.commit()
        result = None

    cursor.close()
    conn.close()

    return result


@app.on_event('startup')
def create_db():
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE if NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username VARCHAR NOT NULL,
            password VARCHAR NOT NULL
        );
    ''')

    cursor.close()
    conn.close()


@app.get('/')
def index():
    return 'Hello, world!'


@app.post('/signup')
def signup(username: str = Body(...), password: str = Body(...)):
    return db_action(
        '''
            INSERT INTO users (username, password) VALUES (?, ?)
        ''',
        (username, password),
        DBAction.commit,
    )


@app.post('/login')
def login(username: str = Body(...), password: str = Body(...)):
    return db_action(
        '''
            SELECT * FROM users WHERE username = ? AND password = ?
        ''',
        (username, password),
        DBAction.fetchone,
    )


uvicorn.run(app)

