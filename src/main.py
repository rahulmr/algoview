import trading.main as tradelib
import pika  # client module for rabbit_mq
import os
import json
import time
cwd = os.getcwd()
print(cwd)
if cwd.find('src') != len(cwd)-3:
    if cwd.find('algoview') == len(cwd)-8:
        os.chdir(cwd + '/src')
    elif len(cwd) > cwd.find('src')+3:
        os.chdir(cwd[:cwd.find('src')+3])
    else:
        print('Warning: cannot resolve path')


# function called when receiving a message from amqp

# TODO: cancel message execution if received more than 30 seconds before


def callback(ch, method, properties, body):
    order_message = decode_message(body)['value']
    underlying = order_message['underlying'].strip()
    msg = order_message['description'].strip()

    # We get a dictionnary out of executing message
    output = tradelib.execute_message(underlying, msg)

    # we merge both dictionaries
    order_message = {**order_message, **output}
    order_message['status'] = 'executed'
    ch.basic_publish(exchange='',
                     routing_key='executed_signals',
                     body=json.dumps(order_message))
    # Main function listener


def decode_message(body):
    message_received = json.loads(json.loads(body.decode('utf-8')))

    if isinstance(message_received, dict) and 'underlying' in message_received and 'description' in message_received:
        return {'valid': 1,
                'value': message_received}
    else:
        return {'valid': 0, 'value': message_received}


def Main(basic_get=False):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))

    channel = connection.channel()
    if not basic_get:
        try:
            channel.queue_purge(queue='hello')
            channel.queue_purge(queue='executed_signals')
        except Exception:
            pass
        channel.queue_declare(queue='hello')
        channel.queue_declare(queue='executed_signals')
        channel.basic_consume(callback,
                              queue='hello',
                              no_ack=True)
        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()
    else:
        method_frame, header_frame, body = channel.basic_get('hello')
        order_message = decode_message(body)['value']
        underlying = order_message['underlying'].strip()
        msg = order_message['description'].strip()

        # We get a dictionnary out of executing message
        output = tradelib.execute_message(underlying, msg)
        # we merge both dictionaries
        order_message = {**order_message, **output}

        print(order_message)
        channel.basic_publish(exchange='',
                              routing_key='executed_signals',
                              body=json.dumps(order_message))


if __name__ == "__main__":
    Main(basic_get=False)
