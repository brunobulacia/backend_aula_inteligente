from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('fichas', views.FichaInscripcionViewSet)
router.register('notas', views.NotaViewSet)
router.register('asistencias', views.AsistenciaViewSet)
router.register('participaciones', views.ParticipacionViewSet)
router.register('profesores', views.ProfesorViewSet, basename='profesores')
router.register('vista-alumno', views.AlumnoViewSet, basename='vista-alumno')

urlpatterns = router.urls