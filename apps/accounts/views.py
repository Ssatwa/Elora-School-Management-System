from django.contrib.auth.views import LoginView

from apps.accounts.forms import SchoolAuthenticationForm


class SchoolLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = SchoolAuthenticationForm
    redirect_authenticated_user = True
