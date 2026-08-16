from __future__ import annotations

from datetime import date
from pathlib import Path

from backend.excel import export_excel, parse_excel
from backend.models import Project, ProjectSnapshot, TaskCreate
from backend.scheduler import schedule

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "sample" / "import-tests"
ASSIGNEES = ["Anna", "Elena", "Mikhail", "Daria", "Pavel"]
ACTIVITIES = [
    "Scope definition",
    "Protocol design",
    "Material preparation",
    "Method development",
    "Experiment execution",
    "Quality review",
    "Data analysis",
    "Evidence review",
    "Documentation",
    "Readiness review",
]


def dependency_indices(index: int) -> list[int]:
    """Create parallel pairs followed by merge points without introducing cycles."""
    if index == 0:
        return []
    position = index % 5
    if position in (1, 2):
        return [index - position]
    if position == 3:
        return [index - 2, index - 1]
    return [index - 1]


def generated_snapshot(task_count: int, title: str) -> ProjectSnapshot:
    ids = [f"task-{index + 1:03d}" for index in range(task_count)]
    tasks = []
    for index, task_id in enumerate(ids):
        activity = ACTIVITIES[index % len(ACTIVITIES)]
        phase = index // 5 + 1
        tasks.append(
            TaskCreate(
                id=task_id,
                name=f"Phase {phase:02d} - {activity}",
                description=f"Import test activity {index + 1} for {title}.",
                assignees=[ASSIGNEES[index % len(ASSIGNEES)]],
                duration=(index % 7) + 1,
                predecessor_ids=[ids[item] for item in dependency_indices(index)],
            )
        )
    return ProjectSnapshot(name=title, start_date=date(2026, 9, 1), tasks=tasks)


def quick_snapshot() -> ProjectSnapshot:
    tasks = [
        TaskCreate(
            id="requirements",
            name="Requirements",
            description="Agree scope and acceptance criteria.",
            assignees=["Anna"],
            duration=2,
        ),
        TaskCreate(
            id="design",
            name="Solution design",
            description="Prepare the implementation design.",
            assignees=["Elena"],
            duration=3,
            predecessor_ids=["requirements"],
        ),
        TaskCreate(
            id="build",
            name="Implementation",
            description="Build and review the solution.",
            assignees=["Mikhail", "Daria"],
            duration=5,
            predecessor_ids=["design"],
        ),
        TaskCreate(
            id="release",
            name="Release",
            description="Complete final verification and release.",
            assignees=["Daria"],
            duration=1,
            predecessor_ids=["build"],
        ),
    ]
    return ProjectSnapshot(name="Quick import test", start_date=date(2026, 9, 1), tasks=tasks)


def internal_tracker_task(
    task_id: str,
    name: str,
    description: str,
    assignees: list[str],
    duration: int,
    predecessor_ids: list[str] | None = None,
) -> TaskCreate:
    return TaskCreate(
        id=task_id,
        name=name,
        description=description,
        assignees=assignees,
        duration=duration,
        predecessor_ids=predecessor_ids or [],
    )


def russian_small_snapshot() -> ProjectSnapshot:
    rows = [
        ("s01", "Сбор требований", "Собрать ожидания внутренних подразделений.", ["Anna"], 3, []),
        (
            "s02",
            "Согласование требований",
            "Утвердить границы первой версии продукта.",
            ["Elena"],
            2,
            ["s01"],
        ),
        (
            "s03",
            "Проектирование архитектуры",
            "Определить компоненты и контракты системы.",
            ["Mikhail"],
            4,
            ["s02"],
        ),
        (
            "s04",
            "Проектирование интерфейса",
            "Подготовить макеты основных экранов.",
            ["Daria"],
            4,
            ["s03"],
        ),
        (
            "s05",
            "Реализация серверной части",
            "Создать программный интерфейс, хранение и бизнес-правила.",
            ["Mikhail"],
            6,
            ["s04"],
        ),
        (
            "s06",
            "Реализация клиентской части",
            "Создать интерфейс управления задачами.",
            ["Daria"],
            6,
            ["s05"],
        ),
        (
            "s07",
            "Приёмочное тестирование",
            "Проверить основные пользовательские сценарии.",
            ["Pavel"],
            3,
            ["s06"],
        ),
        (
            "s08",
            "Ввод в эксплуатацию",
            "Опубликовать сервис и передать инструкции.",
            ["Elena"],
            2,
            ["s07"],
        ),
    ]
    return ProjectSnapshot(
        name="Малый линейный план внутреннего трекера",
        start_date=date(2026, 9, 1),
        tasks=[internal_tracker_task(*row) for row in rows],
    )


