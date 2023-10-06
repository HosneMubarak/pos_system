from django.urls import path

from . import views

app_name = 'account'

urlpatterns = [
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('users/', views.user_list_view, name='user-list'),
    path('users/add/', views.user_add_view, name='user-add'),
    path('users/edit/<int:user_id>/', views.user_edit_view, name='user-edit'),
    path('users/delete/<int:user_id>/', views.user_delete_view, name='user-delete'),
    path('permission-denied/', views.permission_denied_view, name='permission-denied')
]
