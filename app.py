from flask import Flask, render_template, request
from pymongo import MongoClient
import json
from datetime import datetime

app = Flask(__name__)

# Configurações do banco de dados MongoDB
mongo_uri = "mongodb+srv://dicardoso:diogo123@mestradocluster.w3th7tl.mongodb.net/caixaPreta?retryWrites=true&w=majority"
documents = []
try:
    client = MongoClient(mongo_uri, tls=True)
    db = client['temp']
    collection = db["crash"]
except Exception as e:
    print("Erro de conexão:", e)

# Registro do filtro personalizado
@app.template_filter('format_date')
def format_date(value, format='%d/%m/%Y'):
    date_obj = datetime.strptime(value, '%Y-%m-%d')
    return date_obj.strftime(format)

@app.route('/', methods=['GET', 'POST'])
def filtro():
    # dados = list(collection.aggregate([{'$limit':10}]))
    dados = collection.find()
    print([dados])
    if request.method == 'POST':
        filtro_pais = request.form.get('filtro_pais')
        filtro_tipo = request.form.get('filtro_tipo')
        filtro_de = request.form.get('filtro_de')
        filtro_ate = request.form.get('filtro_ate')
        
        resultados_filtrados = filtrar_dados(filtro_pais, filtro_tipo, filtro_de, filtro_ate)
        return render_template('index2.html', resultados=resultados_filtrados, filtro_de=filtro_de, filtro_ate=filtro_ate)

    return render_template('index2.html', resultados=dados[:1000])

def filtrar_dados(filtro_pais, filtro_tipo, filtro_de, filtro_ate):
    pipeline = [{'$limit': 1000}]
    
    # Etapa de filtro por país
    if filtro_pais != 'todos':
        pipeline.append({'$match': {'Country': filtro_pais}})
    
    # Etapa de filtro por tipo
    if filtro_tipo != 'todos':
        pipeline.append({'$match': {'InvestigationType': filtro_tipo}})
    
   # Etapa de filtro por data "de" e/ou "até"
    if filtro_de:
        pipeline.append({'$match': {'EventDate': {'$gte': filtro_de}}})
    
    if filtro_ate:
        pipeline.append({'$match': {'EventDate': {'$lte': filtro_ate}}})
    
    # Executa a consulta de agregação
    resultados = collection.aggregate(pipeline)

    return [doc for doc in resultados]

if __name__ == '__main__':
    app.run(debug=True)
