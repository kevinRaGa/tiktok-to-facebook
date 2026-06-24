============================================================
 TikTok -> Facebook Auto-Poster
 Instrucciones en Español
============================================================

¿QUÉ HACE ESTE PROGRAMA?
------------------------
Descarga tus videos de TikTok UNO POR UNO y los sube
automáticamente a tu página de Facebook.
Cada 15 minutos el programa revisa si ya pasó el tiempo
que elegiste, y si es hora, sube un video nuevo.

No necesitas tener todos los videos descargados -
los descarga y los borra al instante.

Los videos se publican en orden del más antiguo al más
nuevo (primero tus primeros TikTok).

Nota: El programa revisa cada 15 minutos, pero solo
PUBLICA según el intervalo que elijas en "post_interval_hours".
Por ejemplo: si pones 24, publica 1 vez al día, pero
revisa cada 15 minutos para ver si ya es hora.

============================================================
REQUISITOS
============================================================

Antes de empezar, instala esto en tu PC:

1. Python: https://python.org (marca "Add to PATH")
2. ffmpeg: abre PowerShell y escribe:
     winget install ffmpeg
   O descarga desde: https://ffmpeg.org

============================================================
PASO 1: CONFIGURAR (solo la primera vez)
============================================================

Si descargaste de GitHub, primero copia "config.example.json"
y renómbralo a "config.json".

Abre el archivo "config.json" con Bloc de Notas.
Verás algo como esto:

{
  "tiktok_username": "@usuario_de_tiktok",
  "facebook_page_id": "ID_DE_TU_PAGINA",
  "facebook_access_token": "TOKEN_DE_ACCESO_DE_FACEBOOK",
  "post_interval_hours": 24,
  "start_from_video_id": null
}

CAMBIA estos valores:
- "tiktok_username" -> tu usuario de TikTok (ej: "@anaperez")
- "facebook_page_id" -> el ID de tu página de Facebook
- "facebook_access_token" -> el token de acceso (ver Paso 2)
- "post_interval_hours" -> cada cuántas horas subir un video
     * 24 = 1 video por día
     * 12 = 2 videos por día (cada 12 horas)
     * 6 = 4 videos por día (cada 6 horas)
     * 48 = 1 video cada 2 días
- "start_from_video_id" -> (opcional) ID del video por donde empezar
     * Pon el ID (ej: "7376360326297652485") y el programa
       saltará todos los videos anteriores y empezará desde ahí
     * Después de publicar ese video, cámbialo a "null"
       para que continúe con el siguiente video

Guarda el archivo (Ctrl+S).

============================================================
PASO 2: OBTENER EL TOKEN DE FACEBOOK
============================================================

Necesitas un TOKEN DE PÁGINA (no un token de usuario).

1. Ve a https://developers.facebook.com/
2. Inicia sesión con tu cuenta de Facebook
3. Crea una "App" -> elige "Business" o "Ninguna"
4. Ve a "Herramientas" -> "Graph API Explorer"
5. Selecciona tu app
6. En "Permisos", agrega:
   - pages_manage_posts
   - pages_read_engagement
   - pages_show_list
7. Haz clic en "Generate Access Token"
8. Copia el token que aparece (empieza con EAA...)
9. Pégalo en config.json en "facebook_access_token"

Para verificar que el token funciona:
  https://graph.facebook.com/me/accounts?access_token=TU_TOKEN

El token expira cada 60 días. Cuando deje de funcionar,
repite este paso.

============================================================
PASO 3: ENCONTRAR EL ID DE TU PÁGINA
============================================================

1. Ve a tu página de Facebook
2. En la URL verás algo como:
   facebook.com/profile.php?id=123456789
   o
   facebook.com/MiPagina
3. Si ves "MiPagina", usa esta web:
   https://graph.facebook.com/MiPagina?access_token=TU_TOKEN
4. Copia el número y pégalo en config.json

============================================================
PASO 4: EJECUTAR
============================================================

Una sola vez (la primera):

1. Abre PowerShell como Administrador
   (clic derecho -> "Ejecutar como administrador")
2. Navega a la carpeta:
   cd C:\tiktok\tiktok-automation
