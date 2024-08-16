from django.urls  import path
from . import views
app_name = 'Mappa'

urlpatterns = [
    path('select_template/', views.select_template, name='select_template'),
    path('show_template/<str:date_str>/', views.show_template, name='show_template'),
]