def russian_medium_snapshot() -> ProjectSnapshot:
    rows = [
        (
            "m01",
            "Инициация проекта",
            "Зафиксировать цели, владельца и критерии успеха.",
            ["Anna"],
            2,
            [],
        ),
        (
            "m02",
            "Интервью с пользователями",
            "Изучить работу команд и основные затруднения.",
            ["Anna", "Daria"],
            4,
            ["m01"],
        ),
        (
            "m03",
            "Аудит текущих процессов",
            "Описать используемые таблицы и каналы коммуникации.",
            ["Elena"],
            3,
            ["m01"],
        ),
        (
            "m04",
            "Формирование требований",
            "Собрать единый перечень функциональных требований.",
            ["Anna"],
            4,
            ["m02", "m03"],
        ),
        (
            "m05",
            "Информационная архитектура",
            "Спроектировать структуру проектов, задач и фильтров.",
            ["Daria"],
            3,
            ["m04"],
        ),
        (
            "m06",
            "Архитектура решения",
            "Определить сервисы, данные и интеграционные контракты.",
            ["Mikhail"],
            4,
            ["m04"],
        ),
        (
            "m07",
            "Интерактивный прототип",
            "Проверить основные пользовательские потоки на макете.",
            ["Daria", "Anna"],
            5,
            ["m05"],
        ),
        (
            "m08",
            "Каркас серверной части",
            "Создать программный интерфейс и базовые модели предметной области.",
            ["Mikhail"],
            5,
            ["m06"],
        ),
        (
            "m09",
            "Каркас клиентской части",
            "Создать навигацию и базовые компоненты интерфейса.",
            ["Daria"],
            5,
            ["m06", "m07"],
        ),
        (
            "m10",
            "Корпоративный вход",
            "Подключить аутентификацию и основные роли.",
            ["Mikhail", "Pavel"],
            4,
            ["m08"],
        ),
        (
            "m11",
            "Модуль управления задачами",
            "Реализовать создание, изменение и назначение задач.",
            ["Mikhail", "Daria"],
            7,
            ["m08", "m09"],
        ),
        (
            "m12",
            "Комментарии и уведомления",
            "Добавить обсуждения и уведомления об изменениях.",
            ["Daria"],
            5,
            ["m10", "m11"],
        ),
        (
            "m13",
            "Поиск и фильтры",
            "Реализовать поиск и сохранённые представления.",
            ["Daria"],
            4,
            ["m11"],
        ),
        (
            "m14",
            "Пробная миграция данных",
            "Перенести тестовый набор задач из старых таблиц.",
            ["Elena", "Mikhail"],
            5,
            ["m08"],
        ),
        (
            "m15",
            "Интеграционное тестирование",
            "Проверить совместную работу всех модулей.",
            ["Pavel"],
            5,
            ["m12", "m13", "m14"],
        ),
        (
            "m16",
            "Проверка безопасности",
            "Проверить роли, доступ и журналирование действий.",
            ["Pavel", "Mikhail"],
            3,
            ["m10", "m15"],
        ),
        (
            "m17",
            "Нагрузочное тестирование",
            "Проверить работу на расчётном объёме задач.",
            ["Pavel"],
            3,
            ["m15"],
        ),
        (
            "m18",
            "Пилотная эксплуатация",
            "Провести пилот с одной внутренней командой.",
            ["Anna", "Elena"],
            7,
            ["m16", "m17"],
        ),
        (
            "m19",
            "Обучение и инструкции",
            "Подготовить справку и обучить пользователей пилота.",
            ["Anna"],
            3,
            ["m18"],
        ),
        (
            "m20",
            "Промышленный запуск",
            "Открыть сервис целевым подразделениям.",
            ["Elena", "Pavel"],
            2,
            ["m18", "m19"],
        ),
    ]
    return ProjectSnapshot(
        name="Средний план внутреннего трекера",
        start_date=date(2026, 9, 1),
        tasks=[internal_tracker_task(*row) for row in rows],
    )


