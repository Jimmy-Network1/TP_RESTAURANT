from django.shortcuts import render


def login_view(request):
    return render(request, 'accounts/login.html')


def logout_view(request):
    return render(request, 'accounts/logout.html')


def roles_view(request):
    return render(request, 'accounts/roles.html')
