from enum import Enum, auto

import jose.exceptions
import uvicorn
from fastapi import FastAPI, Body
from fastapi.responses import PlainTextResponse
import sqlite3
from jose import jwt

import config

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


def check_existence(username: str):
    return db_action(
        '''
            SELECT * FROM users WHERE username = ?
        ''',
        (username, ),
        DBAction.fetchone,
    )


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
def index(token):
    try:
        user_id = jwt.decode(token, config.SECRET_CODE, algorithms=['SH256'])['id']
    except jose.exceptions.JWTError:
        return {
            'error': 'Invalid token'
        }
    user = db_action(
            '''
                SELECT * FROM users WHERE id = ?
            ''',
            (user_id),
            DBAction.fetchone,
        )
    return user[0]


@app.post('/signup')
def signup(username: str = Body(...), password: str = Body(...)):
    if check_existence(username) is not None:
        return PlainTextResponse('User with this username already exists.')
    return db_action(
        '''
            INSERT INTO users (username, password) VALUES (?, ?)
        ''',
        (username, password),
        DBAction.commit,
    )

@app.post('/login')
def login(username: str = Body(...), password: str = Body(...)):
    user = db_action(
        '''
            SELECT * FROM users WHERE username = ? AND password = ?
        ''',
        (username, password),
        DBAction.fetchone,
    )
    if not user:
        return {
            'error': 'User not found'
        }

    token = jwt.encode({
        'id': user[0]
    }, config.SECRET_CODE)
    return {
        'token': token
    }


uvicorn.run(app)

