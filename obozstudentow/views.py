from django.shortcuts import render
import os
from django.conf import settings
from django.http import HttpResponse, Http404, FileResponse
from django.contrib.auth.decorators import login_required


from .models import Image

@login_required
def download_image(request, image_id):
    if Image.objects.filter(id=image_id).exists():
        image = Image.objects.get(id=image_id)
        return FileResponse(image.image, as_attachment=True, filename=image.name+"_Obóz_Studentow_PWr_2023."+image.image.path.split('.')[-1])
    raise Http404