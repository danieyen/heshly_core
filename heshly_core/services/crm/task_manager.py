from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid



class TaskStatus(str, Enum):

    OPEN = "open"

    IN_PROGRESS = "in_progress"

    COMPLETED = "completed"

    CANCELLED = "cancelled"



class TaskPriority(str, Enum):

    LOW = "low"

    MEDIUM = "medium"

    HIGH = "high"

    URGENT = "urgent"



@dataclass(slots=True)
class CRMTask:

    task_id: str

    business_id: str

    title: str

    related_type: str

    related_id: str


    assigned_to: str | None = None


    priority: TaskPriority = (
        TaskPriority.MEDIUM
    )


    status: TaskStatus = (
        TaskStatus.OPEN
    )


    due_date: datetime | None = None


    created_at: datetime = field(
        default_factory=datetime.utcnow
    )


    completed_at: datetime | None = None



class TaskManagementError(Exception):
    pass



class TaskManager:


    def __init__(self):

        self.tasks: list[CRMTask] = []



    def create_task(
        self,
        business_id: str,
        title: str,
        related_type: str,
        related_id: str,
        assigned_to: str | None = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> CRMTask:


        if not business_id:

            raise TaskManagementError(
                "Business ID is required."
            )


        if not title:

            raise TaskManagementError(
                "Task title is required."
            )


        task = CRMTask(

            task_id=self._generate_id(),

            business_id=business_id,

            title=title,

            related_type=related_type,

            related_id=related_id,

            assigned_to=assigned_to,

            priority=priority,

        )


        self.tasks.append(task)


        return task



    def complete_task(
        self,
        task_id: str,
    ) -> CRMTask:


        for task in self.tasks:

            if task.task_id == task_id:

                task.status = (
                    TaskStatus.COMPLETED
                )

                task.completed_at = (
                    datetime.utcnow()
                )

                return task


        raise TaskManagementError(
            "Task not found."
        )



    def get_tasks(
        self,
        related_id: str,
    ) -> list[CRMTask]:


        return [

            task

            for task in self.tasks

            if task.related_id == related_id

        ]



    def _generate_id(self):

        return (
            f"TASK-{uuid.uuid4().hex[:8].upper()}"
        )