def russian_large_snapshot() -> ProjectSnapshot:
    rows = [
        ("l01", "Паспорт проекта", "Зафиксировать цели, бюджет и ответственных.", ["Anna"], 2, []),
        (
            "l02",
            "Анализ заинтересованных сторон",
            "Определить группы пользователей и владельцев процессов.",
            ["Anna"],
            3,
            ["l01"],
        ),
        (
            "l03",
            "Инвентаризация текущих систем",
            "Описать таблицы, сервисы и источники данных.",
            ["Elena"],
            4,
            ["l01"],
        ),
        (
            "l04",
            "Требования безопасности",
            "Согласовать доступ, аудит и размещение данных.",
            ["Pavel"],
            4,
            ["l01"],
        ),
        (
            "l05",
            "Исследование пользователей",
            "Провести интервью и наблюдение за работой команд.",
            ["Anna", "Daria"],
            5,
            ["l02"],
        ),
        (
            "l06",
            "Требования к интеграциям",
            "Определить системы для обмена данными и уведомлений.",
            ["Elena", "Mikhail"],
            4,
            ["l03"],
        ),
        (
            "l07",
            "Продуктовые требования",
            "Сформировать сценарии и критерии первой версии.",
            ["Anna"],
            5,
            ["l02", "l03", "l05", "l06"],
        ),
        (
            "l08",
            "Целевая архитектура",
            "Спроектировать сервисы, хранение и контракты.",
            ["Mikhail", "Pavel"],
            5,
            ["l03", "l04", "l06", "l07"],
        ),
        (
            "l09",
            "Модель данных",
            "Описать проекты, задачи, связи и историю изменений.",
            ["Mikhail"],
            4,
            ["l07", "l08"],
        ),
        (
            "l10",
            "Модель ролей и прав",
            "Определить полномочия сотрудников и руководителей.",
            ["Pavel", "Anna"],
            4,
            ["l04", "l07"],
        ),
        (
            "l11",
            "Дизайн-система",
            "Подготовить компоненты и правила интерфейса.",
            ["Daria"],
            5,
            ["l05", "l07"],
        ),
        (
            "l12",
            "Прототип интерфейса",
            "Собрать кликабельные сценарии управления задачами.",
            ["Daria", "Anna"],
            6,
            ["l10", "l11"],
        ),
        (
            "l13",
            "Тестирование прототипа",
            "Проверить прототип с представителями подразделений.",
            ["Anna", "Daria"],
            4,
            ["l12"],
        ),
        (
            "l14",
            "Каркас серверного приложения",
            "Создать основу программного интерфейса и бизнес-слоя.",
            ["Mikhail"],
            6,
            ["l08"],
        ),
        (
            "l15",
            "Каркас клиентского приложения",
            "Создать навигацию и основу интерфейса.",
            ["Daria"],
            6,
            ["l08", "l11"],
        ),
        (
            "l16",
            "Конвейер сборки и поставки",
            "Настроить проверки и развёртывание по средам.",
            ["Pavel"],
            4,
            ["l08"],
        ),
        (
            "l17",
            "Мониторинг и журналирование",
            "Добавить метрики, логи и оповещения.",
            ["Pavel", "Mikhail"],
            4,
            ["l14", "l16"],
        ),
        (
            "l18",
            "Корпоративная аутентификация",
            "Подключить принятый в компании способ входа.",
            ["Mikhail", "Pavel"],
            5,
            ["l10", "l14"],
        ),
        (
            "l19",
            "Справочник сотрудников",
            "Реализовать команды, роли и доступность сотрудников.",
            ["Mikhail"],
            5,
            ["l09", "l18"],
        ),
        (
            "l20",
            "Модуль проектов",
            "Реализовать создание и настройку проектов.",
            ["Mikhail", "Daria"],
            6,
            ["l09", "l14"],
        ),
        (
            "l21",
            "Модуль задач",
            "Реализовать карточки, исполнителей и сроки.",
            ["Mikhail", "Daria"],
            8,
            ["l09", "l14", "l15"],
        ),
        (
            "l22",
            "Статусы и рабочие процессы",
            "Добавить настраиваемые статусы и переходы.",
            ["Daria", "Mikhail"],
            5,
            ["l10", "l21"],
        ),
        (
            "l23",
            "Зависимости и подзадачи",
            "Добавить иерархию и связи между задачами.",
            ["Mikhail"],
            6,
            ["l21", "l22"],
        ),
        (
            "l24",
            "Комментарии и упоминания",
            "Реализовать обсуждения внутри задач.",
            ["Daria"],
            5,
            ["l18", "l19", "l21"],
        ),
        (
            "l25",
            "Центр уведомлений",
            "Добавить настраиваемые уведомления о событиях.",
            ["Daria", "Pavel"],
            5,
            ["l17", "l24"],
        ),
        (
            "l26",
            "Поиск и представления",
            "Реализовать фильтры и сохранённые представления.",
            ["Daria"],
            5,
            ["l19", "l20", "l21"],
        ),
        (
            "l27",
            "Отчёты руководителя",
            "Добавить отчёты о сроках и загрузке команды.",
            ["Anna", "Daria"],
            6,
            ["l20", "l21", "l22"],
        ),
        (
            "l28",
            "Журнал аудита",
            "Сохранять значимые действия пользователей.",
            ["Pavel", "Mikhail"],
            5,
            ["l17", "l18", "l21"],
        ),
        (
            "l29",
            "Импорт из старого трекера",
            "Подготовить перенос проектов и пользователей.",
            ["Elena", "Mikhail"],
            6,
            ["l03", "l09", "l19", "l20"],
        ),
        (
            "l30",
            "Очистка исходных данных",
            "Устранить дубли и некорректные значения.",
            ["Elena"],
            5,
            ["l29"],
        ),
        (
            "l31",
            "Пробная миграция",
            "Перенести копию данных и сверить результат.",
            ["Elena", "Mikhail", "Pavel"],
            6,
            ["l23", "l30"],
        ),
        (
            "l32",
            "Интеграция с календарём",
            "Добавить сроки задач в корпоративный календарь.",
            ["Mikhail"],
            5,
            ["l06", "l18", "l21"],
        ),
        (
            "l33",
            "Интеграция с почтой",
            "Отправлять согласованные уведомления по электронной почте.",
            ["Mikhail", "Pavel"],
            4,
            ["l06", "l18", "l25"],
        ),
        (
            "l34",
            "Документация интерфейсов",
            "Описать программный интерфейс и правила интеграции.",
            ["Elena", "Mikhail"],
            4,
            ["l20", "l21", "l24"],
        ),
        (
            "l35",
            "Автоматические тесты",
            "Покрыть основные бизнес-правила и пользовательские пути.",
            ["Pavel"],
            7,
            ["l23", "l25", "l26", "l27"],
        ),
        (
            "l36",
            "Интеграционное тестирование",
            "Проверить модули, миграцию и внешние системы.",
            ["Pavel", "Mikhail"],
            7,
            ["l28", "l31", "l32", "l33", "l34", "l35"],
        ),
        (
            "l37",
            "Аудит безопасности",
            "Проверить права, данные и устойчивость к атакам.",
            ["Pavel"],
            5,
            ["l04", "l18", "l28", "l36"],
        ),
        (
            "l38",
            "Нагрузочное тестирование",
            "Проверить расчётную нагрузку и крупные проекты.",
            ["Pavel", "Mikhail"],
            5,
            ["l17", "l26", "l27", "l36"],
        ),
        (
            "l39",
            "Учение по восстановлению",
            "Проверить резервные копии и возврат сервиса.",
            ["Pavel", "Elena"],
            4,
            ["l16", "l17", "l31"],
        ),
        (
            "l40",
            "Подготовка пилотной среды",
            "Развернуть стабильную версию для пилота.",
            ["Pavel"],
            4,
            ["l16", "l36", "l37", "l38", "l39"],
        ),
        (
            "l41",
            "Учебные материалы",
            "Подготовить инструкции и сценарии обучения.",
            ["Anna", "Daria"],
            4,
            ["l13", "l27", "l34"],
        ),
        (
            "l42",
            "Обучение пилотной группы",
            "Провести занятия и собрать первые вопросы.",
            ["Anna", "Elena"],
            3,
            ["l40", "l41"],
        ),
        (
            "l43",
            "Пилотная эксплуатация",
            "Проверить продукт на реальных проектах.",
            ["Anna", "Elena", "Pavel"],
            10,
            ["l42"],
        ),
        (
            "l44",
            "Исправления по итогам пилота",
            "Закрыть критичные замечания пользователей.",
            ["Mikhail", "Daria", "Pavel"],
            7,
            ["l43"],
        ),
        (
            "l45",
            "Промышленный запуск",
            "Перенести данные и открыть сервис подразделениям.",
            ["Anna", "Elena", "Mikhail", "Daria", "Pavel"],
            3,
            ["l37", "l38", "l39", "l44"],
        ),
    ]
    return ProjectSnapshot(
        name="Крупный план внутреннего трекера",
        start_date=date(2026, 9, 1),
        tasks=[internal_tracker_task(*row) for row in rows],
    )


