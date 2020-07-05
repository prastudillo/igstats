from django.http import HttpResponse
from django.utils.timezone import localtime
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages #alerts
from django.shortcuts import render
from django.views.generic.edit import FormView
from django.db import connection
from django.db.models import Sum, Count
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
                    trans_date=csv_data[10],
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

    #dashboard sheet
    #adding sheet
    dashboard = wb.add_sheet("Dashboard")

    #change width of each cell
    for colx in range(0,6):
        width = 40*256
        dashboard.col(colx).width = width

    # Sheet header, first row
    row_num = 0
    row_num_ticker = 29

    #for headers
    font_style_header = xlwt.XFStyle()
    font_style_header.font.bold = True

    #for timestamp
    date_format = xlwt.XFStyle()
    date_format.num_format_str = 'dd/mm/yy'

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    dashboard.write(0,0,"Top 25 Campaigns",font_style_header) #add dates
    dashboard.write(29,0,"Top 25 Tickers",font_style_header)

    row_num = row_num + 1
    row_num_ticker = row_num_ticker + 1

    #dashboard column header
    dashboard_columns = ['Count', 'Clicked', 'Opened', 'Delivered', 'Bounced', 'Unsubscribed',]
    for col_num in range(len(dashboard_columns)):
        dashboard.write(row_num, col_num, dashboard_columns[col_num], font_style_header)

        #for ticker
        dashboard.write(row_num_ticker, col_num, dashboard_columns[col_num], font_style_header)


    #Top 25 count
    top25count = CampaignType.objects.all().annotate(total_count=Sum("edmdata__total_count")).order_by('total_count')[:25]

    for camptype in top25count:
        row_num = row_num + 1
        dashboard.write(row_num,0,camptype.campaign_id)

        #for ticker
        row_num_ticker = row_num_ticker + 1
        dashboard.write(row_num_ticker,0,camptype.ticker)

    #Top 25 clicked
    top25clicked = CampaignType.objects.all().annotate(total_clicked=Sum("edmdata__clicked")).order_by('total_clicked')[:25]

    row_num = 1
    row_num_ticker = 30
    for camptype in top25clicked:
        row_num = row_num + 1
        dashboard.write(row_num,1,camptype.campaign_id)

        #for ticker
        row_num_ticker = row_num_ticker + 1
        dashboard.write(row_num_ticker,1,camptype.ticker)

    #Top 25 opened
    row_num = 1
    row_num_ticker = 30
    top25opened = CampaignType.objects.all().annotate(total_opened=Sum("edmdata__opened")).order_by('total_opened')[:25]
    for camptype in top25opened:
        row_num = row_num + 1
        dashboard.write(row_num,2,camptype.campaign_id)

        #for ticker
        row_num_ticker = row_num_ticker + 1
        dashboard.write(row_num_ticker,2,camptype.ticker)

    #Top 25 Bounced
    row_num = 1
    row_num_ticker = 30
    top25bounced = CampaignType.objects.all().annotate(total_bounced=Sum("edmdata__bounced")).order_by('total_bounced')[:25]
    for camptype in top25bounced:
        row_num = row_num + 1
        dashboard.write(row_num,3,camptype.campaign_id)

         #for ticker
        row_num_ticker = row_num_ticker + 1
        dashboard.write(row_num_ticker,3,camptype.ticker)

    #Top 25 Unsubscribed
    row_num = 1
    row_num_ticker = 30
    top25unsubscribed = CampaignType.objects.all().annotate(total_unsubscribed=Sum("edmdata__unsubscribed")).order_by('total_unsubscribed')[:25]
    for camptype in top25unsubscribed:
        row_num = row_num + 1
        dashboard.write(row_num,4,camptype.campaign_id)

        #for ticker
        row_num_ticker = row_num_ticker + 1
        dashboard.write(row_num_ticker,4,camptype.ticker)

    #By Campaign sheet
    by_campaign = wb.add_sheet("By Campaign")
    row_num = 0
    by_campaign_headers = ['Campaign', 'Total Count', 'Total Clicked', 'Total Opened', 'Total Delivered', 'Total Bounced', 'Total Complained', 'Total Unsubscribed',]
    for col_num in range(len(by_campaign_headers)):
        by_campaign.write(row_num, col_num, by_campaign_headers[col_num], font_style_header)

    #get data
    campaigntypes = CampaignType.objects.all().annotate(total_count=Sum("edmdata__total_count"),clicked_count = Sum("edmdata__clicked",),opened_count= Sum("edmdata__opened"),delivered_count=Sum("edmdata__delivered"),bounced_count=Sum("edmdata__bounced"),complained_count=Sum("edmdata__complained"),unsubscribed_count=Sum("edmdata__unsubscribed")).order_by('total_count')
    
    for campaigntype in campaigntypes:
        row_num = row_num + 1
        by_campaign.write(row_num,0,campaigntype.campaign_id)
        by_campaign.write(row_num,1,campaigntype.total_count)
        by_campaign.write(row_num,2,campaigntype.clicked_count)
        by_campaign.write(row_num,3,campaigntype.opened_count)
        by_campaign.write(row_num,4,campaigntype.delivered_count)
        by_campaign.write(row_num,5,campaigntype.bounced_count)
        by_campaign.write(row_num,6,campaigntype.complained_count)
        by_campaign.write(row_num,7,campaigntype.unsubscribed_count)

    #By Email Sheet
    by_email = wb.add_sheet("By Email")



    #Top 25 Domain Sheet
    top25domain = wb.add_sheet("Top 25 Domain")

    #Monthly Overall Top 25 Sheet    
    monthlytop25domain = wb.add_sheet("Monthly Overall Top 25")

    wb.save(response)

    return response
