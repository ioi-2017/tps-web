# Mohammad Javad Naderi
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.views import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.utils.translation import ugettext as _

@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {
        'user': request.user
    })


def login(request):
    redirect_to = request.POST.get("next",
                                   request.GET.get("next", ''))
    if request.user.is_authenticated():
        return HttpResponseRedirect(redirect_to)
    else:
        return auth_login(request, template_name="accounts/login.html", redirect_field_name="next")


def logout(request):
    redirect_to = request.POST.get("next",
                                   request.GET.get("next", reverse("accounts:login")))
    if not request.user.is_authenticated():
        return HttpResponseRedirect(redirect_to)
    auth_logout(request)
    messages.success(request, _("You've successfully logged out"))
    return HttpResponseRedirect(redirect_to)