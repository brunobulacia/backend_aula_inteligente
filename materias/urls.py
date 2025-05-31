from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('cursos', views.CursoViewSet)
router.register('materias', views.MateriaViewSet)
router.register('gestiones', views.GestionViewSet)
router.register('horarios', views.HorarioViewSet)
router.register('dias', views.DiaViewSet)
router.register('dia-horarios', views.DiaHorarioViewSet)
router.register('asignaciones', views.MateriaGestionCursoViewSet)

urlpatterns = router.urls