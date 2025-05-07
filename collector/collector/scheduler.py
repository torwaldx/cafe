import subprocess
import schedule
import time

from shared.logging_config import setup_logger
from shared.models.task import Task

logger = setup_logger()

class DbScheduler:
    def __init__(self, check_interval: int = 10):
        self.check_interval = check_interval
        self.scheduled_jobs = []
        self.task_cache = {}

    def run_script(self, task: Task):
        try:
            logger.info("Запуск задачи: %s", task.task)
            result = subprocess.run(
                ["uv", "run", "-m", task.script_module], capture_output=True, text=True
            )
            if result.returncode == 0:
                logger.info(
                    "Задача '%s' успешно выполнена. Результат: \n...\n%s\n------------------------",
                    task.task,
                    "\n".join(result.stderr.strip().splitlines()[-2:]),
                )
            else:
                logger.error(
                    "Задача %s завершена с ошибкой (код %s). Ошибка: %s",
                    task.task,
                    result.returncode,
                    result.stderr.strip(),
                )
        except Exception as e:
            logger.exception("Исключение при выполнении задачи '%s': %s", task.task, str(e))

    def clear_schedule(self):
        for job in self.scheduled_jobs:
            schedule.cancel_job(job)
        self.scheduled_jobs = []

    def apply_schedule(self, tasks: list[Task]):
        self.clear_schedule()
        for task in tasks:
            self.scheduled_jobs.append(task.get_job(self.run_script))


    async def check_for_updates(self):
        tasks = await Task.objects.all(is_active=True)
        task_snapshot = {(t.id, t.script_module, t.schedule_time) for t in tasks}
        if task_snapshot != self.task_cache:
            logger.info("Обнаружены изменения в задачах. Обновляю расписание.")
            self.apply_schedule(tasks)
            self.task_cache = task_snapshot

    async def start(self):
        logger.info("Запуск планировщика")
        db = Task.ormar_config.database
        await db.connect()
        try:
            while True:
                await self.check_for_updates()
                schedule.run_pending()
                time.sleep(self.check_interval)
        finally:
            await db.disconnect()


if __name__ == "__main__":
    import asyncio
    scheduler = DbScheduler()
    asyncio.run(scheduler.start())
