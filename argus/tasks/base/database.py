from datetime import datetime, timezone

from peewee import CharField, DateTimeField, Model, SqliteDatabase, TextField

db = SqliteDatabase('tasks.db')


def get_current_utc_time():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TaskResult(Model):
    task_name = CharField()
    result = TextField()  # Store the result as a JSON-encoded string
    created_at = DateTimeField(
        default=get_current_utc_time
    )  # UTC timestamp for entry creation

    class Meta:
        database = db


def init_database() -> None:
    with db:
        db.create_tables([TaskResult])
