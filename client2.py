import socket
import threading
import os
from os.path import join, dirname
from dotenv import load_dotenv

load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

HOST = os.environ.get('HOST')
PORT = int(os.environ.get('PORT'))
SEND_BYTE_LEN = 6

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
except Exception as e:
    print(e)


def input_msg(s):
    # client -> server
    while True:
        raw_data = input('>>>')
        b = bytes(b'')
        splited_data = raw_data.split(',')
        for data in splited_data:
            b += int(data).to_bytes(1, 'little')
        for i in range(SEND_BYTE_LEN - len(splited_data)):
            b += int(0).to_bytes(1, 'little')
        print('push data', b)
        s.send(b)


def handler(s):
    # servert -> client
    while True:
        try:
            data = s.recv(1024)
            print('data', data)
            _data = [data[i:i + 1] for i in range(len(data))]
            data_list = []
            for _ in _data:
                _byte = int.from_bytes(_, 'little')
                data_list.append(_byte)

            if int.from_bytes(_data[0], 'little') == 128:
                print('Bye')
                s.close()

            print('Accepted data from server is\n',
                  data, data_list)

        except KeyboardInterrupt as ke:
            print(ke)
            s.close()
            break
        except UnicodeDecodeError as ud:
            print('Accepted data from server is\n',
                  data)
            continue
        except Exception as e:
            print('receive err', e)
            break


if __name__ == '__main__':
    thread = threading.Thread(
        target=handler,
        args=(s,),
        daemon=False)
    thread.start()

    try:
        input_msg(s)
    except Exception as e:
        print(e)
        s.close()
