from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class Direccion(models.Model):
    ciudad = models.CharField(max_length=50)
    zona = models.CharField(max_length=50, blank=True, null=True)
    calle = models.CharField(max_length=100)
    numero = models.CharField(max_length=10)
    referencia = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.calle} #{self.numero}, {self.zona or ''} - {self.ciudad}"

class UsuarioManager(BaseUserManager):
    def create_user(self, nombre, apellidos, correo, password=None):
        if not nombre:
            raise ValueError("El usuario debe tener un nombre")
        if not correo:
            raise ValueError("El usuario debe tener un email")
        if not apellidos:
            raise ValueError("El usuario debe tener apellidos registrados")
        user = self.model(
            nombre=nombre,
            apellidos=apellidos,
            correo=self.normalize_email(correo),
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, nombre, apellidos, correo, password):
        user = self.create_user(nombre, apellidos, correo, password)
        user.is_staff = True
        user.is_superuser = True
        user.tipo_usuario = 'admin'
        user.save(using=self._db)
        return user
    
    def get_by_natural_key(self, correo):
        return self.get(correo=correo)

class Usuario(AbstractUser):
    username = None
    TIPO_USUARIO_CHOICES = [
        ('admin', 'Administrador'),
        ('prof', 'Profesor'),
    ]
    nombre = models.CharField(max_length=50)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    tipo_usuario = models.CharField(max_length=5, choices=TIPO_USUARIO_CHOICES)
    direccion = models.OneToOneField(Direccion, on_delete=models.SET_NULL,null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


