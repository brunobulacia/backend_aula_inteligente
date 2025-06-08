from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import Usuario, Direccion



class DireccionSerializer(serializers.ModelSerializer):
    departamento = serializers.CharField(source='departamento.nombre', read_only=True)
    class Meta: 
        model = Direccion
        fields = '__all__'  
        read_only_fields = ['id']  


class UsuarioSerializer(serializers.ModelSerializer):
    direccion = DireccionSerializer() 
    class Meta:
        model = Usuario
        fields = ['id','nombre', 'apellidos', 'email', 'tipo_usuario', 'password', 'direccion']
        extra_kwargs = {
            'password': {'write_only': True},
        }
    def create(self, validated_data):
        direccion_data = validated_data.pop('direccion')
        direccion = Direccion.objects.create(**direccion_data)

        password = validated_data.pop('password', None)
        validated_data['direccion'] = direccion

        user = Usuario(**validated_data)

        if password:
            user.set_password(password)

        if user.tipo_usuario == 'admin':
            user.is_staff = True
            user.is_superuser = True

        user.save()
        return user


    def validate_email(self, value):
        user = getattr(self, 'instance', None)
        if Usuario.objects.exclude(pk=getattr(user, 'pk', None)).filter(email=value).exists():
            raise serializers.ValidationError("Ese correo ya está registrado.")
        return value
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.password = make_password(password)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance