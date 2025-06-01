from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('fichas', views.FichaInscripcionViewSet)

urlpatterns = router.urls