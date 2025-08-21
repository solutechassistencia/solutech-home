from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash
import sqlite3
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)
app.secret_key = 'segredo_solutech'

DB_NAME = 'database.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ordens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente TEXT,
                    servico TEXT,
                    valor REAL,
                    status TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )''')
    # usuário admin padrão
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ("admin", "admin"))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM ordens")
    ordens = c.fetchall()
    conn.close()
    return render_template('index.html', ordens=ordens)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user'] = username
            return redirect(url_for('index'))
        else:
            flash("Usuário ou senha inválidos")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/add', methods=['GET','POST'])
def add():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        cliente = request.form['cliente']
        servico = request.form['servico']
        valor = request.form['valor']
        status = request.form['status']
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO ordens (cliente, servico, valor, status) VALUES (?,?,?,?)",
                  (cliente, servico, valor, status))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/edit/<int:ordem_id>', methods=['GET','POST'])
def edit(ordem_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if request.method == 'POST':
        cliente = request.form['cliente']
        servico = request.form['servico']
        valor = request.form['valor']
        status = request.form['status']
        c.execute("UPDATE ordens SET cliente=?, servico=?, valor=?, status=? WHERE id=?",
                  (cliente, servico, valor, status, ordem_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    else:
        c.execute("SELECT * FROM ordens WHERE id=?", (ordem_id,))
        ordem = c.fetchone()
        conn.close()
        return render_template('edit.html', ordem=ordem)

@app.route('/delete/<int:ordem_id>')
def delete(ordem_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM ordens WHERE id=?", (ordem_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/pdf/<int:ordem_id>')
def gerar_pdf(ordem_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM ordens WHERE id=?", (ordem_id,))
    ordem = c.fetchone()
    conn.close()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Cabeçalho da empresa
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, height - 20, "SOLUTECH HOME – Assistência Técnica")
    p.setFont("Helvetica", 8)
    p.drawString(300, height - 20, "CNPJ 47.062.189/0001-00")
    p.drawString(40, height - 32, "Av. Das Monções, 1144 - Mogi das Cruzes - SP")
    p.drawString(300, height - 32, "Tel: (11) 96451-8003 / (11) 96302-6488 / (11) 98151-2129")

    # Dados da OS
    p.setFont("Helvetica", 10)
    y = height - 80
    p.drawString(40, y, f"Ordem de Serviço Nº {ordem[0]}")
    p.drawString(40, y-20, f"Cliente: {ordem[1]}")
    p.drawString(40, y-40, f"Serviço: {ordem[2]}")
    p.drawString(40, y-60, f"Valor: R$ {ordem[3]}")
    p.drawString(40, y-80, f"Status: {ordem[4]}")

    # Assinaturas
    y = 120
    p.line(60, y, 250, y)
    p.drawString(100, y-12, "Assinatura do Cliente")
    p.line(320, y, 510, y)
    p.drawString(360, y-12, "Assinatura do Técnico")

    p.showPage()
    p.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name=f'ordem_{ordem_id}.pdf',
                     mimetype='application/pdf')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
