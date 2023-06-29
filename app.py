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
    db = client['airplaneCrash']
    event = db["event"]
except Exception as e:
    print("Erro de conexão:", e)

# Registro do filtro personalizado
@app.template_filter('format_date')
def format_date(value, format='%d/%m/%Y'):
    date_obj = datetime.strptime(value, '%Y-%m-%d')
    return date_obj.strftime(format)

def listar_paises():
    return list(event.aggregate([
            {
                '$group': {
                    '_id': '$Country'
                }
            },
            {
                '$match': {
                    '_id': {
                        '$ne': None
                    }
                }
            },
            {
                '$sort': {
                    '_id': 1
                }
            }
        ]))

@app.route('/dash', methods=['GET', 'POST'])
def dash():
    return render_template('chart.html')

@app.route('/', methods=['GET', 'POST'])
def filtro():
    if request.method == 'POST':
        filtro_pais = request.form.get('filtro_pais')
        filtro_tipo = request.form.get('filtro_tipo')
        filtro_de = request.form.get('filtro_de')
        filtro_ate = request.form.get('filtro_ate')
        
        resultados_filtrados = filtrar_dados(filtro_pais, filtro_tipo, filtro_de, filtro_ate)

        # Consulta ao MongoDB para obter a lista de países
        paises = listar_paises()

        return render_template('index.html', resultados=resultados_filtrados, filtro_pais=filtro_pais, filtro_tipo=filtro_tipo, filtro_de=filtro_de, filtro_ate=filtro_ate, paises=paises)

    return render_template('index.html')

def filtrar_dados(filtro_pais, filtro_tipo, filtro_de, filtro_ate):
    pipeline = []

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

    # Etapa de $lookup com a coleção Injury
    pipeline.append({
        '$lookup': {
            'from': 'injury',
            'localField': 'EventCode',
            'foreignField': 'EventCode',
            'as': 'injury_details'
        }
    })

    # Etapa de limite de documentos
    pipeline.append({'$limit': 7000})

    # Executa a consulta de agregação
    resultados = event.aggregate(pipeline)

    return [doc for doc in resultados]

if __name__ == '__main__':
    app.run(debug=True)
