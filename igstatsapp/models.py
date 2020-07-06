from django.db import models

# Create your models here.

#campaign type data
class CampaignType(models.Model):
    ticker = models.CharField(max_length=5, null=True)
    campaign_id = models.CharField(max_length=100, primary_key=True)

#domain data
class Domain(models.Model):
    email_domain = models.CharField(max_length=100, primary_key=True)


# Csv_data; Staging table
class CsvData(models.Model):

    ticker = models.CharField(max_length=5, null=True)
    domain = models.CharField(max_length=100)
    campaign_id = models.CharField(max_length=100)
    recipient = models.CharField(max_length=100)
    clicked = models.PositiveIntegerField()
    opened = models.PositiveIntegerField()
    delivered = models.PositiveIntegerField()
    bounced = models.PositiveIntegerField()
    complained = models.PositiveIntegerField()
    unsubscribed = models.PositiveIntegerField()
    trans_date  = models.DateTimeField()


#edm data
class EdmData(models.Model):

    ticker = models.CharField(max_length=5, null=True)
    domain = models.CharField(max_length=100)
    campaign_id = models.ForeignKey(CampaignType,on_delete=models.CASCADE)
    recipient_email = models.CharField(max_length=100)
    recipient = models.ForeignKey(Domain,on_delete=models.CASCADE)
    clicked = models.PositiveIntegerField()
    opened = models.PositiveIntegerField()
    delivered = models.PositiveIntegerField()
    bounced = models.PositiveIntegerField()
    complained = models.PositiveIntegerField()
    unsubscribed = models.PositiveIntegerField()
    trans_date  = models.DateTimeField()
    
    total_count = models.IntegerField()

    def save(self, *args, **kwargs):
        self.total_count = sum(
            [self.clicked, self.opened, self.delivered, self.bounced, self.complained, self.unsubscribed])
        return super(EdmData, self).save(*args, **kwargs)

