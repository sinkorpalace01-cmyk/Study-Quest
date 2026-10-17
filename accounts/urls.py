from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.SignInView.as_view(), name="login"),
    path("logout/", views.SignOutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("delete/", views.delete_account, name="delete_account"),
    path("invite/", views.invite, name="invite"),
    path("invite/<uuid:token>/", views.invite_accept, name="invite_accept"),
    path("password-reset/", views.BrandedPasswordResetView.as_view(template_name="accounts/password_reset.html", email_template_name="emails/password_reset.txt", html_email_template_name="emails/password_reset.html", subject_template_name="accounts/password_reset_subject.txt", success_url="/accounts/password-reset/done/"), name="password_reset"),
    path("password-reset/done/", views.BrandedPasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", views.BrandedPasswordResetConfirmView.as_view(template_name="accounts/password_reset_confirm.html", success_url="/accounts/reset/done/"), name="password_reset_confirm"),
    path("reset/done/", views.BrandedPasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"), name="password_reset_complete"),
    path("password-change/", views.BrandedPasswordChangeView.as_view(template_name="accounts/password_change.html", success_url="/accounts/profile/"), name="password_change"),
]
