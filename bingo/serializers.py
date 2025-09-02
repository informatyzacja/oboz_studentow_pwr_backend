from rest_framework import serializers
from .models import BingoUserInstance, BingoUserTask, BingoTaskTemplate
from .utils import check_bingo_win


# class BingoTaskTemplateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = BingoTaskTemplate
#         fields = "__all__"
class BingoTaskTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BingoTaskTemplate
        fields = ["id", "task_name", "description"]


class BingoUserTaskSerializer(serializers.ModelSerializer):
    task = BingoTaskTemplateSerializer(read_only=True)

    class Meta:
        model = BingoUserTask
        fields = [
            "id",
            "task",
            "row",
            "col",
            "task_state",
            "user_comment",
            "reviewer_comment",
            "photo_proof",
            "submitted_at",
            "reviewed_at",
            "reviewed_by",
        ]


# def get_photo_proof(self, obj):
#     if obj.photo_proof:
#         request = self.context.get("request")
#         return request.build_absolute_uri(obj.photo_proof.url)
#     return None


class BingoUserInstanceSerializer(serializers.ModelSerializer):
    # Pole, które zwróci zadania jako siatkę 2D (lista list)
    tasks_grid = serializers.SerializerMethodField()
    can_submit_for_review = serializers.SerializerMethodField()

    class Meta:
        model = BingoUserInstance
        fields = [
            "id",
            "user",
            "created_at",
            "completed_at",
            "has_won",
            "swap_used",
            "review_status",
            "can_submit_for_review",
            "tasks_grid",
        ]
        read_only_fields = [
            "user",
            "created_at",
            "completed_at",
            "has_won",
            "review_status",
        ]

    def get_can_submit_for_review(self, instance):
        # Użytkownik może wysłać planszę, jeśli:
        # 1. Ma ułożoną linię bingo.
        # 2. Plansza jest wciąż w trakcie gry (nie została już wysłana lub zakończona).
        if instance.review_status == instance.ReviewStatus.IN_PROGRESS:
            return check_bingo_win(instance)
        return False

    def get_tasks_grid(self, instance):
        # Układa zadania w siatkę 5x5 na podstawie ich atrybutów 'row' i 'col'.
        tasks = instance.tasks.all().order_by("row", "col")
        task_serializer = BingoUserTaskSerializer(
            tasks, many=True, context=self.context
        )

        grid = [[] for _ in range(5)]
        for task_data in task_serializer.data:
            grid[task_data["row"]].append(task_data)

        return grid
