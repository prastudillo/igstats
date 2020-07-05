from selenium import webdriver
import unittest

class NewVisitorTest(unittest.TestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_can_start_a_list_and_retrive_it_later(self):
        #Check the app and check its home page
        self.browser.get('http://localhost:8000')

        #notices the page title and header mention IGStats
        self.assertIn('IGStats', self.browser.title)
        self.fail('Finish the test')

        #uploads csv files into the form

        #redirects to success page

        #exports excel file

if __name__ == '__main__':
    unittest.main(warnings='ignore')