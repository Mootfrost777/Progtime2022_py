import json

from utils import db_action, DBAction, run_code


class Task:
    id: int
    name: str
    description: str
    tests: str

    def __init__(self, task_id: int, name: str, description: str, tests: str):
        self.id = task_id
        self.name = name
        self.description = description
        self.tests = tests

    @staticmethod
    def create(name: str, description: str, tests: str) -> 'Task':
        """Create a new task"""
        task_id = db_action(
            '''
                INSERT INTO tasks (name, description, tests) VALUES (?, ?, ?)
            ''',
            (name, description, tests),
            DBAction.commit,
        )
        task = Task(task_id, name, description, tests)
        return task

    @staticmethod
    def get(task_id: int) -> 'Task':
        """Get a task by id"""
        db_task = db_action(
            '''
                SELECT * FROM tasks WHERE id = ?
            ''',
            (task_id,),
            DBAction.fetchone,
        )
        if db_task is None:
            return None
        task = Task(db_task[0], db_task[1], db_task[2], db_task[3])
        return task

    @staticmethod
    def all() -> list:
        """Get all tasks"""
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
        """Save the task to the database"""
        db_action(
            '''
                UPDATE tasks SET name = ?, description = ?, tests = ? WHERE id = ?
            ''',
            (self.name, self.description, self.tests, self.id),
            DBAction.commit,
        )

    def check_solution(self, code: str) -> dict:
        """Check if the task solution is correct"""
        tests = json.loads(self.tests)

        tests_completed = 0
        for test in tests:
            program_input = test['input']
            expected_output = test['output']
            result = run_code(code, program_input)
            result = result.replace('\r', '')
            if result[-1] == '\n':
                result = result[:-1]
            if result != expected_output:
                return {
                    'status': False,
                    'user_output': result,
                    'expected_output': expected_output,
                    'tests_completed': tests_completed,
                    'tests_total': len(tests),
                }
            tests_completed += 1
        return {
            'status': True,
        }

