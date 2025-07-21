import random
from .models import BingoTaskTemplate, BingoUserInstance, BingoUserTask


def create_bingo_for_user(user, num_tasks=25):
    tasks = list(BingoTaskTemplate.objects.filter(is_active=True))
    selected_tasks = random.sample(tasks, min(num_tasks, len(tasks)))
    instance = BingoUserInstance.objects.create(user=user)
    for task in selected_tasks:
        BingoUserTask.objects.create(instance=instance, task=task)
    return instance


def swap_user_task(task):
    instance = task.instance
    used_tasks = instance.tasks.values_list("task_id", flat=True)
    available_tasks = BingoTaskTemplate.objects.filter(is_active=True).exclude(
        id__in=used_tasks
    )
    if not available_tasks.exists():
        return None
    new_task = random.choice(list(available_tasks))
    task.task = new_task
    task.task_state = BingoUserTask.TaskState.NOT_STARTED
    task.user_comment = ""
    task.reviewer_comment = ""
    task.photo_proof_url = ""
    task.submitted_at = None
    task.reviewed_at = None
    task.reviewed_by = None
    task.save()
    return new_task
