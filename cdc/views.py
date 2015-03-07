from django.shortcuts import (
    render, render_to_response, redirect, get_object_or_404)
from models import SiteUser, LoginSession, Testimonial
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from .forms import *
from .actions import *


def index(request):
    if request.GET.get('logout', False):
        context = {'script': 'True'}
        return render(request, 'cdc/index.html', context)
    return render(request, 'cdc/index.html')


def contact(request):
    return render(request, 'cdc/contact.html')


def about(request):
    return render(request, 'cdc/about.html')


def testimonials(request):
    user = None
    if is_logged_in(request):
        user = get_user(request)

    if user and request.GET.get('remove', False):
        entry = Testimonial.objects.get(postedby=request.GET['remove'])
        entry.delete()

    template_values = {
            'testimonials': Testimonial.objects.all(),
            'user': user
    }
    return render(request, 'cdc/testimonials.html', template_values)


def login_view(request):
    if request.method == 'GET':
        # Split into user login, company login, admin login
        if is_logged_in(request):  # or is_admin(request):
            return HttpResponseRedirect('home')
        else:
            return render(request, 'cdc/login.html')

    account = request.POST.get('account')
    company = request.POST.get('company')
    pin = request.POST.get('pin')

    # Make sure all required fields are in request
    if (account is None or company is None or pin is None):
        context = {'error': 'Please fill out all fields before submitting.'}
        return render(request, 'cdc/login.html', context)

    # Authentication
    user = authenticate(username=account, password=pin)
    if user is not None:
        if user.is_active:
            login(request, user)
            response = HttpResponseRedirect('home')
            return response

    context = {
        'error': ("The username/password combination you "
                  "entered doesn't match.")}
    return render(request, 'cdc/login.html', context)


def login_admin(request):
    if request.method == 'GET':
        return render(request, 'cdc/admin.html')

    if request.method == 'POST':
        # Do admin login
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None and user.is_superuser:
            # create admin session token
            login(request, user)
            response = redirect('/accounts/home')
            return response

    context = {
        'error': ("The username/password combination you "
                  "entered doesn't match.")}
    return render(request, 'cdc/admin.html', context)


def settings(request):
    if not is_logged_in(request):
        return HttpResponseRedirect('login')

    try:
    if request.method == 'POST':
        newpass = request.POST.get('newpass')
        deleteaccount = request.POST.get('deleteaccount')
        deletefiles = request.POST.get('deletefiles')
        user = User.objects.get(username__exact==user.username)

        if newpass is not None:
            user.password = newpass
            user.save()

        elif deleteaccount is not None:
            user.delete()

        elif deletefiles is not None:
            delete_files(user.username)
    except Exception as e:
        return HttpResponse(str(e))

    return render(request, 'cdc/settings.html')


def logout_view(request):
    """
    - Need to enable auto session store management
    """
    logout(request)
    response = redirect('../?logout=true')
    return response


def account_home(request):
    if not is_logged_in(request):
        return HttpResponseRedirect('login')

    user = get_user(request)
    page = request.GET.get('page', False)
    success = request.GET.get('success', False)
    context = {'page': page}
    return render(request, 'cdc/account.html', context)


def upload(request):
    if not is_logged_in(request):
        return HttpResponseRedirect('login')

    username = request.user.username
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                handle_uploaded_file(
                    request.FILES['file'], request.POST['title'], username)
                return HttpResponseRedirect('success')
            except Exception as e:
                return HttpResponse(str(e))

    else:
        form = UploadFileForm()
    return render_to_response('cdc/upload.html', {'form': form})


def download(request):
    if not is_logged_in(request):
        return HttpResponseRedirect('login')

    if request.method == 'GET':
        filename = request.GET.get('filename')
        filepath = os.path.join('/uploads', request.user.username, filename)
        if os.path.exists(filepath):
            fp = open(filepath)
            response = HttpResponse(fp.read())
            fp.close()
            response['Content-Type'] = 'application/octet-stream'
            return response
    
    return HttpResponse('File not found')



