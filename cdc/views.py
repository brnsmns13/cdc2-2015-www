from django.shortcuts import (
    render, render_to_response, redirect, get_object_or_404)
from models import SiteUser, LoginSession, Testimonial
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from .forms import *
from .actions import *

def index(request):
    if request.GET.get('logout', False):
        context = { 'script' : 'True' }
        return render(request, 'cdc/index.html', context)
    return render(request, 'cdc/index.html')

def contact(request):
    return render(request, 'cdc/contact.html')

def about(request):
    return render(request, 'cdc/about.html')

def testimonials(request):
    # This logic needs to be switched around, need auth to delete
    if request.GET.get('remove', False):
        entry = Testimonial.objects.get(postedby=request.GET['remove'])
        entry.delete()
    user = None
    if is_logged_in(request):
        user = get_user(request)

    template_values = {
            'testimonials': Testimonial.objects.all(),
            'user': user
    }
    return render(request, 'cdc/testimonials.html', template_values)

def login(request):
    """
    - (pin/next) is indicator of company or user login
    """
    # Split into user login, company login, admin login
    if is_logged_in(request): # or is_admin(request):
        return HttpResponseRedirect('home')

    # Make sure all required fields are in request
    elif (request.POST.get('next', False) and
         (not request.POST.get('account', False) or
          not request.POST.get('company', False) or
          not request.POST.get('pin', False))):
        context = { 'error' : "Please fill out all fields before submitting." }
        return render(request, 'cdc/login.html', context)

    # Company login
    elif (request.POST.get('account', False) and 
            request.POST.get('company', False) and 
            request.POST.get('pin', False)):
        # Authentication
        account = request.POST['account']
        company = request.POST['company']
        pin = request.POST['pin']
        # Make sure all POST variables are present
        if account and company and pin:
            if User.objects.filter(username=account).exists():
                siteuser = SiteUser.objects.get(
                    company=company, user=User.objects.get(username=account))
                # if the user supplied the correct password
                print account, company, pin
                if siteuser.user.check_password(pin):
                    print "authed"
                    token = create_session(siteuser.user.username)
                    response = HttpResponseRedirect('home')
                    response.set_cookie('secret_token', token)
                    return response
                else:
                    context = {
                        'error' : ("The username/password combination you "
                                   "entered doesn't match.") }
                    return render(request, 'cdc/login.html', context)
            else:
                context = { 'error' : "The user you requested was not found." }
                return render(request, 'cdc/login.html', context)

    # Admin user login
    elif request.POST.get('admin', False):
        user = get_object_or_404(
            User, username=request.POST.get('username', False))
        if (user.check_password(request.POST.get('password', True)) and
                user.is_superuser):
            token = create_session(user.username)
            response = HttpResponseRedirect('home')
            response.set_cookie('secret_token', token)
            return response
    else:
        return render(request, 'cdc/login.html')

def login_admin(request):
    return render(request, 'cdc/admin.html')

def settings(request):
    return render(request, 'cdc/settings.html')

def logout(request):
    """
    - Need to enable auto session store management
    """
    response = redirect('../?logout=true')
    response.delete_cookie('secret_token')
    try:
        LoginSession.objects.filter(
                token=request.COOKIES.get('secret_token', False)).delete()
        print "Session deleted successfully"
    except Exception as e:
        print "could not delete session"
        print e
    return response

def account_home(request):
    if is_logged_in(request):
        user = get_user(request)
        page = request.GET.get('page', False)
        success = request.GET.get('success', False)
        context = { 'user' : user, 'page' : page }
        return render(request, 'cdc/account.html', context)
    return HttpResponseRedirect('login')

def upload(request):
    user = get_user(request).username
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(
                request.FILES['file'], request.POST['title'], user)
            return HttpResponseRedirect('success')
    else:
        form = UploadFileForm()
    return render_to_response('cdc/upload.html', {'form': form})

def form(request):
    if request.method == 'POST':
        form = TestimonialForm(request.POST, request.FILES)
        entry = Testimonial(
            text=request.POST['text'], postedby=request.POST['postedby'])
        entry.save()
        return HttpResponseRedirect('testimonials')
    else:
        form = TestimonialForm()
    return render_to_response('cdc/form.html', {'form': form})

def success(request):
    return render(request, 'cdc/success.html')

def filings(request):
    user = get_user(request)
    files = list_files(user, '/incoming/')
    template_values = {
        'files': files,
        'user': user,
        'mode': 'incoming'}
    return render(request, 'cdc/files.html', template_values)

def reports(request):
    user = get_user(request)
    files = list_files(user, '/outgoing/')
    template_values = {
        'files': files,
        'user': user,
        'mode': 'outgoing'}
    return render(request, 'cdc/files.html', template_values)

def admin(request):
    message = ''
    files = None
    create = None
    accounts = None
    if request.GET.get('user_button', False):
        create = 'newuser'
    elif request.GET.get('admin_button', False):
        create = 'newadmin'

    # Password reset
    if request.POST.get('pwreset', False):
        user = get_object_or_404(User, username=request.POST['account'])
        user.set_password(request.POST.get('pin', False))
        user.save()
        message += 'Password successfully reset!\n'

    # Delete User
    if request.POST.get('delete', False):
        user = get_object_or_404(User, username=request.POST['account'])
        user.delete()
        message += 'User successfully deleted!\n'

    # Create new site user
    if request.POST.get('newuser', False):
        account = request.POST.get('account', False)
        if User.objects.filter(username=account).exists():
            message += 'Error: User already exists in database.\n'
        else:
            account = request.POST.get('account', False)
            pin = request.POST.get('pin', False)
            company = request.POST.get('company', False)
            user = User.objects.create_user(account, '', pin)
            siteuser = SiteUser(user=user, company=company)
            siteuser.save()
            # Create the upload and download directories for the new user
            targetdir = 'uploads/' + user.username
            if not os.path.exists(targetdir):
                os.makedirs(targetdir + '/incoming')
                os.chmod(targetdir + '/incoming', 0777)
                os.makedirs(targetdir + '/outgoing')
                os.chmod(targetdir + '/outgoing', 0777)
            message += 'User successfully created!\n'

    # Create new admin
    if request.POST.get('newadmin', False):
        account = request.POST.get('account', False)
        if User.objects.filter(username=account).exists():
            message += 'Error: User already exists in database.\n'
        else:
            username = request.POST.get('username', False)
            passwd = request.POST.get('passwrod', False)
            user = User.objects.create_user(username, '', passwd)
            user.is_superuser = True
            user.save()
            siteuser = SiteUser(user=user, company="Admin")
            siteuser.save()
            message += 'Admin successfully created!\n'

    # Delete a file
    if request.GET.get('delete', False):
        try:
            os.remove(request.GET['delete'])
            message += 'File \'' + request.GET['delete'] + '\' deleted!\n'
        except OSError:
            message += 'That file does not exist.\n'

    # List a user's files
    if request.GET.get('search', False):
        files = list_files(
            request.GET.get('search', ''), '/' + request.GET.get('mode', ''))
        if not files:
            message += "No files found!\n"
    if request.GET.get('list_users', False):
        accounts = User.objects.all()
    if get_user(request) and get_user(request).is_superuser:
        template_values = {
            'users' : accounts,
            'create' : create,
            'message' : message,
            'files' : files,
            'mode' : request.GET.get('mode', False),
            'search' : request.GET.get('search', False),
            'user' : get_user(request) 
        }
        return render(request, 'cdc/account.html', template_values)
    return HttpResponseRedirect('login/admin')
