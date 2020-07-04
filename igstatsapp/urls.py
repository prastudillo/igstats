from django.urls import path
from django.conf import settings
from django.conf.urls.static import static


from .views import (
    home_view,
    FileFieldView,
    success_page_view,
    download_excel_report
)


urlpatterns = [

    # home page
    path('', FileFieldView.as_view(), name='home'),
    path('success', success_page_view, name='success'),
    path('export', download_excel_report, name='export'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)