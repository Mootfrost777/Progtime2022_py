
from utils import db_action, DBAction, run_code


class Task:
    id: int
    name: str
    description: str
    result: str

    def __init__(self, task_id: int, name: str, description: str, result: str):
        self.id = task_id
        self.name = name
        self.description = description
        self.result = result

    @staticmethod
    def create(name: str, description: str, result: str) -> 'Task':
        task_id = db_action(
            '''
                INSERT INTO tasks (name, description, result) VALUES (?, ?, ?)
            ''',
            (name, description, result),
            DBAction.commit,
        )
        task = Task(task_id, name, description, result)
        return task

    @staticmethod
    def get(task_id: int) -> 'Task':
        db_task = db_action(
            '''
                SELECT * FROM tasks WHERE id = ?
            ''',
            (task_id,),
            DBAction.fetchone,
        )
        task = Task(db_task[0], db_task[1], db_task[2], db_task[3])
        return task

    @staticmethod
    def all() -> list:
        db_tasks = db_action(
            '''
                SELECT * FROM tasks
            ''',
            (),
            DBAction.fetchall,
        )
        tasks = []
        for task in db_tasks:
            tasks.append(Task(task[0], task[1], task[2], task[3]))
        return tasks

    def save(self):
        db_action(
            '''
                UPDATE tasks SET name = ?, description = ?, result = ? WHERE id = ?
            ''',
            (self.name, self.description, self.result, self.id),
            DBAction.commit,
        )

    def check_solution(self, code: str) -> bool:
        result = run_code(code)
        result = result.replace('\r', '')
        if result[-1] == '\n':
            result = result[:-1]
        print(repr(result))
        print(repr(self.result))
        return result == self.result
