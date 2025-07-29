import random
from .models import BingoTaskTemplate, BingoUserInstance, BingoUserTask


def create_bingo_for_user(user, num_tasks=25):
    tasks = list(BingoTaskTemplate.objects.filter(is_active=True))

    if len(tasks) < num_tasks:
        raise ValueError("Za mało aktywnych zadań do stworzenia planszy")

    selected_tasks = random.sample(tasks, num_tasks)

    instance = BingoUserInstance.objects.create(user=user)

    index = 0
    for row in range(5):
        for col in range(5):
            task = selected_tasks[index]
            BingoUserTask.objects.create(instance=instance, task=task, row=row, col=col)
            index += 1

    return instance


def swap_user_task(task):
    instance = task.instance

    # Sprawdź, czy wymiana została już wykorzystana
    if instance.swap_used:
        return None  # Zwróć None, jeśli limit został wyczerpany

    used_tasks = instance.tasks.values_list("task_id", flat=True)
    available_tasks = BingoTaskTemplate.objects.filter(is_active=True).exclude(
        id__in=used_tasks
    )
    if not available_tasks.exists():
        # Teoretycznie można zwrócić inny błąd, ale None też zadziała
        return None

    new_task = random.choice(list(available_tasks))
    task.task = new_task
    task.task_state = BingoUserTask.TaskState.NOT_STARTED
    # ... resetowanie pozostałych pól
    task.photo_proof.delete(save=False) if task.photo_proof else None
    task.save()

    # Ustaw flagę i zapisz instancję planszy
    instance.swap_used = True
    instance.save(update_fields=["swap_used"])

    return new_task


def check_bingo_win(instance):
    grid = [[None for _ in range(5)] for _ in range(5)]
    for task in instance.tasks.all():
        grid[task.row][task.col] = task

    def line_won(line):
        return all(t and t.task_state == BingoUserTask.TaskState.APPROVED for t in line)

    # Wiersze i kolumny
    for i in range(5):
        if line_won([grid[i][j] for j in range(5)]):
            return True
        if line_won([grid[j][i] for j in range(5)]):
            return True

    # Przekątne
    if line_won([grid[i][i] for i in range(5)]):
        return True
    if line_won([grid[i][4 - i] for i in range(5)]):
        return True

    return False
