from django.urls import path, include

import authentication.views as auth_views
import nollesystemet.views as views

login_urls = ([
    path('', views.LoginViewFohseriet.as_view(), name='index'),
    path('cred/', views.LoginCredentialsViewFohseriet.as_view(), name='cred'),
    path('cas/', auth_views.login.LoginCas.as_view(), name='cas'),
], 'logga-in')

happening_urls = ([
    path('', views.HappeningListViewFohseriet.as_view(), name="lista"),
    path('<int:pk>/redigera/', views.HappeningUpdateView.as_view(), name='redigera'),
    path('<int:pk>/anmalda/', views.HappeningRegisteredListView.as_view(), name='anmalda'),
    path('skapa/', views.HappeningUpdateView.as_view(), name='skapa'),
    path('<int:pk>/ladda-ned-anmalda/', views.HappeningDownloadView.as_view(), name='ladda-ned-anmalda'),
], 'evenemang')

user_urls = ([
    path('', views.UsersListView.as_view(), name="index"),
    path('skapa/', views.UserUpdateView.as_view(), name='skapa'),
    path('<int:pk>/redigera/', views.UserUpdateView.as_view(), name='redigera'),
    path('<int:pk>/anmalningar/', views.UserRegistrationsListView.as_view(), name='anmalningar'),
], 'anvandare')

registration_urls = ([
    path('<int:pk>/redigera/', views.RegistrationUpdateView.as_view(), name="redigera"),
], 'anmalan')

nolle_form_urls = ([
    path('', views.NolleFormInspectView.as_view(), name="index"),
    path('ladda-ned-svar/', views.NolleFormDownloadView.as_view(), name="ladda-ned-svar"),
], 'nolleenkaten')

fohseriet_urls = ([
    path('', views.misc.FohserietMenuView.as_view(template_name='fohseriet/index.html'), name='index'),

    path('logga-in/', include(login_urls)),
    path('logga-ut/', views.authentication.LogoutViewFohseriet.as_view(), name='logga-ut'),
    path('evenemang/', include(happening_urls)),
    path('anvandare/', include(user_urls)),
    path('anmalan/', include(registration_urls)),
    path('nolleenkaten/', include(nolle_form_urls)),
], 'fohseriet')
