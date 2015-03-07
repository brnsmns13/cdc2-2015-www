from models import LoginSession, SiteUser
import os
from django.contrib.auth.models import User

def handle_uploaded_file(f, title, user):
    targetdir = os.path.join('/uploads', user, 'incoming')
    if not os.path.exists(targetdir):
        os.makedirs(targetdir)
    target_file = os.path.join(targetdir, title)
    with open(target_file, 'wb+') as destination:
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

def delete_files(account):
    incoming_dir = os.path.join('/uploads', account , 'incoming')
    outgoing_dir = os.path.join('/uploads', account , 'outgoing')

    for _, __, f in os.path.walk(incoming_dir):
        os.remove(f)

    for _, __, f in os.path.walk(outgoing_dir):
        os.remove(f)



