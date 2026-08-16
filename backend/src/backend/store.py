from copy import deepcopy
from dataclasses import dataclass, field

from backend.models import Project, ProjectSnapshot, TaskCreate, TaskUpdate
from backend.scheduler import PlanValidationError, schedule
from backend.seed import seed_snapshot


@dataclass
class ProjectStore:
    snapshot: ProjectSnapshot = field(default_factory=seed_snapshot)
    revision: int = 1
    undo_snapshot: ProjectSnapshot | None = None

    def project(self) -> Project:
        return Project(
            name=self.snapshot.name,
            start_date=self.snapshot.start_date,
            tasks=schedule(self.snapshot),
            revision=self.revision,
        )

    def replace(self, snapshot: ProjectSnapshot) -> Project:
        schedule(snapshot)
        self.undo_snapshot = deepcopy(self.snapshot)
        self.snapshot = deepcopy(snapshot)
        self.revision += 1
        return self.project()

    def add(self, item: TaskCreate) -> Project:
        candidate = deepcopy(self.snapshot)
        candidate.tasks.append(item)
        return self.replace(candidate)

    def update(self, task_id: str, update: TaskUpdate) -> Project:
        candidate = deepcopy(self.snapshot)
        for index, task in enumerate(candidate.tasks):
            if task.id == task_id:
                candidate.tasks[index] = TaskCreate(
                    **(task.model_dump() | update.model_dump(exclude_none=True))
                )
                return self.replace(candidate)
        raise KeyError(task_id)

    def delete(self, task_id: str) -> Project:
        candidate = deepcopy(self.snapshot)
        if not any(task.id == task_id for task in candidate.tasks):
            raise KeyError(task_id)
        candidate.tasks = [
            task.model_copy(
                update={
                    "predecessor_ids": [
                        predecessor_id
                        for predecessor_id in task.predecessor_ids
                        if predecessor_id != task_id
                    ]
                }
            )
            for task in candidate.tasks
            if task.id != task_id
        ]
        return self.replace(candidate)

    def reset(self) -> Project:
        return self.replace(seed_snapshot())

    def undo(self) -> Project:
        if self.undo_snapshot is None:
            raise PlanValidationError("There is nothing to undo")
        previous = self.undo_snapshot
        self.undo_snapshot = deepcopy(self.snapshot)
        self.snapshot = previous
        self.revision += 1
        return self.project()


store = ProjectStore()
