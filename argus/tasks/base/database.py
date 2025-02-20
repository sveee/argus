from datetime import datetime, timezone

from peewee import CharField, DateTimeField, Model, SqliteDatabase, TextField

db = SqliteDatabase('tasks.db')


def get_current_utc_time():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TaskResult(Model):
    task_id = CharField()
    result = TextField()
    created_at = DateTimeField(default=get_current_utc_time)

    class Meta:
        database = db


class RunningTask(Model):
    task_id = CharField(unique=True)
    serialized_data = TextField()
    last_updated = DateTimeField(default=get_current_utc_time)

    class Meta:
        database = db


def init_database() -> None:
    db.create_tables([RunningTask, TaskResult])
