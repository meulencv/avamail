import imaplib
import email
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import re

#cargamos los secrets de .env
load_dotenv()
#obtenemos la lista de apikeys de serpapi
passw = os.getenv('passw')

def normalizar_email(entrada_usuario):
    """
    Normaliza la entrada del usuario para convertirla en un email completo.
    Si no contiene @, asume que es un nombre de usuario y agrega el dominio.
    """
    entrada_usuario = entrada_usuario.strip().lower()
    
    # Si ya contiene @, devolverlo tal como está
    if '@' in entrada_usuario:
        return entrada_usuario
    
    # Si no contiene @, construir el email
    # Si no termina en .estudiante, agregarlo automáticamente para estudiantes
    if not entrada_usuario.endswith('.estudiante'):
        # Verificar si es un nombre de cuenta especial (admin, info, etc.)
        cuentas_especiales = ['admin', 'info', 'soporte', 'contacto', 'ventas', 'marketing', 'profesor', 'director']
        if entrada_usuario in cuentas_especiales:
            return f"{entrada_usuario}@avarobotica.es"
        else:
            # Para nombres normales, agregar .estudiante automáticamente
            return f"{entrada_usuario}.estudiante@avarobotica.es"
    else:
        # Ya tiene .estudiante, solo agregar el dominio
        return f"{entrada_usuario}@avarobotica.es"

def es_email_restringido(email):
    """
    Determina si un email es restringido según las reglas:
    - Los emails que terminan en .estudiante NO son restringidos
    - Todos los demás emails de @avarobotica.es SÍ son restringidos
    - Emails especiales como admin, info, soporte, etc. siempre son restringidos
    """
    if not email or '@' not in email:
        return True
    
    email = email.lower().strip()
    
    # Emails especiales siempre restringidos
    emails_especiales = [
        'admin@avarobotica.es',
        'info@avarobotica.es',
        'soporte@avarobotica.es',
        'contacto@avarobotica.es',
        'ventas@avarobotica.es',
        'marketing@avarobotica.es',
        'profesor@avarobotica.es',
        'director@avarobotica.es'
    ]
    
    if email in emails_especiales:
        return True
    
    # Si el email no es de @avarobotica.es, considerarlo restringido por seguridad
    if not email.endswith('@avarobotica.es'):
        return True
    
    # Extraer la parte local del email (antes del @)
    parte_local = email.split('@')[0]
    
    # Si termina en .estudiante, NO es restringido
    if parte_local.endswith('.estudiante'):
        return False
    
    # Todos los demás emails de @avarobotica.es son restringidos
    return True

def extraer_texto_plano(html_content):
    """
    Extrae texto plano de contenido HTML para mostrar como snippet.
    """
    if not html_content:
        return ""
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remover scripts y estilos
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Obtener texto plano
        texto = soup.get_text()
        # Limpiar espacios en blanco excesivos
        lineas = (linea.strip() for linea in texto.splitlines())
        parrafos = (frase.strip() for linea in lineas for frase in linea.split("  "))
        texto_limpio = ' '.join(parrafo for parrafo in parrafos if parrafo)
        
        # Limitar a 150 caracteres para el snippet
        return texto_limpio[:150] + "..." if len(texto_limpio) > 150 else texto_limpio
    except:
        return "Sin contenido disponible"

def buscar_correo(email_buscar):
    """
    Busca correos para el email especificado.
    La verificación de restricciones se hace en app.py, aquí solo procesamos la búsqueda.
    """
    if not email_buscar or '@' not in email_buscar:
        return [{"error": "Email inválido"}]
    
    user = 'footytictactoe@yahoo.com'
    password = passw 
    imap_url = 'imap.mail.yahoo.com'
    
    if not password:
        return [{"error": "Error de configuración: No se pudo obtener la contraseña del servidor de correo"}]
    def obtener_cuerpo(msg):
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/html':
                    charset = part.get_content_charset()
                    cuerpo = part.get_payload(decode=True)
                    if charset:
                        cuerpo = cuerpo.decode(charset)
                    return cuerpo
        else:
            content_type = msg.get_content_type()
            if content_type == 'text/html':
                charset = msg.get_content_charset()
                cuerpo = msg.get_payload(decode=True)
                if charset:
                    cuerpo = cuerpo.decode(charset)
                return cuerpo

        # Si no se encontró contenido HTML, buscar contenido de tipo text/plain
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    charset = part.get_content_charset()
                    cuerpo = part.get_payload(decode=True)
                    if charset:
                        cuerpo = cuerpo.decode(charset)
                    return cuerpo
        else:
            content_type = msg.get_content_type()
            if content_type == 'text/plain':
                charset = msg.get_content_charset()
                cuerpo = msg.get_payload(decode=True)
                if charset:
                    cuerpo = cuerpo.decode(charset)
                return cuerpo

        return None

    try:
        con = imaplib.IMAP4_SSL(imap_url)
        con.login(user, password)
        con.select('Inbox')

        result, data = con.search(None, 'TO', email_buscar)
        
        ids = data[0].split()
        print(f"Encontrados {len(ids)} correos para {email_buscar}")
        
        resultados = []
        for num in ids[::-1][:5]:  # Recorrer en reversa para obtener los correos más recientes primero
            typ, data = con.fetch(num, '(RFC822)')
            msg_data = email.message_from_bytes(data[0][1])
            cuerpo = obtener_cuerpo(msg_data)
            
            # Extraer información del email
            subject = msg_data.get('Subject', 'Sin asunto')
            from_addr = msg_data.get('From', 'Remitente desconocido')
            date = msg_data.get('Date', '')
            
            # Decodificar subject si está codificado
            if subject and subject.startswith('=?'):
                try:
                    subject = email.header.decode_header(subject)[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode('utf-8')
                except:
                    pass
            
            # Extraer nombre del remitente (quitar email)
            sender_name = from_addr
            if '<' in from_addr:
                sender_name = from_addr.split('<')[0].strip().replace('"', '')
            
            # Crear snippet del contenido
            snippet = extraer_texto_plano(cuerpo) if cuerpo else "Sin contenido"
            
            print(f"Procesando correo: {subject}")

            email_data = {
                'subject': subject or 'Sin asunto',
                'sender': sender_name or 'Remitente desconocido',
                'date': date,
                'snippet': snippet,
                'content': cuerpo or 'Sin contenido disponible'
            }
            
            resultados.append(email_data)

        # Cierra la conexión con el servidor IMAP
        con.logout()

        if resultados:
            return resultados
        else:
            return [{"error": f"No se encontraron emails para {email_buscar}"}]
            
    except Exception as e:
        print(f"Error al buscar correos: {str(e)}")
        return [{"error": f"Error al conectar con el servidor de correo: {str(e)}"}]
