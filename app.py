from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3, os
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ibjp40anos_secret_2024'

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ibjp40.db')
LOGIN = 'IBJPMIDIA'
SENHA = 'Op5IBJP00'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fase TEXT NOT NULL, texto TEXT NOT NULL,
        done INTEGER DEFAULT 0, responsavel TEXT DEFAULT '',
        prioridade TEXT DEFAULT 'normal',
        criado_em TEXT DEFAULT '')''')
    # Adiciona coluna updated_at se não existir (compatibilidade)
    try:
        c.execute('ALTER TABLE tasks ADD COLUMN updated_at TEXT DEFAULT ""')
    except:
        pass
    c.execute('''CREATE TABLE IF NOT EXISTS membros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL, funcao TEXT DEFAULT '', inicial TEXT DEFAULT '')''')
    c.execute('''CREATE TABLE IF NOT EXISTS config (
        chave TEXT PRIMARY KEY, valor TEXT)''')
    c.execute('SELECT COUNT(*) FROM tasks')
    if c.fetchone()[0] == 0:
        now = datetime.now().isoformat()
        seed = [
            ('antes','Criar série de posts contagem regressiva (10 dias)',0,'Anderson','alta'),
            ('antes','Gravar depoimentos curtos (10–20s) dos membros',0,'','alta'),
            ('antes','Editar vídeo principal — trailer 1 min',0,'','alta'),
            ('antes','Publicar stories diários com bastidores',0,'','normal'),
            ('antes','Definir identidade visual padrão para posts',1,'Anderson','normal'),
            ('antes','Preparar logotipo 40 anos para uso nas redes',1,'Anderson','normal'),
            ('antes','Coletar fotos antigas da história da igreja',0,'','alta'),
            ('antes','Criar 3 cards com versículos + testemunhos',0,'','normal'),
            ('durante','Testar transmissão ao vivo (áudio + internet)',0,'','alta'),
            ('durante','Designar fotógrafo(a) para cobertura exclusiva',0,'','alta'),
            ('durante','Gravar stories ao vivo: chegada, louvor, palavra',0,'','alta'),
            ('durante','Fazer entrevistas rápidas nos corredores',0,'','normal'),
            ('durante','Transmissão no YouTube ou Instagram Live',0,'','alta'),
            ('durante','Marcar pessoas nos stories para ampliar alcance',0,'','normal'),
            ('durante','Montar espaço instagramável "40 Anos IBJP"',0,'','normal'),
            ('durante','Organizar telão com linha do tempo da igreja',0,'','normal'),
            ('depois','Editar e postar vídeo-resumo do dia (30–60s)',0,'','alta'),
            ('depois','Selecionar melhores fotos e publicar álbum',0,'','alta'),
            ('depois','Agradecer a todos nas redes sociais',0,'','normal'),
            ('depois','Publicar vídeo completo da transmissão no YouTube',0,'','normal'),
        ]
        for f,t,d,r,p in seed:
            c.execute('INSERT INTO tasks (fase,texto,done,responsavel,prioridade,criado_em,updated_at) VALUES (?,?,?,?,?,?,?)',(f,t,d,r,p,now,now))
    c.execute('SELECT COUNT(*) FROM membros')
    if c.fetchone()[0] == 0:
        for n,f,i in [('Anderson','Design & Identidade Visual','A'),('Fotógrafo(a)','Cobertura Fotográfica','F'),('Stories','Redes Sociais ao Vivo','S'),('Câmera','Vídeo & Transmissão','C')]:
            c.execute('INSERT INTO membros (nome,funcao,inicial) VALUES (?,?,?)',(n,f,i))
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    return redirect(url_for('login_page') if not session.get('logged_in') else url_for('dashboard'))

@app.route('/login', methods=['GET','POST'])
def login_page():
    error = None
    if request.method == 'POST':
        if request.form.get('usuario') == LOGIN and request.form.get('senha') == SENHA:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        error = 'Usuário ou senha incorretos.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/state')
@login_required
def get_state():
    conn = get_db()
    tasks_raw = conn.execute('SELECT * FROM tasks ORDER BY id').fetchall()
    membros_raw = conn.execute('SELECT * FROM membros ORDER BY id').fetchall()
    config_raw = conn.execute('SELECT chave,valor FROM config').fetchall()
    conn.close()
    tasks = {'antes':[],'durante':[],'depois':[]}
    for t in tasks_raw:
        tasks[t['fase']].append(dict(t))
    return jsonify({'tasks':tasks,'membros':[dict(m) for m in membros_raw],'config':{r['chave']:r['valor'] for r in config_raw}})

@app.route('/api/tasks', methods=['POST'])
@login_required
def add_task():
    data = request.json
    now = datetime.now().isoformat()
    conn = get_db()
    cur = conn.execute('INSERT INTO tasks (fase,texto,done,responsavel,prioridade,criado_em,updated_at) VALUES (?,?,0,?,?,?,?)',
        (data['fase'],data['texto'],data.get('responsavel',''),data.get('prioridade','normal'),now,now))
    conn.commit()
    task = dict(conn.execute('SELECT * FROM tasks WHERE id=?',(cur.lastrowid,)).fetchone())
    conn.close()
    return jsonify(task)

@app.route('/api/tasks/<int:tid>', methods=['PATCH'])
@login_required
def update_task(tid):
    data = request.json
    now = datetime.now().isoformat()
    conn = get_db()
    fields, vals = [], []
    for f in ['done','responsavel','prioridade','texto']:
        if f in data:
            fields.append(f'{f}=?')
            vals.append(data[f])
    if not fields:
        conn.close()
        return jsonify({'ok':True})
    vals.append(tid)
    conn.execute(f'UPDATE tasks SET {", ".join(fields)} WHERE id=?', vals)
    conn.commit()
    task = dict(conn.execute('SELECT * FROM tasks WHERE id=?',(tid,)).fetchone())
    conn.close()
    return jsonify(task)

@app.route('/api/tasks/<int:tid>', methods=['DELETE'])
@login_required
def delete_task(tid):
    conn = get_db()
    conn.execute('DELETE FROM tasks WHERE id=?',(tid,))
    conn.commit()
    conn.close()
    return jsonify({'ok':True})

@app.route('/api/tasks/fase/<fase>/done_all', methods=['POST'])
@login_required
def mark_all_done(fase):
    conn = get_db()
    conn.execute('UPDATE tasks SET done=1 WHERE fase=?',(fase,))
    conn.commit()
    conn.close()
    return jsonify({'ok':True})

@app.route('/api/membros', methods=['GET'])
@login_required
def get_membros():
    conn = get_db()
    rows = [dict(m) for m in conn.execute('SELECT * FROM membros ORDER BY id').fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/membros', methods=['POST'])
@login_required
def add_membro():
    data = request.json
    nome = data.get('nome','')
    conn = get_db()
    cur = conn.execute('INSERT INTO membros (nome,funcao,inicial) VALUES (?,?,?)',
                       (nome,data.get('funcao',''),nome[0].upper() if nome else '?'))
    conn.commit()
    m = dict(conn.execute('SELECT * FROM membros WHERE id=?',(cur.lastrowid,)).fetchone())
    conn.close()
    return jsonify(m)

@app.route('/api/membros/<int:mid>', methods=['DELETE'])
@login_required
def delete_membro(mid):
    conn = get_db()
    conn.execute('DELETE FROM membros WHERE id=?',(mid,))
    conn.commit()
    conn.close()
    return jsonify({'ok':True})

@app.route('/api/config', methods=['GET'])
@login_required
def get_config():
    conn = get_db()
    rows = conn.execute('SELECT chave,valor FROM config').fetchall()
    conn.close()
    return jsonify({r['chave']:r['valor'] for r in rows})

@app.route('/api/config', methods=['POST'])
@login_required
def set_config():
    data = request.json
    conn = get_db()
    for k,v in data.items():
        conn.execute('INSERT OR REPLACE INTO config (chave,valor) VALUES (?,?)',(k,v))
    conn.commit()
    conn.close()
    return jsonify({'ok':True})

init_db()

if __name__ == '__main__':
    app.run(debug=True)
