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


def swap_user_task(task: BingoUserTask):
    instance = task.instance

    if instance.swap_used:
        return None

    used_tasks_ids = instance.tasks.values_list("task_id", flat=True)
    available_tasks = BingoTaskTemplate.objects.filter(is_active=True).exclude(
        id__in=used_tasks_ids
    )

    if not available_tasks.exists():
        return None

    new_task_template = random.choice(list(available_tasks))

    # Resetowanie zadania
    if task.photo_proof:
        try:
            task.photo_proof.delete(save=False)
        except Exception as e:
            print(f"Could not delete photo for task {task.id}: {e}")

    task.task = new_task_template
    task.task_state = BingoUserTask.TaskState.NOT_STARTED
    task.user_comment = None
    task.reviewer_comment = None
    task.photo_proof = None
    task.submitted_at = None
    task.reviewed_at = None
    task.reviewed_by = None
    task.save()  # zapis zmiany w zadaniu

    instance.swap_used = True
    instance.save(update_fields=["swap_used"])  # zapis zmiany w instancji

    return new_task_template  # zwrócenie nowego zadania


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
