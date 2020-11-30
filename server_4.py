import socket
import threading
import sys
import random
import copy
import time

HOST = '127.0.0.1'
PORT = 50003
SEND_BYTE_LEN = 6
CLIENTS = 5
SUCCESS_TARGET_CNT = 3
FAILURE_TARGET_CNT = 3
clients_list = []
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s_target_list = []
f_target_list = []

point_map = {}

plus_twenty = False

start_flg = False


def remove_conection(con, address):
    print('[切断]{}'.format(address))
    con.close()
    clients_list.remove((con, address))


def init_dataset():
    for i in range(SUCCESS_TARGET_CNT):
        while True:
            num = random.randint(0, 100)
            if num not in s_target_list:
                break
        s_target_list.append(num)
        s_target_list.append(1)

    for i in range(FAILURE_TARGET_CNT):
        while True:
            num = random.randint(0, 100)
            if (num not in s_target_list) and (num not in f_target_list):
                break
        f_target_list.append(num)


def start_server():
    # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(CLIENTS)
    print("Server is listening at {}:{}".format(HOST, PORT))

    while True:
        if start_flg:
            print('Game Start!')
            break
        else:
            print('Game not start')
            time.sleep(1)

    init_dataset()
    print('あたり/ハズレ', s_target_list, f_target_list)
    while True:
        try:
            con, address = sock.accept()
            print("[接続]{}".format(address))
            clients_list.append((con, address))
            point_map[address[1]] = 0

            threading.Thread(target=receive_handler,
                             args=(con, address),
                             daemon=False).start()

        except Exception as e:
            print('start_server() err', e)
            con.close()


def push_handler():
    # server -> client
    global plus_twenty, start_flg
    raw_data = input('>>>')
    b = bytes(b'')

    data = raw_data.split(',')
    data.append(0)
    if int(data[0]) == 0:  # game start
        print('Game Start')
        start_flg = True
        for c in clients_list:
            send_result(c, 0)
    elif int(data[0]) == 128:  # game over
        print('Game Over')
        # return result to all clients
        for c in clients_list:
            send_result(c, 128)
    elif int(data[0]) == 1:  # judge point
        print('Judge')
        for c in clients_list:
            send_result(c, 1)
    else:
        if int(data[1]) == 255:  # additional function
            plus_twenty = not plus_twenty
            print('拡張機能', 'ON' if plus_twenty else 'OFF')

        splited_data = raw_data.split(',')
        for data in raw_data.split(','):
            b += int(data).to_bytes(1, 'little')
        for i in range(SEND_BYTE_LEN - len(splited_data)):
            b += int(0).to_bytes(1, 'little')
        print('push data', b)
        for c in clients_list:
            c[0].sendto(b, c[1])


def receive_handler(con, address):
    # client -> server
    while True:
        try:
            data = con.recv(1024)
            _data = [data[i:i + 1] for i in range(len(data))]
            data_list = []
            for _ in _data:
                _byte = int.from_bytes(_, 'little')
                data_list.append(_byte)

            judge_point(data_list, address)

            print("[R]{} - {}".format(address, data))

            for c in clients_list:  # send result to client
                send_result(c, 1)
        except ConnectionResetError:
            print('Connection Err')
            remove_conection(con, address)
            break
        except Exception as e:
            print('Receive err', e)
            break
        else:
            if not data:
                print('Not data')
                remove_conection(con, address)
                break


def double_point(data_list, address):  # custom function
    if data_list[1] == 255:
        point_map[address] = point_map[address] * 2
        return


def judge_point(data_list, address):
    global s_target_list, f_target_list, plus_twenty
    address = address[1]

    # additional function
    if plus_twenty:
        point_map[address] = point_map[address] + 20
        plus_twenty = False
    double_point(data_list, address)

    if data_list[0] in s_target_list:
        if point_map[address] <= 245:
            point_map[address] = point_map[address] + 10

        s_target_list.remove(data_list[0])
        return

    if data_list[0] in f_target_list:
        if point_map[address] >= 10:
            point_map[address] = point_map[address] - 10

        f_target_list.remove(data_list[0])
        return

    if point_map[address] > 0:
        point_map[address] = point_map[address] - 1


def send_result(c, b):
    msg = b''
    msg += int(b).to_bytes(1, 'little')

    _p_map = copy.copy(point_map)

    me = _p_map.pop(c[1][1])
    msg += int(me).to_bytes(1, 'little')

    point_list = list(_p_map.values())
    for i in range(len(point_list)):
        msg += int(point_list[i]).to_bytes(1, 'little')

    for i in range(SEND_BYTE_LEN - 2 - len(point_list)):
        msg += int(0).to_bytes(1, 'little')

    c[0].sendto(msg, c[1])


if __name__ == "__main__":
    threading.Thread(target=start_server,
                     daemon=True).start()
    try:
        while True:
            push_handler()
    except Exception as e:
        print('push_handler() err', e)
