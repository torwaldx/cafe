from typing import Callable
import re
import ormar
import schedule
from pydantic import field_validator, model_validator

from .db import ormar_base_config

SCHEDULE_MAPPING = {
    "hour": lambda task, job: schedule.every(task.count)
    .hours.at(task.schedule_time[-3:])
    .do(job, task),

    "day": lambda task, job: schedule.every(task.count).days.at(task.schedule_time).do(job, task),
}
VALID_SCHEDULE_TYPES = SCHEDULE_MAPPING.keys()
TIME_PATTERN = r"^(:[0-5][0-9]|[0-1][0-9]:[0-5][0-9]|2[0-3]:[0-5][0-9])$"


class Task(ormar.Model):
    ormar_config = ormar_base_config.copy()

    id: int = ormar.Integer(primary_key=True)
    task: str = ormar.String(max_length=512)
    script_module: str = ormar.String(max_length=255)
    count: int = ormar.Integer(minimum=1, server_default="1")
    schedule_type: str = ormar.String(max_length=20, default="hour", server_default="hour")
    schedule_time: str = ormar.String(max_length=10, server_default=":00")
    is_active: bool = ormar.Boolean(default=True, server_default="1")

    @field_validator("schedule_type", mode="after")
    @classmethod
    def validate_schedule_type(cls, v):
        if v not in VALID_SCHEDULE_TYPES:
            raise ValueError(
                f"Недопустимый период запуска: {v}. Ожидается : {', '.join(VALID_SCHEDULE_TYPES)}"
            )
        return v

    @field_validator("schedule_time", mode="after")
    @classmethod
    def validate_schedule_time(cls, v):
        if not re.compile(TIME_PATTERN).match(v):
            raise ValueError(f"Неверный формат времени: {v}. Ожидается HH:MM или :MM.")
        return v

    @model_validator(mode="after")
    def time_compliance_check(self):
        if self.schedule_type != "hour" and len(self.schedule_time) <= 3:
            raise ValueError("Ожидаемый формат времени для данного типа расписания: HH:MM.")
        return self

    def get_job(self, job: Callable):
        return SCHEDULE_MAPPING[self.schedule_type](self, job)
