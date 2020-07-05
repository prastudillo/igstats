from django.test import TestCase
from django.urls import reverse
from igstatsapp.views import FileFieldView

# Create your tests here.
class HomePageTest(TestCase):

    def test_root_url_resolves_to_home_page_view(self):
        found = reverse(FileFieldView.as_view())
        self.assertEqual(found.func, FileFieldView.as_view())