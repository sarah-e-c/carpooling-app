# import unittest
# import requests
# import time
# import os
# import secrets

# ENDPOINT = 'http://127.0.0.1:8000'

# class Tests(unittest.TestCase):
    
#     def test_driver_auth(self):
#         """
#         Testing that the driver auth cookie is working
#         """
#         session = requests.Session()
#         session.cookies.set('driver_access_key_time', str(time.time()))
#         source = requests.get(f'{ENDPOINT}/driver/crowder/sarah', cookies=session.cookies)
#         self.assertEqual(source.status_code, 200)
    
#     def test_driver_not_found(self):
#         """
#         Method to test that the driver not found page is working
#         """
#         session = requests.Session()
#         session.cookies.set('driver_access_key_time', str(time.time()))
#         source = requests.get(f'{ENDPOINT}/driver/{secrets.token_urlsafe(4)}/{secrets.token_urlsafe(4)}', cookies=session.cookies)
#         self.assertEqual(source.text, 'No driver was found.')


#     def test_driver_auth_time(self):
#         """
#         Testing that the driver auth cookie is timing out, and that it redirects to the get_driver_access page
#         """
#         session = requests.Session()
#         session.cookies.set('driver_access_key_time', str(time.time() - 60*60*24*30*12))
#         source = requests.get(f'{ENDPOINT}/driver/crowder/sarah', cookies=session.cookies)

#         self.assert_(source.history[0].is_redirect)

#     def test_driver_access_key_validation(self):
#         """
#         Testing that the driver access key validation is working with the wrong key
#         """
#         source = requests.post(f'{ENDPOINT}/get-driver-access/crowder/sarah', data={'key': 'wrong'})
#         self.assertEqual(source.status_code, 203)

#     def test_test_auth_cookie(self):
#         """
#         Testing that the test auth cookie is working
#         """
#         source = requests.post(f'{ENDPOINT}/get-driver-access/crowder/sarah', data={'key': os.environ.get('PERM_TEST_KEY')})
#         self.assertEqual(source.status_code, 200)


#     def test_driver_auth_none(self):
#         """
#         Testing that not having an auth cookie redirects to the get_driver_access page
#         """
#         session = requests.Session()
#         session.cookies.clear()
#         source = requests.get(f'{ENDPOINT}/driver/crowder/sarah', cookies=session.cookies)
#         self.assert_(source.history[0].is_redirect)
        

#     def test_admin_auth(self):
#         """
#         Testing that admin authorization is working
#         """
#         response = requests.post(f'{ENDPOINT}/admin', data={'username': os.environ.get('ADMIN_USERNAME'), 'password': os.environ.get('ADMIN_PASSWORD')})
#         self.assertEqual(response.status_code, 200)
#         response = requests.post(f'{ENDPOINT}/admin', data={'username': os.environ.get('ADMIN_USERNAME'), 'password': 'wrong'})
#         self.assertEqual(response.status_code, 203)
#         response = requests.post(f'{ENDPOINT}/admin', data={'username': 'wrong', 'password': os.environ.get('ADMIN_PASSWORD')})
#         self.assertEqual(response.status_code, 203)

# if __name__ == '__main__':
#     unittest.main()