3. Ejecuta el setup:
   .\setup.ps1
4. ¡Listo! Ya está programado (revisa cada 15 minutos).

Después de eso, el programa se ejecuta SOLO cada 15
minutos. No tienes que hacer nada más.

============================================================
PROBAR MANUALMENTE
============================================================

Antes de esperar la tarea automática, prueba que todo
funciona abriendo PowerShell (NO como administrador) y
escribe:

  cd C:\tiktok\tiktok-automation
  python tiktok_poster.py

Si ves mensajes de error, revisa que config.json tenga
los valores correctos.

============================================================
CÓMO CAMBIAR LA FRECUENCIA
============================================================

- Abre config.json con Bloc de Notas
- Cambia "post_interval_hours" al número que quieras
- Guarda el archivo (Ctrl+S)
- El cambio se aplica automáticamente en los próximos 15
  minutos (cuando el programa vuelva a revisar)

Ejemplos:
  24 = cada 24 horas (1 video al día)
  12 = cada 12 horas (2 videos al día)
  6  = cada 6 horas (4 videos al día)
  48 = cada 48 horas (1 video cada 2 días)

IMPORTANTE: El programa revisa si debe publicar cada 15
minutos, pero solo PUBLICA según el número de horas que
elijas arriba. Si pones 24, solo publicará 1 vez al día
(aunque revise cada 15 minutos).

============================================================
VER LISTA DE VIDEOS
============================================================

Para ver todos los videos de TikTok con su ID (número):

  cd C:\tiktok\tiktok-automation
  python tiktok_poster.py --list-videos

Esto muestra algo como:

   1. 7083323128964779269  Título del video...
   2. 7376360326297652485  Otro título...
   ...
 628. 7653237413648567559  Último video...

Los videos más antiguos aparecen primero.

============================================================
EMPEZAR DESDE UN VIDEO ESPECÍFICO
============================================================

Si quieres empezar a publicar desde un video en específico
(saltándote los más antiguos):

1. Corre python tiktok_poster.py --list-videos para ver
   los IDs de los videos
2. Encuentra el ID del video por donde quieres empezar
3. Abre config.json y cambia:
     "start_from_video_id": "ID_DEL_VIDEO"
   Ejemplo:
     "start_from_video_id": "7376360326297652485"
4. Guarda y corre python tiktok_poster.py
5. El programa publicará ese video y los siguientes
6. Después de la primera publicación, abre config.json
   y cámbialo de vuelta a:
     "start_from_video_id": null
   Para que continúe normalmente con el siguiente video.

============================================================
REVISAR EL REGISTRO (LOG)
============================================================

Cada vez que el programa se ejecuta, escribe en el archivo
"poster.log" lo que hizo. Puedes abrirlo con Bloc de Notas
para ver:

  2026-06-22 14:47:02  START
  2026-06-22 14:47:03  Using cached video list (628 videos)
  2026-06-22 14:47:03  Next post in 23.9h. Nothing to do.
  2026-06-22 14:47:03  DONE  (duration: 1s)

O cuando publica:

  2026-06-22 14:47:02  START
  2026-06-22 14:47:05  Fetched 628 videos
  2026-06-22 14:47:06  DL    7632121713089711367  Título...
  2026-06-22 14:48:30  UP    7632121713089711367
  2026-06-22 14:48:31  POST  7632121713089711367  (took 89s)
  2026-06-22 14:48:31  DONE  (duration: 89s)

Si algo sale mal, revisa este archivo primero.

============================================================
CÓMO VER QUÉ ESTÁ PASANDO
============================================================

Abre PowerShell (como administrador) y corre:
  Get-ScheduledTask -TaskName TikTokFacebookPoster

Para ver el historial de ejecución:
  Get-ScheduledTask -TaskName TikTokFacebookPoster | Get-ScheduledTaskInfo

============================================================
CÓMO DETENER EL PROGRAMA
============================================================

Abre PowerShell como administrador:
  Unregister-ScheduledTask -TaskName TikTokFacebookPoster -Confirm:$false

Para volver a activarlo, corre setup.ps1 de nuevo.

============================================================
¡Eso es todo!
============================================================
