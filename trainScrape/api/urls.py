from django.urls import path, include
from . import views
from rest_framework import routers
from django.contrib import admin
from django.urls import path
from .views import get_json

# router = routers.DefaultRouter()
# router.register(r'trains', views.TrainViewSet)

urlpatterns = [
    # path('', include(router.urls)),
    # path('api-auth/', include('rest_framework.urls'))
    path('admin/', admin.site.urls),
    path('getjson/', get_json, name='get_json'),
]