import os
from datetime import datetime, timezone
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])


def lambda_handler(event, context):
	accion = event.get('accion')

	if accion == 'add':
		ingrediente = event['ingrediente']
		cantidad = event.get('cantidad', '1')
		table.put_item(
			Item={
				'ingrediente': ingrediente,
				'cantidad': str(cantidad),
				'fecha_ingreso': datetime.now(timezone.utc).isoformat(),
			}
		)
		return {
			'status': 'ok',
			'mensaje': f'{ingrediente} anadido a la nevera',
		}

	if accion == 'list':
		items = table.scan().get('Items', [])
		ahora = datetime.now(timezone.utc)
		resultado = []

		for it in items:
			fecha = datetime.fromisoformat(it['fecha_ingreso'])
			dias = (ahora - fecha).days
			resultado.append(
				{
					'ingrediente': it['ingrediente'],
					'cantidad': it['cantidad'],
					'dias_en_nevera': dias,
				}
			)

		return {'status': 'ok', 'ingredientes': resultado}

	return {
		'status': 'error',
		'mensaje': 'accion no reconocida, usa add o list',
	}