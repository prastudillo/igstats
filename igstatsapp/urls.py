from django.urls import path
from django.conf import settings

from .views import (
    home_view,
    success_page_view
)


urlpatterns = [

    # home page

    path('', home_view, name='home'),
    path('success', success_page_view, name='success'),

]
