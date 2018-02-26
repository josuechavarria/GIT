from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

def home(request):
    numbers = [1,2,3,4,5]
    name = 'Hector Machuca'
    args = {'name' :name, 'numbers': numbers}
    return render(request, 'evaluaciones/landing.html',args)

def principal(request):
    return render(request,'evaluaciones/principal.html')

def login(request):
    return render(request, 'accounts/login.html')
