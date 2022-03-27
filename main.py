import sqlite3
from enum import Enum, auto

import jose.exceptions
import uvicorn
from fastapi import FastAPI, Body, Header, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse
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
        user_id = jwt.decode(authorization, config.SECRET_CODE, algorithms=['HS256'])['id']
    except jose.exceptions.JWTError:
        raise HTTPException(
            status_code=400,
            detail='Invalid token'
        )

    user = db_action(
        '''
            SELECT * FROM users WHERE id = ?
        ''',
        (user_id,),
        DBAction.fetchone,
    )
    return user


def send_html(name: str):
    with open(f'html/{name}.html', 'r', encoding='utf-8') as f:
        return HTMLResponse(f.read())


@app.get('/')
def index():
    return send_html('index')


@app.get('/login')
def login_page():
    return send_html('login')


@app.get('/signup')
def register_page():
    return send_html('signup')


@app.get('/api/ping')
def ping(user: list = Depends(get_user)):
    return {
        'response': 'Pong',
        'username': user[1],
    }


@app.post('/api/login')
def login(username: str = Body(...), password: str = Body(...)):
    user = db_action(
        '''
            SELECT * FROM users WHERE username = ? AND password = ?
        ''',
        (username, password),
        DBAction.fetchone,
    )
    if not user:
        raise HTTPException(
            status_code=404,
            detail='User not found'
        )

    token = jwt.encode({'id': user[0]}, config.SECRET_CODE, algorithm='HS256')
    return {
        'token': token
    }


@app.post('/api/signup')
def register(username: str = Body(...), password: str = Body(...)):
    user = db_action(
        '''
            SELECT * FROM users WHERE username = ?
        ''',
        (username,),
        DBAction.fetchone,
    )
    if user:
        raise HTTPException(
            status_code=400,
            detail='User already exists'
        )

    db_action(
        '''
            INSERT INTO users (username, password) VALUES (?, ?)
        ''',
        (username, password),
        DBAction.commit,
    )

    return {
        'message': 'Registration successful'
    }


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
