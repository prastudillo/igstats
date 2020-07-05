from django.http import HttpResponse
from django.utils.timezone import localtime
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages #alerts
from django.shortcuts import render
from django.views.generic.edit import FormView
from django.db import connection
from .forms import FileFieldForm
from .models import CsvData, EdmData, CampaignType, Domain
import csv, io
import xlwt


#for uploading multiples files
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
                #for staging
                data_set = f.read().decode('UTF-8')
                io_string = io.StringIO(data_set)
                next(io_string)

                for column in csv.reader(io_string, delimiter=',', quoting=csv.QUOTE_NONE):

                    #checks if blank line
                    if any(x.strip() for x in column):
                        
                        
                        #saving data from csv to db ... try bulk create for faster queries
                        created = CsvData.objects.create(
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
            
            #add data to campaign type table
            campaign_types = CsvData.objects.values_list('ticker','campaign_id').distinct()
            for camp_type in campaign_types:
                created_camp_type = CampaignType.objects.create(ticker=camp_type[0], campaign_id=camp_type[1])

            #add data to domain table
            recipient_list = CsvData.objects.values_list('recipient',flat=True)
            email_domain_list = []
            for recipient in recipient_list:
                email_domain_str = "@" + recipient.split("@")[1]
                email_domain_list.append(email_domain_str)

            email_domain_set = set(email_domain_list)
            for email_domain in email_domain_set:

                created_domain = Domain.objects.create(email_domain=email_domain)

            #add data to edm table with foreign keys
            csv_data_list = CsvData.objects.values_list('ticker','domain','campaign_id',
            'recipient','clicked','opened','delivered','bounced','complained','unsubscribed','trans_date')

            for csv_data in csv_data_list:
                
                #for email_domain
                email_domain_str= "@"  + csv_data[3].split("@")[1]

                #insertion of data into edmdata table
                created_edm_data = EdmData.objects.create(
                    ticker=csv_data[0],
                    domain=csv_data[1],
                    campaign_id=CampaignType.objects.get(campaign_id=csv_data[2]),
                    recipient=Domain.objects.get(email_domain=email_domain_str),
                    clicked=csv_data[4],
                    opened=csv_data[5],
                    delivered=csv_data[6],
                    bounced=csv_data[7],
                    complained=csv_data[8],
                    unsubscribed=csv_data[9],
                    trans_date=csv_data[10]
                )

            #remove all contents of csvdata table
            CsvData.objects.all().delete()

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

#create a new view that executes SQL directly
#using connection
def home_view(request):
    return render(request, 'igstatsapp/home.html')

#Success page
#download excel file 
def success_page_view(request):
    return render(request, 'igstatsapp/success_page.html')


# export to excel
def download_excel_report(request):
    response = HttpResponse(content_type='application/ms-excel')

    response['Content-Disposition'] = 'attachment; filename="INVESTING GIANTS-EDM STATS.xls" '

    #creating workbook
    wb = xlwt.Workbook(encoding='utf-8')

    #adding sheet
    ws = wb.add_sheet("sheet1")

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    #for timestamp
    date_format = xlwt.XFStyle()
    date_format.num_format_str = 'dd/mm/yy'
    #column header
    columns = ['Column1', 'Column2', 'Column 3', 'Column4',]

    #write column headers in sheet

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num],font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    #get data from db
    data = EdmData.objects.all()[:100]

    for my_row in data:
        row_num = row_num + 1
        ws.write(row_num, 0, my_row.ticker, font_style)
        ws.write(row_num, 1, my_row.domain, font_style)
        ws.write(row_num, 2, my_row.campaign_id, font_style)
        ws.write(row_num, 3, my_row.recipient, font_style)
        ws.write(row_num, 4, my_row.clicked, font_style)
        ws.write(row_num, 5, my_row.opened, font_style)
        ws.write(row_num, 6, my_row.delivered, font_style)
        ws.write(row_num, 7, my_row.bounced, font_style)
        ws.write(row_num, 8, my_row.complained, font_style)
        ws.write(row_num, 9, my_row.unsubscribed, font_style)
        ws.write(row_num, 10, my_row.trans_date, date_format)

    #FORMAT NOW THE OUTPUT

    wb.save(response)

    return response
