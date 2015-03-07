from models import LoginSession, SiteUser
import os
from django.contrib.auth.models import User

def handle_uploaded_file(f, title, user):
    targetdir = 'uploads/' + user.__str__() + '/incoming/'
    if not os.path.exists(targetdir):
        os.makedirs(targetdir)
    with open(targetdir + title, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

# def is_logged_in(request):
#     # Session hijacking...
#     return LoginSession.objects.filter(token=request.COOKIES.get('secret_token', False)).exists()

def is_logged_in(request):
    return request.user.is_authenticated()

def is_admin(request):
    return is_logged_in(request) and request.user.is_superuser

def get_user(request):
    return request.user

def list_files(account, mode):
    targetdir = '/uploads/%s/%s/' % (account , mode)
    targetdir = targetdir.replace('../', '')
    if os.path.exists(targetdir):
        return os.listdir(targetdir)
    else:
        return False
