from flask import Flask, render_template, redirect, request, url_for, make_response
from mail import buscar_correo

app = Flask(__name__)

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
        texto = request.form.get('texto')
        return redirect(url_for('buscar', contenido=texto))
    return render_template('index.html')

@app.route('/buscar/<contenido>')
def buscar(contenido):
    resultado = buscar_correo(contenido)
    return render_template('resultado.html', resultado=resultado)

if __name__ == '__main__':
    app.run()
