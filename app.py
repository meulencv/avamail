from flask import Flask, render_template, redirect, request, url_for, make_response, session, flash
from mail import buscar_correo, es_email_restringido, normalizar_email
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'ava_robotica_educativa_2025_secret_key')
app.permanent_session_lifetime = timedelta(hours=24)

# Contraseña para cuentas restringidas
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'AvaRobotica2025!')

@app.after_request
def add_header(response):
    """
    Agrega las cabeceras de no almacenamiento en caché a todas las respuestas HTTP.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Cache-Control"] = "public, max-age=0"
    return response

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        entrada_usuario = request.form.get('texto', '').strip()
        tipo_cuenta = request.form.get('tipo_cuenta', 'estudiante').strip()
        
        if not entrada_usuario:
            flash('Por favor, introduce tu nombre de usuario o email.', 'error')
            return render_template('index.html')
        
        # Normalizar el email según el tipo de cuenta
        if tipo_cuenta == 'profesor':
            # Para profesores, usar el formato admin
            if '@' not in entrada_usuario:
                email_completo = f"{entrada_usuario}@avarobotica.es"
            else:
                email_completo = entrada_usuario
        else:
            # Para estudiantes, usar el formato normal
            email_completo = normalizar_email(entrada_usuario)
        
        # Verificar si es un email restringido
        if es_email_restringido(email_completo):
            # Verificar si ya está autenticado
            if session.get('authenticated') and session.get('email') == email_completo:
                return redirect(url_for('buscar', contenido=email_completo))
            else:
                # Redirigir a la página de autenticación
                return render_template('auth.html', email=email_completo, nombre_usuario=entrada_usuario)
        else:
            # Email no restringido, acceso directo
            return redirect(url_for('buscar', contenido=email_completo))
    
    return render_template('index.html')

@app.route('/auth', methods=['POST'])
def auth():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    
    if not email or not password:
        return render_template('auth.html', email=email, error='Email y contraseña son requeridos.')
    
    # Verificar contraseña
    if password == ADMIN_PASSWORD:
        # Autenticación exitosa
        session.permanent = True
        session['authenticated'] = True
        session['email'] = email
        session['auth_time'] = datetime.now().isoformat()
        
        flash(f'Acceso autorizado para {email}', 'success')
        return redirect(url_for('buscar', contenido=email))
    else:
        # Contraseña incorrecta
        return render_template('auth.html', email=email, error='Contraseña incorrecta. Acceso denegado.')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('index'))

@app.route('/buscar/<contenido>')
def buscar(contenido):
    # Verificar acceso para emails restringidos
    if es_email_restringido(contenido):
        if not (session.get('authenticated') and session.get('email') == contenido):
            flash('Acceso denegado. Debes autenticarte primero.', 'error')
            return redirect(url_for('index'))
    
    resultado = buscar_correo(contenido)
    return render_template('resultado.html', resultado=resultado, email=contenido)

if __name__ == '__main__':
    app.run()
