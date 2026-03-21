# PawPal+ — Final UML Class Diagram

> Copy the Mermaid block below into **https://mermaid.live**, then
> use **Export → PNG** to save `uml_final.png` in the project folder.

```mermaid
classDiagram
    direction TB

    class Owner {
        +String name
        +int available_minutes
        +List~String~ preferences
        +List~Pet~ pets
        +get_available_minutes() int
        +add_preference(preference) void
        +add_pet(pet) void
        +get_all_tasks() List~Task~
    }

    class Pet {
        +String name
        +String species
        +int age
        +String special_needs
        +List~Task~ tasks
        +get_profile() String
        +is_senior() bool
        +add_task(task) void
        +remove_task(title) void
    }

    class Task {
        +String title
        +int duration_minutes
        +String priority
        +String category
        +String preferred_time
        +bool completed
        +String frequency
        +date due_date
        +String pet_name
        +mark_complete() Task
        +is_high_priority() bool
        +to_dict() dict
    }

    class ScheduledTask {
        +String start_time
        +String end_time
        +String reason
        +display() String
        -_calculate_end_time() void
    }

    class Scheduler {
        +List~Task~ tasks
        +List~ScheduledTask~ schedule
        +int remaining_minutes
        +add_task(task) void
        +remove_task(title) void
        +prioritize_tasks() List~Task~
        +fits_in_time(task) bool
        +generate_schedule(start_time) List~ScheduledTask~
        +sort_by_time(scheduled_tasks)$ List~ScheduledTask~
        +filter_tasks(tasks, pet_name, completed)$ List~Task~
        +detect_conflicts() List~String~
        +explain_plan() String
    }

    Owner "1"      -->  "0..*" Pet          : owns
    Pet   "1"      o--  "0..*" Task         : has tasks
    Task            ..>        Task          : mark_complete() returns next occurrence
    Scheduler "1"  -->  "1"   Owner         : uses budget from
    Scheduler "1"  -->  "1"   Pet           : uses context from
    Scheduler "1"  *--  "0..*" ScheduledTask : produces
    ScheduledTask "1" --> "1"  Task          : wraps
```

## What changed from the initial design

| # | Change | Why |
|---|---|---|
| 1 | `Owner` gained `pets`, `add_pet()`, `get_all_tasks()` | Tasks now flow Owner → Pet → Task; Scheduler pulls via `owner.get_all_tasks()` |
| 2 | `Pet` gained `tasks` list, `add_task()`, `remove_task()` | Tasks live on the pet they belong to, not directly on the Scheduler |
| 3 | `Task` gained `completed`, `frequency`, `due_date`, `pet_name` | Support for completion tracking, recurring tasks, and cross-pet filtering |
| 4 | `Task.mark_complete()` added with return type `Task` | Returns the next occurrence for daily/weekly tasks using `timedelta` |
| 5 | `Scheduler` gained `remaining_minutes` | Needed by `fits_in_time()` to track live budget as tasks are scheduled |
| 6 | `Scheduler.sort_by_time()` added (static `$`) | Sorts `ScheduledTask` list chronologically for display |
| 7 | `Scheduler.filter_tasks()` added (static `$`) | Filters task pool by `pet_name` and/or `completed` status |
| 8 | `Scheduler.detect_conflicts()` added | Pairwise overlap check; returns warning strings |
| 9 | `Pet o-- Task` relationship added | Replaces the old `Scheduler o-- Task`; tasks no longer live on the scheduler |
| 10 | `Task ..> Task` self-link added | Expresses that `mark_complete()` can produce a new `Task` instance |
