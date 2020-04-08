#
# Серверное приложение для соединений
#
import asyncio
import sys
import time
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    login_list: list = []
    message_history: list = []
    server: 'Server'                                    # одинарные кавычки для обращения к классу/типу класса до его объявления
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")
                if self.login in self.login_list:
                    self.transport.write(f"Логин {self.login} уже занят, попробуйте другой\r\n".encode())
                    time.sleep(2)
                    self.transport.close()
                    print("user disconnected due to incorrect login")
                else:
                    self.login_list.append(self.login)
                    self.send_history(self)
                    self.transport.write(f"Привет, {self.login}!\r\n".encode())
            else:
                self.transport.write("Неправильный логин\r\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        self.transport.write(f"Для подключения введите логин в виде login:username\r\nC нами {self.login_list}\r\n".encode())
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        self.login_list.remove(self.login)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        self.message_history.append(message)
        for user in self.server.clients:
            user.transport.write(message.encode())

    def send_history(self, message_history: list):
        for _ in self.message_history[-10:]:
            self.transport.write(f"{_}".encode())


class Server:
    clients: list

    def __init__(self):
        self.clients = []

    def build_protocol(self):
        return ServerProtocol(self)                     # объект класса серверПротокол создается на основе текущего подключения

    async def start(self):
        loop = asyncio.get_running_loop()               # работает постоянно

        coroutine = await loop.create_server(           # await - асинхронная функция?. при асинхроне
            self.build_protocol,                        # конструктор протокола
            '127.0.0.1',            # ip адрес
            8888                    # порт
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()                 # работать бесконечно, то же самое что return await


process = Server()

try:
    asyncio.run(process.start())
except Exception:
    print("Сервер остановлен вручную")                 # не видно
    sys.exit(0)                                        # не срабатывает видимо

