# Mohammad Javad Naderi
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, resolve_url
from django.contrib.auth.views import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.utils.http import is_safe_url
from django.utils.translation import ugettext as _

from cps import settings


@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {
        'user': request.user
    })


def login(request):
    redirect_to = request.POST.get("next",
                                   request.GET.get("next", reverse("problems:problems")))
    if request.user.is_authenticated():
        return HttpResponseRedirect(redirect_to)
    else:
        if request.method == "POST":
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():

                # Ensure the user-originating redirection url is safe.
                if not is_safe_url(url=redirect_to, host=request.get_host()):
                    redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

                # Okay, security check complete. Log the user in.
                auth_login(request, form.get_user())

                return HttpResponseRedirect(redirect_to)
        else:
            form = AuthenticationForm(request)

        return render(request, "accounts/login.html", context={"form": form})


def logout(request):
    redirect_to = request.POST.get("next",
                                   request.GET.get("next", reverse("accounts:login")))
    if not request.user.is_authenticated():
        return HttpResponseRedirect(redirect_to)
    auth_logout(request)
    messages.success(request, _("You've successfully logged out"))
    return HttpResponseRedirect(redirect_to)