def form(request):
    if request.method == 'POST':
        f = TestimonialForm(request.POST, request.FILES)
        entry = Testimonial(
            text=request.POST['text'], postedby=request.POST['postedby'])
        entry.save()
        return HttpResponseRedirect('testimonials')
    else:
        f = TestimonialForm()
    return render_to_response('cdc/form.html', {'form': f})


def success(request):
    return render(request, 'cdc/success.html')


def filings(request):
    if not is_logged_in(request):
        return HttpResponseRedirect('login')

    files = list_files(request.user.username, '/incoming/')
    template_values = {
        'files': files,
        'mode': 'incoming'}
    return render(request, 'cdc/files.html', template_values)


def reports(request):
    if not is_logged_in(request):
        return HttpResponseRedirect('login')

    files = list_files(request.user.username, '/outgoing/')
    template_values = {
        'files': files,
        'mode': 'outgoing'}
    return render(request, 'cdc/files.html', template_values)


def admin(request):
    if not is_admin(request):
        return HttpResponseRedirect('login_admin')

    message = ''
    files = None
    create = None
    accounts = None

    if request.method == 'POST':
        # Password reset
        if request.POST.get('pwreset', False):
            user = get_object_or_404(User, username=request.POST['account'])
            user.set_password(request.POST.get('pin', False))
            user.save()
            message += 'Password successfully reset!\n'

        # Delete User
        if request.POST.get('delete', False):
            user = User.objects.get(username__exact=request.POST.get('account'))
            if user is not None:
                user.delete()
                message += 'User successfully deleted!\n'
            else:
                message += 'User does not exist\n'

        # Create new site user
        if request.POST.get('newuser', False):
            account = request.POST.get('account')

            user = None
            try:
                user = User.objects.get(username__exact=account)
            except Exception as e:
                pass

            if user is not None:
                message += 'Error: User already exists in database.\n'

            else:
                account = request.POST.get('account', False)
                pin = request.POST.get('pin', False)
                company = request.POST.get('company', False)
                user = User.objects.create_user(account, '', pin)
                user.save()
                siteuser = SiteUser(user=user, company=company)
                siteuser.save()

                # Create the upload and download directories for the new user
                targetdir = 'uploads/' + user.username
                if not os.path.exists(targetdir):
                    os.makedirs(targetdir + '/incoming')
                    os.makedirs(targetdir + '/outgoing')
                message += 'User successfully created!\n'

        # Create new admin
        if request.POST.get('newadmin', False):
            account = request.POST.get('account')

            try:
                user = User.objects.get(username__exact=account)
            except Exception as e:
                user = None

            if user is not None:
                message += 'Error: User already exists in database.\n'

            else:
                username = request.POST.get('username', False)
                passwd = request.POST.get('password', False)
                user = User.objects.create_user(username, '', passwd)
                user.is_superuser = True
                user.save()
                siteuser = SiteUser(user=user, company="Admin")
                siteuser.save()
                message += 'Admin successfully created!\n'

    if request.method == 'GET':
        if request.GET.get('user_button', False):
            create = 'newuser'
        elif request.GET.get('admin_button', False):
            create = 'newadmin'

        # Delete a file
        if request.GET.get('delete', False):
            try:
                os.remove(request.GET['delete'])
                message += 'File \'' + request.GET['delete'] + '\' deleted!\n'
            except OSError:
                message += 'That file does not exist.\n'

        # List a user's files
        elif request.GET.get('search'):
            files = list_files(
                request.GET.get('search', ''), '/' + request.GET.get('mode', ''))
            if not files:
                message += "No files found!\n"

        if request.GET.get('list_users'):
            accounts = User.objects.all()

        if is_admin(request):
            template_values = {
                'users': accounts,
                'create': create,
                'message': message,
                'files': files,
                'mode': request.GET.get('mode', False),
                'search': request.GET.get('search', False)
            }
            return render(request, 'cdc/account.html', template_values)

    return HttpResponseRedirect('login/admin')
