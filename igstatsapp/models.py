from django.db import models

# Create your models here.

#campaign type data
class CampaignType(models.Model):
    ticker = models.CharField(max_length=4, null=True)
    campaign_id = models.CharField(max_length=100, primary_key=True)

#domain data
class Domain(models.Model):
    email_domain = models.CharField(max_length=100, primary_key=True)


#edm data
class EdmData(models.Model):

    ticker = models.CharField(max_length=5, null=True)
    domain = models.CharField(max_length=100)
    campaign_id = models.CharField(max_length=100, blank=False)
    recipient = models.CharField(max_length=100)
    clicked = models.PositiveIntegerField()
    opened = models.PositiveIntegerField()
    delivered = models.PositiveIntegerField()
    bounced = models.PositiveIntegerField()
    complained = models.PositiveIntegerField()
    unsubscribed = models.PositiveIntegerField()
    trans_date  = models.DateTimeField()

