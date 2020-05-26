from django.contrib.auth.views import LoginView
from django.urls import path, include

import authentication.views as auth_views
from . import views

app_name = 'fohseriet'

login_urls = ([
    path('', LoginView.as_view(), name='index'),
    path('cred/', views.LoginCredentialsView.as_view(), name='cred'),
    path('cas/', auth_views.LoginCas.as_view(), name='cas'),
], 'logga-in')

event_urls = ([
    path('', views.HappeningListView.as_view(), name="happening-list"),
    path('<int:pk>/', views.HappeningUpdateView.as_view(), name='happening-update'),
    path('skapa-evenemang', views.HappeningCreateView.as_view(), name='create_happening'),
], 'evenemang')

user_urls = ([
    path('', views.MenuView.as_view(template_name='fohseriet/anvandare.html'), name="index"),
], 'anvandare')


urlpatterns = [
    path('', views.MenuView.as_view(template_name='fohseriet/index.html'), name='index'),

    path('logga-in/', include(login_urls)),
    path('logga-ut/', views.LogoutView.as_view(), name='logga-ut'),
    path('evenemang/', include(event_urls)),
    path('anvandare/', include(user_urls)),
]