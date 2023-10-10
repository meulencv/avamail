import imaplib
import email
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

#cargamos los secrets de .env
load_dotenv()
#obtenemos la lista de apikeys de serpapi
passw = os.getenv('passw')

def buscar_correo(email_buscar):
    if email_buscar == "admin@avarobotica.es":
        return ["Acceso denegado :("]
    else:
        user = 'avaalumnos@zohomail.eu'
        password = passw 
        imap_url = 'imap.zoho.eu'


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

            return None

        con = imaplib.IMAP4_SSL(imap_url)
        con.login(user, password)
        con.select('Inbox')

        result, data = con.search(None, 'TO', email_buscar)
        
        ids = data[0].split()
        print (ids)
        resultados = []
        for num in ids[::-1][:5]:  # Recorrer en reversa para obtener los correos más recientes primero
            typ, data = con.fetch(num, '(RFC822)')
            msg_data = email.message_from_bytes(data[0][1])
            cuerpo = obtener_cuerpo(msg_data)
            subject = msg_data['Subject']
            print(subject)


            if cuerpo:
                resultados.append(cuerpo)

        # Cierra la conexión con el servidor IMAP
        con.logout()

        if resultados:
            return resultados
        else:
            return ["No se encontraron E-Mails"]
