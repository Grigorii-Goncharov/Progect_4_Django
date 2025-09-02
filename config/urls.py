
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', include('mailservices.urls', namespace='mailservices')),
    # path('users/', include('users.urls', namespace='users')),
]
