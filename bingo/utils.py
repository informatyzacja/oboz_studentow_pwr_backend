import random
from .models import BingoTaskTemplate, BingoUserInstance, BingoUserTask


def create_bingo_for_user(user, num_tasks=9):
    tasks = list(BingoTaskTemplate.objects.filter(is_active=True))
    selected_tasks = random.sample(tasks, min(num_tasks, len(tasks)))
    instance = BingoUserInstance.objects.create(user=user)
    for task in selected_tasks:
        BingoUserTask.objects.create(instance=instance, task=task)
    return instance


# ogarnąć rozmiar planszy, żeby była kwadratowa i 5x5
