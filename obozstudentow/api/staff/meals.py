from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import permission_required
from django.utils import timezone


from ...models import Meal, MealValidation, User

@api_view(['PUT'])
@permission_required('obozstudentow.can_validate_meals')
def validate_meal(request):
    if 'meal_id' not in request.data:
        return Response({'success': False, 'error': 'Nie podano ID posiłku'})
    if 'user_id' not in request.data:
        return Response({'success': False, 'error': 'Nie podano ID użytkownika'})
    

    if not User.objects.filter(id=int(request.data['user_id'])).exists():
        return Response({'success': False, 'error': 'Użytkownik nie istnieje'})

    user = User.objects.get(id=int(request.data['user_id']))

    if not Meal.objects.filter(id=request.data['meal_id']).exists():
        return Response({'success': False, 'error': 'Posiłek nie istnieje', 'user': user.first_name + ' ' + user.last_name})

    if MealValidation.objects.filter(meal_id=request.data['meal_id'], user=user).exists():
        mv = MealValidation.objects.get(meal_id=request.data['meal_id'], user=user)
        date = timezone.localtime(mv.timeOfValidation)
        return Response({'success': False, 'error': f'Posiłek zrealizowany {date.strftime("%H:%M %d.%m")}', 'user': user.first_name + ' ' + user.last_name})
    
    mv = MealValidation.objects.create(meal_id=request.data['meal_id'], user_id=request.data['user_id'])
    mv.save()


    return Response({'success': True, 'error': None, 'user': user.first_name + ' ' + user.last_name })