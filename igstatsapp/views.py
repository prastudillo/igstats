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
from django.db.models.functions import ExtractMonth, ExtractYear, ExtractDay
from .forms import FileFieldForm
from .models import CsvData, EdmData, CampaignType, Domain, Recipient
import calendar
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

            #add data to recipient table
            recipient_list = CsvData.objects.values_list('recipient').distinct()
            for recipient in recipient_list:
                email_domain_str = "@" + recipient[0].split("@")[1]
                created_recipient = Recipient.objects.create(recipient_email=recipient[0],domain=email_domain_str)

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
                    recipient_email=Recipient.objects.get(recipient_email=csv_data[3]),
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
    for colx in range(0,10):
        width = 40*256
        dashboard.col(colx).width = width

    # Sheet header, first row
    row_num = 0
    row_num_ticker = 0

    #for headers
    font_style_header = xlwt.XFStyle()
    font_style_header.font.bold=True

    #for column headers
    font_style_column_header = xlwt.XFStyle()
    font_style_column_header.font.bold = True
    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = xlwt.Style.colour_map['gray25']
    font_style_column_header.pattern = pattern

    #for timestamp
    date_format = xlwt.XFStyle()
    date_format.num_format_str = 'dd/mm/yy'

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    #query by month
    month_dashboard_header = ['Total EDMs','Clicked','Clicked %', 'Opened', 'Opened %', 'Unsubscribed', 'Unsubscribed %', 'Delivered', 'Bounced','Complained']

    for col_num in range(len(month_dashboard_header)):
        dashboard.write(row_num, col_num+1, month_dashboard_header[col_num], font_style_column_header)

    edmdata_month = CampaignType.objects.annotate(month=ExtractMonth('edmdata__trans_date'),year=ExtractYear('edmdata__trans_date'),).order_by('month','year').values('month','year').annotate(monthly_count=Sum('edmdata__total_count'),monthly_clicked=Sum('edmdata__clicked'),monthly_opened=Sum('edmdata__opened'),monthly_unsubscribed=Sum('edmdata__unsubscribed'),monthly_delivered=Sum('edmdata__delivered'),monthly_bounced=Sum('edmdata__bounced'),monthly_complained=Sum('edmdata__complained')).values('month','year','monthly_count','monthly_clicked','monthly_opened','monthly_unsubscribed','monthly_delivered','monthly_bounced','monthly_complained')

    for edmdata in edmdata_month:
        row_num = row_num + 1 

        #month yr string
        month_yr_str = str(calendar.month_name[edmdata['month']]) + " " + str(edmdata['year'])

        dashboard.write(row_num,0,month_yr_str,font_style_header)
        dashboard.write(row_num,1,edmdata['monthly_count'])
        dashboard.write(row_num,2,edmdata['monthly_clicked'])
        dashboard.write(row_num,3,round((edmdata['monthly_clicked']/edmdata['monthly_count']),3))
        dashboard.write(row_num,4,edmdata['monthly_opened'])
        dashboard.write(row_num,5,round((edmdata['monthly_opened']/edmdata['monthly_count']),3))
        dashboard.write(row_num,6,edmdata['monthly_unsubscribed'])
        dashboard.write(row_num,7,round((edmdata['monthly_unsubscribed']/edmdata['monthly_count']),3))
        dashboard.write(row_num,8,edmdata['monthly_delivered'])
        dashboard.write(row_num,9,edmdata['monthly_bounced'])
        dashboard.write(row_num,10,edmdata['monthly_complained'])

    row_num = row_num + 4
    dashboard.write(row_num,0,"Top 25 Campaigns",font_style_header) #add dates
    row_num = row_num + 1
    starting_row = row_num

    row_num_ticker = row_num_ticker + 27
    dashboard.write(row_num_ticker,0,"Top 25 Tickers",font_style_header)
    row_num_ticker = row_num_ticker + 1
    starting_row_ticker = row_num_ticker

    #dashboard column header
    dashboard_columns = ['Count', 'Clicked', 'Opened', 'Delivered', 'Bounced', 'Unsubscribed',]
    for col_num in range(len(dashboard_columns)):
        dashboard.write(row_num, col_num, dashboard_columns[col_num], font_style_column_header)

        #for ticker
        dashboard.write(row_num_ticker, col_num, dashboard_columns[col_num], font_style_column_header)


    #Top 25 count
    top25count = CampaignType.objects.all().annotate(total_count=Sum("edmdata__total_count")).order_by('-total_count')[:25]

    for camptype in top25count:
        row_num = row_num + 1
        dashboard.write(row_num,0,camptype.campaign_id)

        #for ticker
        row_num_ticker = row_num_ticker + 1
        dashboard.write(row_num_ticker,0,camptype.ticker)

    #Top 25 clicked
    top25clicked = CampaignType.objects.all().annotate(total_clicked=Sum("edmdata__clicked")).order_by('-total_clicked')[:25]

    row_num = starting_row
    row_num_ticker = starting_row_ticker

    for camptype in top25clicked:
        row_num = row_num + 1
        dashboard.write(row_num,1,camptype.campaign_id)

        #for ticker
        row_num_ticker = row_num_ticker + 1
        dashboard.write(row_num_ticker,1,camptype.ticker)

    #Top 25 opened
    row_num = starting_row
    row_num_ticker = starting_row_ticker

    top25opened = CampaignType.objects.all().annotate(total_opened=Sum("edmdata__opened")).order_by('-total_opened')[:25]
    for camptype in top25opened:
        row_num = row_num + 1
        dashboard.write(row_num,2,camptype.campaign_id)

        # for ticker
        row_num_ticker = row_num_ticker + 1
        dashboard.write(row_num_ticker,2,camptype.ticker)

    #Top 25 Bounced
    row_num = starting_row
    row_num_ticker = starting_row_ticker

    top25bounced = CampaignType.objects.all().annotate(total_bounced=Sum("edmdata__bounced")).order_by('-total_bounced')[:25]
    for camptype in top25bounced:
        row_num = row_num + 1
        dashboard.write(row_num,3,camptype.campaign_id)

        # for ticker
        row_num_ticker = row_num_ticker + 1
        dashboard.write(row_num_ticker,3,camptype.ticker)

    #Top 25 Unsubscribed
    row_num = starting_row
    row_num_ticker = starting_row_ticker

    top25unsubscribed = CampaignType.objects.all().annotate(total_unsubscribed=Sum("edmdata__unsubscribed")).order_by('-total_unsubscribed')[:25]
    for camptype in top25unsubscribed:
        row_num = row_num + 1
        dashboard.write(row_num,4,camptype.campaign_id)

        # for ticker
        row_num_ticker = row_num_ticker + 1
        dashboard.write(row_num_ticker,4,camptype.ticker)


    #By Campaign sheet
    by_campaign = wb.add_sheet("By Campaign")
    row_num = 0
    by_campaign_headers = ['Campaign', 'Total Count', 'Total Clicked', 'Total Opened', 'Total Delivered', 'Total Bounced', 'Total Complained', 'Total Unsubscribed',]
    for col_num in range(len(by_campaign_headers)):
        by_campaign.write(row_num, col_num, by_campaign_headers[col_num], font_style_header)
    
    #change width of cell
    for colx in range(0,8):
        width = 30*256
        by_campaign.col(colx).width = width
 
    #get data
    campaigntypes = CampaignType.objects.all().annotate(total_count=Sum("edmdata__total_count"),clicked_count = Sum("edmdata__clicked",),opened_count= Sum("edmdata__opened"),delivered_count=Sum("edmdata__delivered"),bounced_count=Sum("edmdata__bounced"),complained_count=Sum("edmdata__complained"),unsubscribed_count=Sum("edmdata__unsubscribed")).order_by('-total_count')
    
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
    
    #add per month 


    #By Email Sheet
    by_email = wb.add_sheet("By Email")
    row_num = 0
    by_email_headers = ['Email', 'Domain', 'Total Count', 'Total Clicked','Total Opened', 'Total Delivered', 'Total Bounced', 'Total Complained', 'Total Unsubscribed',]
    for col_num in range(len(by_email_headers)):
        by_email.write(row_num, col_num, by_email_headers[col_num], font_style_header)

    #change width of cell
    for colx in range(0,25):
        width = 30*256
        by_email.col(colx).width = width

    # get data
    by_email_list =Recipient.objects.all().annotate(total_overall_count=Sum("edmdata__total_count"),clicked_count = Sum("edmdata__clicked"),opened_count= Sum("edmdata__opened"),delivered_count=Sum("edmdata__delivered"),bounced_count=Sum("edmdata__bounced"),complained_count=Sum("edmdata__complained"),unsubscribed_count=Sum("edmdata__unsubscribed")).order_by('-total_overall_count')

    for email in by_email_list:
        row_num = row_num + 1
        by_email.write(row_num,0,email.recipient_email)
        by_email.write(row_num,1,email.domain)
        by_email.write(row_num,2,email.total_overall_count)
        by_email.write(row_num,3,email.clicked_count)
        by_email.write(row_num,4,email.opened_count)
        by_email.write(row_num,5,email.delivered_count)
        by_email.write(row_num,6,email.bounced_count)
        by_email.write(row_num,7,email.complained_count)
        by_email.write(row_num,8,email.unsubscribed_count)

    #get the per month and render it
    by_email_month = EdmData.objects.all().annotate(month=ExtractMonth('trans_date'),year=ExtractYear('trans_date')).order_by('month','year').values('month','year').distinct()

   
    col_num = 8 #after total unsubscribed
    for email_month in by_email_month:
        row_num = 0

        #writing the column headers per month
        month_count_str = str(calendar.month_name[email_month['month']]) + " " + str(email_month['year']) + " Count"
        month_clicked_str = str(calendar.month_name[email_month['month']]) + " " + str(email_month['year']) + " Clicked"  
        month_opened_str = str(calendar.month_name[email_month['month']]) + " " + str(email_month['year']) + " Opened"
        month_delivered_str = str(calendar.month_name[email_month['month']]) + " " + str(email_month['year']) + " Delivered"
        month_bounced_str = str(calendar.month_name[email_month['month']]) + " " + str(email_month['year']) + " Bounced" 
        month_complained_str = str(calendar.month_name[email_month['month']]) + " " + str(email_month['year']) + " Complained"
        month_unsubscribed_str = str(calendar.month_name[email_month['month']]) + " " + str(email_month['year']) + " Unsubscribed"

        by_email.write(row_num, col_num+1, month_count_str, font_style_header)
        by_email.write(row_num, col_num+2, month_clicked_str, font_style_header)
        by_email.write(row_num, col_num+3, month_opened_str,font_style_header)
        by_email.write(row_num, col_num+4, month_delivered_str,font_style_header)
        by_email.write(row_num, col_num+5, month_bounced_str,font_style_header)
        by_email.write(row_num, col_num+6, month_complained_str,font_style_header)
        by_email.write(row_num, col_num+7, month_unsubscribed_str,font_style_header)


        by_email_month = Recipient.objects.all().annotate(month=ExtractMonth('edmdata__trans_date'),year=ExtractYear('edmdata__trans_date'),monthly_count=Sum('edmdata__total_count'),clicked_count = Sum("edmdata__clicked"),opened_count= Sum("edmdata__opened"),delivered_count=Sum("edmdata__delivered"),bounced_count=Sum("edmdata__bounced"),complained_count=Sum("edmdata__complained"),unsubscribed_count=Sum("edmdata__unsubscribed")).order_by('-monthly_count').filter(month=email_month['month'],year=email_month['year'])

        for email in by_email_month:
            row_num = row_num + 1
            by_email.write(row_num,col_num+1,email.monthly_count)
            by_email.write(row_num,col_num+2,email.clicked_count)
            by_email.write(row_num,col_num+3,email.opened_count)
            by_email.write(row_num,col_num+4,email.delivered_count)
            by_email.write(row_num,col_num+5,email.bounced_count)
            by_email.write(row_num,col_num+6,email.complained_count)
            by_email.write(row_num,col_num+7,email.unsubscribed_count)

        col_num = col_num + 7


    #Top 25 Domain Sheet
    top25domain = wb.add_sheet("Top 25 Domain")
    
    #up to latest date
    #get the latest date
    latest_date = EdmData.objects.order_by('-trans_date').first()
    latest_date_str = latest_date.trans_date.strftime("%B %d %Y")
    top25domain.write(1,0,"Up to " + latest_date_str, font_style_header)

    #overall top 25 first
    top25domain.write(2,1,"Overall Top 25", font_style_header)

    domain_top = Domain.objects.annotate(total_overall_count=Sum('edmdata__total_count'),total_clicked=Sum('edmdata__clicked'),total_opened=Sum('edmdata__opened'),total_delivered=Sum('edmdata__delivered'),total_bounced=Sum('edmdata__bounced'),total_complained=Sum('edmdata__complained'),total_unsubscribed=Sum('edmdata__unsubscribed')).order_by('-total_overall_count')[:25]

    row_num = 3
    # headers
    top_domain_headers = ['Domain', 'Count', 'Clicked','Opened', 'Delivered', 'Bounced', 'Complained', 'Unsubscribed',]

    for col_num in range(len(top_domain_headers)):
        top25domain.write(row_num, col_num+1, top_domain_headers[col_num], font_style_column_header)

    #write data of top 25 overall
    # row_num = row_num + 1
    for domain in domain_top:
        row_num = row_num + 1
        top25domain.write(row_num,1,domain.email_domain)
        top25domain.write(row_num,2,domain.total_overall_count)
        top25domain.write(row_num,3,domain.total_clicked)
        top25domain.write(row_num,4,domain.total_opened)
        top25domain.write(row_num,5,domain.total_delivered)
        top25domain.write(row_num,6,domain.total_bounced)
        top25domain.write(row_num,7,domain.total_complained)
        top25domain.write(row_num,8,domain.total_unsubscribed)

    row_num = row_num + 2
    #per month
    #query the months
    #get the per month and render it
    domain_month = Domain.objects.all().annotate(month=ExtractMonth('edmdata__trans_date'),year=ExtractYear('edmdata__trans_date')).order_by('month','year').values('month','year').distinct()


    for month in domain_month:

        month_yr_str = str(calendar.month_name[month['month']]) + "-" + str(month['year'])

        #date and year of table 
        top25domain.write(row_num,0,month_yr_str,font_style_header)
        row_num = row_num + 1

        #table headers
        for col_num in range(len(top_domain_headers)):
            top25domain.write(row_num, col_num+1, top_domain_headers[col_num], font_style_column_header)

        #data
        top_domain_month = Domain.objects.all().annotate(month=ExtractMonth('edmdata__trans_date'),year=ExtractYear('edmdata__trans_date'),monthly_count=Sum('edmdata__total_count'),monthly_clicked = Sum("edmdata__clicked"),monthly_opened= Sum("edmdata__opened"),monthly_delivered=Sum("edmdata__delivered"),monthly_bounced=Sum("edmdata__bounced"),monthly_complained=Sum("edmdata__complained"),monthly_unsubscribed=Sum("edmdata__unsubscribed")).order_by('-monthly_count').filter(month=month['month'],year=month['year'])[:25]

        #render monthly data to table
        for domain in top_domain_month:
            row_num = row_num + 1
            top25domain.write(row_num,1,domain.email_domain)
            top25domain.write(row_num,2,domain.monthly_count)
            top25domain.write(row_num,3,domain.monthly_clicked)
            top25domain.write(row_num,4,domain.monthly_opened)
            top25domain.write(row_num,5,domain.monthly_delivered)
            top25domain.write(row_num,6,domain.monthly_bounced)
            top25domain.write(row_num,7,domain.monthly_complained)
            top25domain.write(row_num,8,domain.monthly_unsubscribed)

        row_num = row_num + 2
    

    #Monthly Overall Top 25 Sheet    
    monthlytop25domain = wb.add_sheet("Monthly Overall Top 25")

    #Domain List
    monthlytop25domain.write(0,1,"Domain List", font_style_header)
    monthlytop25domain.write(1,1,"Data Until " + latest_date_str, font_style_header)

    row_num = 4
    #latest date

    #for each month
    for month in domain_month:
        
        
        month_yr_str = str(calendar.month_name[month['month']]) + "-" + str(month['year'])

        monthlytop25domain.write(row_num,0,month_yr_str,font_style_header)
        row_num = row_num + 1
        monthlytop25domain.write(row_num,0,"Overall Top 25",font_style_header)
        row_num = row_num + 1
        starting_row = row_num 

        #counter variables
        rem_row = 0 #remaining rows
        total_rows = 25

        # count header
        monthlytop25domain.write_merge(row_num,row_num,1,2,"Count", font_style_column_header)

        #count
        top_domain_count = Domain.objects.all().annotate(month=ExtractMonth('edmdata__trans_date'),year=ExtractYear('edmdata__trans_date'),monthly_count=Sum('edmdata__total_count'),monthly_clicked = Sum("edmdata__clicked"),monthly_opened= Sum("edmdata__opened"),monthly_delivered=Sum("edmdata__delivered"),monthly_bounced=Sum("edmdata__bounced"),monthly_complained=Sum("edmdata__complained"),monthly_unsubscribed=Sum("edmdata__unsubscribed")).order_by('-monthly_count').filter(month=month['month'],year=month['year'])[:25]
        
        for domain in top_domain_count:
            row_num = row_num + 1
            monthlytop25domain.write(row_num,1,domain.email_domain)
            monthlytop25domain.write(row_num,2,domain.monthly_count)
        

        #clicked

        top_domain_clicked = Domain.objects.all().annotate(month=ExtractMonth('edmdata__trans_date'),year=ExtractYear('edmdata__trans_date'),monthly_count=Sum('edmdata__total_count'),monthly_clicked = Sum("edmdata__clicked"),monthly_opened= Sum("edmdata__opened"),monthly_delivered=Sum("edmdata__delivered"),monthly_bounced=Sum("edmdata__bounced"),monthly_complained=Sum("edmdata__complained"),monthly_unsubscribed=Sum("edmdata__unsubscribed")).order_by('-monthly_clicked').filter(month=month['month'],year=month['year'])[:25]

        row_num = starting_row
        # clicked header
        monthlytop25domain.write_merge(row_num,row_num,4,5,"Clicked", font_style_column_header)

        for domain in top_domain_clicked:
            row_num = row_num + 1
            monthlytop25domain.write(row_num,4,domain.email_domain)
            monthlytop25domain.write(row_num,5,domain.monthly_clicked)


        # row_num = row_num + (total_rows-rem_row)

        # opened
        top_domain_opened = Domain.objects.all().annotate(month=ExtractMonth('edmdata__trans_date'),year=ExtractYear('edmdata__trans_date'),monthly_count=Sum('edmdata__total_count'),monthly_clicked = Sum("edmdata__clicked"),monthly_opened= Sum("edmdata__opened"),monthly_delivered=Sum("edmdata__delivered"),monthly_bounced=Sum("edmdata__bounced"),monthly_complained=Sum("edmdata__complained"),monthly_unsubscribed=Sum("edmdata__unsubscribed")).order_by('-monthly_opened').filter(month=month['month'],year=month['year'])[:25]

        row_num = starting_row
        #opened header
        monthlytop25domain.write_merge(row_num,row_num,7,8,"Opened", font_style_column_header)

        for domain in top_domain_opened:
            row_num = row_num + 1
            monthlytop25domain.write(row_num,7,domain.email_domain)
            monthlytop25domain.write(row_num,8,domain.monthly_opened)
        
        #delivered
        top_domain_delivered = Domain.objects.all().annotate(month=ExtractMonth('edmdata__trans_date'),year=ExtractYear('edmdata__trans_date'),monthly_count=Sum('edmdata__total_count'),monthly_clicked = Sum("edmdata__clicked"),monthly_opened= Sum("edmdata__opened"),monthly_delivered=Sum("edmdata__delivered"),monthly_bounced=Sum("edmdata__bounced"),monthly_complained=Sum("edmdata__complained"),monthly_unsubscribed=Sum("edmdata__unsubscribed")).order_by('-monthly_delivered').filter(month=month['month'],year=month['year'])[:25]

        row_num = starting_row
        #delivered header
        monthlytop25domain.write_merge(row_num,row_num,10,11,"Delivered", font_style_column_header)

        for domain in top_domain_delivered:
            row_num = row_num + 1
            monthlytop25domain.write(row_num,10,domain.email_domain)
            monthlytop25domain.write(row_num,11,domain.monthly_delivered)

        #bounced
        top_domain_bounced = Domain.objects.all().annotate(month=ExtractMonth('edmdata__trans_date'),year=ExtractYear('edmdata__trans_date'),monthly_count=Sum('edmdata__total_count'),monthly_clicked = Sum("edmdata__clicked"),monthly_opened= Sum("edmdata__opened"),monthly_delivered=Sum("edmdata__delivered"),monthly_bounced=Sum("edmdata__bounced"),monthly_complained=Sum("edmdata__complained"),monthly_unsubscribed=Sum("edmdata__unsubscribed")).order_by('-monthly_bounced').filter(month=month['month'],year=month['year'])[:25]

        row_num = starting_row
        #bounced header
        monthlytop25domain.write_merge(row_num,row_num,13,14,"Bounced", font_style_column_header)

        for domain in top_domain_bounced:
            row_num = row_num + 1
            monthlytop25domain.write(row_num,13,domain.email_domain)
            monthlytop25domain.write(row_num,14,domain.monthly_bounced)

        #complained
        top_domain_complained = Domain.objects.all().annotate(month=ExtractMonth('edmdata__trans_date'),year=ExtractYear('edmdata__trans_date'),monthly_count=Sum('edmdata__total_count'),monthly_clicked = Sum("edmdata__clicked"),monthly_opened= Sum("edmdata__opened"),monthly_delivered=Sum("edmdata__delivered"),monthly_bounced=Sum("edmdata__bounced"),monthly_complained=Sum("edmdata__complained"),monthly_unsubscribed=Sum("edmdata__unsubscribed")).order_by('-monthly_complained').filter(month=month['month'],year=month['year'])[:25]

        row_num = starting_row
        #complained header
        monthlytop25domain.write_merge(row_num,row_num,16,17,"Complained", font_style_column_header)

        for domain in top_domain_complained:
            row_num = row_num + 1
            monthlytop25domain.write(row_num,16,domain.email_domain)
            monthlytop25domain.write(row_num,17,domain.monthly_complained)

        #unsubscribed
        top_domain_unsubscribed = Domain.objects.all().annotate(month=ExtractMonth('edmdata__trans_date'),year=ExtractYear('edmdata__trans_date'),monthly_count=Sum('edmdata__total_count'),monthly_clicked = Sum("edmdata__clicked"),monthly_opened= Sum("edmdata__opened"),monthly_delivered=Sum("edmdata__delivered"),monthly_bounced=Sum("edmdata__bounced"),monthly_complained=Sum("edmdata__complained"),monthly_unsubscribed=Sum("edmdata__unsubscribed")).order_by('-monthly_unsubscribed').filter(month=month['month'],year=month['year'])[:25]

        row_num = starting_row
        #unsubscribed header
        monthlytop25domain.write_merge(row_num,row_num,19,20,"Unsubscribed", font_style_column_header)

        for domain in top_domain_unsubscribed:
            row_num = row_num + 1
            monthlytop25domain.write(row_num,19,domain.email_domain)
            monthlytop25domain.write(row_num,20,domain.monthly_unsubscribed)
    
        row_num = row_num + 2




    wb.save(response)

    return response
