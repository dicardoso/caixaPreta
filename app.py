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
    event = db["crash"]
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
    paises = listar_paises()
    filtro_pais = request.form.get('filtro_pais')
    filtro_tipo = request.form.get('filtro_tipo')
    filtro_de = request.form.get('filtro_de')
    filtro_ate = request.form.get('filtro_ate')
    filtro_limite = request.form.get('filtro_limite')
    if filtro_limite is None:
        filtro_limite = 1000
        
    resultados_filtrados = filtrar_dados(filtro_pais, filtro_tipo, filtro_de, filtro_ate, filtro_limite)

    return render_template('index.html', resultados=resultados_filtrados, 
        filtro_pais=filtro_pais, filtro_tipo=filtro_tipo, filtro_de=filtro_de, 
        filtro_ate=filtro_ate, paises=paises, limite_default=filtro_limite, total=len(resultados_filtrados))

    return render_template('index.html', paises=paises)

def filtrar_dados(filtro_pais, filtro_tipo, filtro_de, filtro_ate, filtro_limite=1000):
    pipeline = []

    if filtro_pais != 'todos' and filtro_pais != None:
        pipeline.append({'$match': {'Country': filtro_pais}})

    if filtro_tipo != 'todos' and filtro_pais != None:
        pipeline.append({'$match': {'InvestigationType': filtro_tipo}})

    if filtro_de:
        pipeline.append({'$match': {'EventDate': {'$gte': filtro_de}}})

    if filtro_ate:
        pipeline.append({'$match': {'EventDate': {'$lte': filtro_ate}}})

    # Etapa de $lookup com a coleção Injury
    # pipeline.append({
    #     '$lookup': {
    #         'from': 'injury',
    #         'localField': 'EventCode',
    #         'foreignField': 'EventCode',
    #         'as': 'injury_details',
    #     }
    # })

    pipeline.append({'$limit': int(filtro_limite)})

    resultados = event.aggregate(pipeline)

    return [doc for doc in resultados]

if __name__ == '__main__':
    app.run(port=8080, debug=True)
