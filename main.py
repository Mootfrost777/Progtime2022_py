
import sqlite3

import jose.exceptions
import uvicorn
from fastapi import FastAPI, Body, Header, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse
from jose import jwt

import config
from utils import db_action, DBAction, run_code
from task_checker import Task

app = FastAPI()


@app.on_event('startup')
def create_db():
    """Creates database"""
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE if NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username VARCHAR NOT NULL,
            password VARCHAR NOT NULL
        );
    ''')
    cursor.execute('''
            CREATE TABLE if NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            description VARCHAR,
            result VARCHAR NOT NULL
        );
    ''')

    cursor.close()
    conn.close()
    task = Task.get(1)


def get_user(authorization: str = Header(...)):
    """Returns user"""
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
    """Returns html file"""
    with open(f'html/{name}.html', 'r', encoding='utf-8') as f:
        return HTMLResponse(f.read())


@app.get('/')
def index():
    """Returns index page"""
    return send_html('index')


@app.get('/tasks')
def tasks():
    """Returns tasks page"""
    return send_html('tasks')


@app.get('/login')
def login_page():
    """Returns login page"""
    return send_html('login')


@app.get('/signup')
def register_page():
    """Returns signup page"""
    return send_html('signup')


@app.get('/api/ping')
def ping(user: list = Depends(get_user)):
    """Pings server"""
    return {
        'response': 'Pong',
        'username': user[1],
    }


@app.post('/api/execute')
def execute(user: list = Depends(get_user), code: str = Body(..., embed=True)):
    """Executes code"""
    return {
        'result': run_code(code)
    }


@app.post('/api/login')
def login(username: str = Body(...), password: str = Body(...)):
    """Logs in user"""
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
    """Registers user"""
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


@app.get('/api/get_tasks')
def get_tasks(user: list = Depends(get_user)):
    """Returns all tasks"""
    return Task.all()


@app.post('/api/send_task')
def send_task(user: list = Depends(get_user), task_id: int = Body(...), code: str = Body(...)):
    """Checks task"""
    task = Task.get(task_id)
    return {
        'result': task.check_solution(code)
    }


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
