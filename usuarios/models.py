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
    def create_user(self, nombre, apellidos, email, password=None, **extra_fields):
        if not nombre:
            raise ValueError("El usuario debe tener un nombre")
        if not email:
            raise ValueError("El usuario debe tener un email")
        if not apellidos:
            raise ValueError("El usuario debe tener apellidos registrados")
        user = self.model(
            nombre=nombre,
            apellidos=apellidos,
            email=self.normalize_email(email),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, nombre, apellidos, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('tipo_usuario', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')

        return self.create_user(nombre, apellidos, email, password, **extra_fields)
    
    def get_by_natural_key(self, email):
        return self.get(email=email)

class Usuario(AbstractUser):
    username = None
    TIPO_USUARIO_CHOICES = [
        ('admin', 'Administrador'),
        ('prof', 'Profesor'),
        ('alum', 'Alumno'),
    ]
    nombre = models.CharField(max_length=50)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    tipo_usuario = models.CharField(max_length=5, choices=TIPO_USUARIO_CHOICES)
    direccion = models.OneToOneField(Direccion, on_delete=models.SET_NULL,null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellidos']
    objects = UsuarioManager()

    def __str__(self):
        return self.email


