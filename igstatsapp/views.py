from django.http import HttpResponse
from django.utils.timezone import localtime
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages #alerts

from django.shortcuts import render

#Home page
#folder upload

def home_view(request):
    return render(request, 'igstatsapp/home.html')


#Success page
#download excel file 
def success_page_view(request):
    return render(request, 'igstatsapp/success_page.html')