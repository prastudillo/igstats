from django.http import HttpResponse
from django.utils.timezone import localtime
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages #alerts
from django.shortcuts import render
from django.views.generic.edit import FormView
from .forms import FileFieldForm

import csv, io

class FileFieldView(FormView):
    form_class = FileFieldForm
    template_name = 'igstatsapp/home.html'  # Replace with your template.
    success_url = '/success'  # Replace with your URL or reverse().

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('file_field')
        
        print(len(files))
        if form.is_valid():
            for f in files:
                print(f.name)

                #csv is now read
                #import all data from csv to database

            return self.form_valid(form)
        else:
            return self.form_invalid(form)


def home_view(request):
    return render(request, 'igstatsapp/home.html')


#Success page
#download excel file 
def success_page_view(request):
    return render(request, 'igstatsapp/success_page.html')