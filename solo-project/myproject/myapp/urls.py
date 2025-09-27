from django.urls import path
from .import views

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register', views.register, name='register'),
    path('register_page' , views.register_page ,name='register_page'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('login_page', views.login_page, name='login_page'),

    # Parent dashboard
    path('parent_dashboard', views.parent_dashboard, name='parent_dashboard'),
    path('add_kid', views.add_kid, name='add_kid'),

    # Kid self-dashboard
    path("kid/dashboard/", views.kid_dashboard, name="kid_dashboard"),
    path("kid/balance/", views.kid_balance, name="kid_balance"),
    path("kid/goals/", views.kid_goals, name="kid_goals"),
    path("kid/transactions/", views.kid_transactions, name="kid_transactions"),
    path("kid/rewards/", views.kid_rewards, name="kid_rewards"),
    path("kid/transaction/", views.make_transaction, name="make_transaction"),
    path("kid/add_goal/", views.add_goal, name="add_goal"), 

    # Parent views of kids
    path("parent/kid/<int:kid_id>/goals/", views.parent_kid_goals, name="parent_kid_goals"),
    path("parent/kid/<int:kid_id>/transactions/", views.parent_kid_transactions, name="parent_kid_transactions"),
    path('parent/kid/<int:kid_id>/rewards/', views.parent_kid_rewards, name='parent_kid_rewards'),
    path('parent/kid/<int:kid_id>/remove/', views.remove_kid, name='remove_kid'),
    path("parent/kid/<int:kid_id>/set_allowance/", views.set_allowance, name="set_allowance"),
    path('parent/tips/', views.parent_tips, name='parent_tips'),

    #API
    
    


]