def russian_fixtures() -> list[tuple[str, ProjectSnapshot]]:
    return [
        ("05-ru-small-linear-8-tasks.xlsx", russian_small_snapshot()),
        ("06-ru-medium-20-tasks.xlsx", russian_medium_snapshot()),
        ("07-ru-large-complex-45-tasks.xlsx", russian_large_snapshot()),
    ]


def write_and_verify(filename: str, snapshot: ProjectSnapshot, language: str = "en") -> None:
    tasks = schedule(snapshot)
    project = Project(name=snapshot.name, start_date=snapshot.start_date, tasks=tasks)
    content = export_excel(project, language=language)
    target = OUTPUT_DIR / filename
    target.write_bytes(content)
    imported = parse_excel(content, snapshot.name, snapshot.start_date)
    assert len(imported.tasks) == len(snapshot.tasks)
    assert [task.name for task in imported.tasks] == [task.name for task in snapshot.tasks]
    schedule(imported)
    print(f"created {target.name}: {len(imported.tasks)} tasks")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fixtures = [
        ("01-quick-4-tasks.xlsx", quick_snapshot()),
        ("02-small-10-tasks.xlsx", generated_snapshot(10, "Small import test")),
        ("03-medium-25-tasks.xlsx", generated_snapshot(25, "Medium import test")),
        ("04-large-60-tasks.xlsx", generated_snapshot(60, "Large import test")),
    ]
    for filename, snapshot in fixtures:
        write_and_verify(filename, snapshot)
    for filename, snapshot in russian_fixtures():
        write_and_verify(filename, snapshot, language="ru")


if __name__ == "__main__":
    main()
