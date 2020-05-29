from django.urls import path, include

import authentication.views as auth_views
from . import views

app_name = 'fohseriet'

login_urls = ([
    path('', views.LoginView.as_view(), name='index'),
    path('cred/', views.LoginCredentialsView.as_view(), name='cred'),
    path('cas/', auth_views.login.LoginCas.as_view(), name='cas'),
], 'logga-in')

happening_urls = ([
    path('', views.HappeningListView.as_view(), name="lista"),
    path('<int:pk>/redigera/', views.HappeningUpdateView.as_view(), name='redigera'),
    path('<int:pk>/anmalda/', views.HappeningRegisteredListView.as_view(), name='anmalda'),
    path('skapa/', views.HappeningUpdateView.as_view(), name='skapa'),
], 'evenemang')

user_urls = ([
    path('', views.UsersListView.as_view(), name="index"),
    path('<int:pk>/redigera/', views.UserUpdateView.as_view(), name='redigera'),
    path('<int:pk>/anmalningar/', views.UserRegistrationsListView.as_view(), name='anmalningar'),
], 'anvandare')

registration_urls = ([
    path('<int:pk>/redigera/', views.RegistrationUpdateView.as_view(), name="redigera"),
], 'anmalan')

urlpatterns = [
    path('', views.FohserietMenuView.as_view(template_name='fohseriet/index.html'), name='index'),

    path('logga-in/', include(login_urls)),
    path('logga-ut/', views.LogoutView.as_view(), name='logga-ut'),
    path('evenemang/', include(happening_urls)),
    path('anvandare/', include(user_urls)),
    path('anmalan/', include(registration_urls)),
]