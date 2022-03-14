from enum import Enum, auto

import uvicorn
from fastapi import FastAPI, Body, Header, Depends
from fastapi.responses import HTMLResponse
from fastapi.exceptions import HTTPException

import sqlite3

import jose.exceptions
from jose import jwt

import config  # import secret code

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


def get_user(authorization: str = Header(...)):
    try:
        user_id = jwt.decode(authorization, config.SECRET_CODE, algorithms=['SH256'])['id']
    except jose.exceptions.JWTError:
        raise HTTPException(status_code=400, detail='Invalid token')
    user = db_action(
            '''
                SELECT * FROM users WHERE id = ?
            ''',
            (user_id,),
            DBAction.fetchone,
        )
    return user


@app.get('/')
def index():
    with open('index.html', 'r', encoding='UTF-8') as f:
        data = f.read()
    return HTMLResponse(data)  # return home page


@app.post('/signup')
def signup(username: str = Body(...), password: str = Body(...)):
    if check_existence(username) is not None:
        raise HTTPException(status_code=409, detail='Username already exists')
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
        raise HTTPException(status_code=404, detail='User not found')

    token = jwt.encode({
        'id': user[0]
    }, config.SECRET_CODE)
    return {
        'token': token
    }


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)

