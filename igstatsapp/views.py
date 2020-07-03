from django.http import HttpResponse
from django.utils.timezone import localtime
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages #alerts
from django.shortcuts import render
from django.views.generic.edit import FormView
from .forms import FileFieldForm
from .models import EdmData
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
                
                #import all data from csv to database
                data_set = f.read().decode('UTF-8')
                io_string = io.StringIO(data_set)
                next(io_string)

                for column in csv.reader(io_string, delimiter=',', quoting=csv.QUOTE_NONE):
                    #checks if blank line
                    if any(x.strip() for x in column):

                        #saving data from csv to db
                        created = EdmData.objects.create(
                        ticker=column[0],
                        domain=column[1],
                        campaign_id=column[2],
                        recipient=column[3],
                        clicked=column[4],
                        opened=column[5],
                        delivered=column[6],
                        bounced=column[7],
                        complained=column[8],
                        unsubscribed=column[9],
                        trans_date=column[10]
                )

            return self.form_valid(form)
        else:
            return self.form_invalid(form)


def home_view(request):
    return render(request, 'igstatsapp/home.html')


#Success page
#download excel file 
def success_page_view(request):
    return render(request, 'igstatsapp/success_page.html')