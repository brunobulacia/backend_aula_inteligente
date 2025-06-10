import firebase_admin
from firebase_admin import credentials, messaging
import os

# Ruta absoluta al archivo JSON en la raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
cred_path = os.path.join(BASE_DIR, 'notificaciones-push-30569-firebase-adminsdk-fbsvc-e6de9410fa.json')

# Solo inicializamos una vez
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

def enviar_notificacion_push(token, titulo, cuerpo):
    try:
        mensaje = messaging.Message(
            notification=messaging.Notification(
                title=titulo,
                body=cuerpo,
            ),
            token=token,
        )
        respuesta = messaging.send(mensaje)
        print("✅ Notificación enviada:", respuesta)
        return True
    except Exception as e:
        print("❌ Error al enviar notificación:", e)
        return False
