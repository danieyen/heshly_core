from heshly_core.services.crm.task_manager import (
    TaskManager,
    TaskPriority,
    TaskStatus,
)



def run():

    manager = TaskManager()



    task = manager.create_task(

        business_id="BIZ-001",

        title="Follow up quotation",

        related_type="opportunity",

        related_id="OPP-001",

        assigned_to="Sales Agent",

        priority=TaskPriority.HIGH,

    )


    print(
        "Created Task:"
    )

    print(task)



    assert task.status == (
        TaskStatus.OPEN
    )


    assert task.priority == (
        TaskPriority.HIGH
    )



    completed = manager.complete_task(
        task.task_id
    )


    print(
        "\nCompleted Task:"
    )

    print(completed)



    assert completed.status == (
        TaskStatus.COMPLETED
    )



    tasks = manager.get_tasks(
        "OPP-001"
    )


    print(
        "\nRelated Tasks:"
    )

    print(tasks)



    assert len(tasks) == 1



    print(
        "\n✅ Task Management Functional Test Passed"
    )



if __name__ == "__main__":

    run()