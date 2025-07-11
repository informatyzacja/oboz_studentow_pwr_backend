from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import permission_required
from django.utils import timezone


from ...models import Meal, MealValidation, User

from django.urls import path


@api_view(["GET"])
@permission_required("obozstudentow.can_validate_meals")
def get_current_meal(request):
    return Response(
        Meal.objects.filter(start__lte=timezone.now(), end__gt=timezone.now())
        .order_by("-start")
        .values("id", "name", "start")
        .first()
        or {}
    )


@api_view(["GET"])
@permission_required("obozstudentow.can_validate_meals")
def get_current_meals(request):
    return Response(
        Meal.objects.filter(start__lte=timezone.now(), end__gt=timezone.now())
        .order_by("start")
        .values("id", "name", "start")
    )


@api_view(["GET"])
@permission_required("obozstudentow.can_validate_meals")
def check_meal_validation(request):
    if "meal_id" not in request.GET:
        return Response({"success": False, "error": "Nie podano ID posiłku"})
    if "user_id" not in request.GET:
        return Response({"success": False, "error": "Nie podano ID użytkownika"})

    if not User.objects.filter(bandId=request.GET["user_id"].zfill(6)).exists():
        return Response({"success": False, "error": "Użytkownik nie istnieje"})

    user = User.objects.get(bandId=request.GET["user_id"].zfill(6))

    if not Meal.objects.filter(id=request.GET["meal_id"]).exists():
        return Response(
            {
                "success": False,
                "error": "Posiłek nie istnieje",
                "user": user.first_name + " " + user.last_name,
                "user_title": user.title,
                "user_diet": user.diet,
            }
        )

    if MealValidation.objects.filter(
        meal_id=request.GET["meal_id"], user=user
    ).exists():
        mv = MealValidation.objects.get(meal_id=request.GET["meal_id"], user=user)
        validatedByInfo = ""
        if mv.validatedBy:
            validatedByInfo = f", zatwierdzone przez {mv.validatedBy.first_name} {mv.validatedBy.last_name}"
        return Response(
            {
                "success": False,
                "error": f'Posiłek zrealizowany {mv.timeOfValidation.strftime("%H:%M %d.%m")}'
                + validatedByInfo,
                "user": user.first_name + " " + user.last_name,
                "user_title": user.title,
                "user_diet": user.diet,
            }
        )

    return Response(
        {
            "success": True,
            "error": None,
            "user": user.first_name + " " + user.last_name,
            "user_title": user.title,
            "user_diet": user.diet,
        }
    )


@api_view(["PUT"])
@permission_required("obozstudentow.can_validate_meals")
def validate_meal(request):
    if "meal_id" not in request.data:
        return Response({"success": False, "error": "Nie podano ID posiłku"})
    if "user_id" not in request.data:
        return Response({"success": False, "error": "Nie podano ID użytkownika"})

    if not User.objects.filter(bandId=request.data["user_id"].zfill(6)).exists():
        return Response({"success": False, "error": "Użytkownik nie istnieje"})

    user = User.objects.get(bandId=request.data["user_id"].zfill(6))

    if not Meal.objects.filter(id=request.data["meal_id"]).exists():
        return Response(
            {
                "success": False,
                "error": "Posiłek nie istnieje",
                "user": user.first_name + " " + user.last_name,
                "user_title": user.title,
                "user_diet": user.diet,
            }
        )

    if MealValidation.objects.filter(
        meal_id=request.data["meal_id"], user=user
    ).exists():
        mv = MealValidation.objects.get(meal_id=request.data["meal_id"], user=user)
        return Response(
            {
                "success": False,
                "error": f'Posiłek zrealizowany {mv.timeOfValidation.strftime("%H:%M %d.%m")}',
                "user": user.first_name + " " + user.last_name,
                "user_title": user.title,
                "user_diet": user.diet,
            }
        )

    mv = MealValidation.objects.create(
        meal_id=request.data["meal_id"], user_id=user.id, validatedBy=request.user
    )
    mv.save()

    return Response(
        {
            "success": True,
            "error": None,
            "user": user.first_name + " " + user.last_name,
            "user_title": user.title,
            "user_diet": user.diet,
        }
    )


urlpatterns = [
    path("validate/", validate_meal),
    path("check/", check_meal_validation),
    path("current-meal/", get_current_meal),
    path("current-meals/", get_current_meals),
]
