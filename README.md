# BACKEND AULA INTELIGENTE

Pasos para no inicializar bien el proyecto:

1. Clonar el proyecto

2. Abrir la consola en vs code y fijarte si tenes instalado el entorno virtual
   con el siguiente comando: pip install virtualenv

3. Una vez instalado dentro de esa misma ruta o la ruta principal del proyecto
   crear el entorno virtual con: python -m venv venv

4. Creado el entorno virtual, ingresar y ejecutar: .\venv\Scripts\Activate.ps1

5. Una vez dentro del entorno virtual te deberia salir con "(venv)" la terminal

6. Si se cumple el paso 5 entonces ejecutar: pip install -r requirements.txt

## IMPORTANTE

Siempre que se instales nuevas dependencias al proyecto ejecutar:
pip freeze > requirements.txt
