from django.shortcuts import render


def error_404(request, exception):
    return render(
        request, "error_documents/404.html", {"url": request.path}, status=404
    )


def error_403(request, exception):
    return render(
        request, "error_documents/403.html", {"url": request.path}, status=403
    )


def error_crft(request, reason):
    print(reason)
    return render(
        request, "error_documents/crft.html", {"url": request.path}, status=403
    )


def error_500(request):
    return render(request, "error_documents/500.html", status=500)


def error_400(request, exception):
    return render(request, "error_documents/400.html", status=400)
