from fastapi import FastAPI, Body
from fastapi.responses import PlainTextResponse
import uvicorn
import sqlite3

app = FastAPI()


@app.on_event('startup')
def create_db():
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE if NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username VARCHAR NOT NULL,
            password VARCHAR NOT NULL
        )
    ''')
    cursor.close()
    conn.close()


@app.get('/')
def index():
    return PlainTextResponse('Any text :)')


@app.post('/login')
def login(username: str = Body(...), password: str = Body(...)):
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM users WHERE username = ? AND password = ?
    ''', (username, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


@app.post('/test')
def test():
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (username, password) VALUES ('1', '1')
    ''')
    user = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    return user


uvicorn.run(app)
