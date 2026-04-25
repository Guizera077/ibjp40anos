# IBJP 40 Anos — Painel de Gestão

## Rodar localmente

```bash
pip install flask
python app.py
```
Acesse: http://localhost:5000
Login: IBJPMIDIA / Op5IBJP00

## Deploy no Render (recomendado — grátis)

1. Crie conta em render.com
2. New > Web Service > conecte o GitHub
3. Build Command: `pip install flask`
4. Start Command: `gunicorn app:app`
5. Pronto!

## Deploy no Railway

1. railway.app > New Project > Deploy from GitHub
2. Ele detecta Flask automaticamente
3. Pronto!

## Estrutura
```
ibjp40/
├── app.py           # backend Flask
├── requirements.txt
└── templates/
    ├── login.html
    └── dashboard.html
```
