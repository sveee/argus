from argus.logger_setup import setup_logging
from argus.tasks.base.database import init_database
from argus.tasks.base.task import TaskManager


def main() -> None:
    task_manager = TaskManager()
    task_manager.run()


if __name__ == '__main__':
    setup_logging()
    init_database()
    main()
