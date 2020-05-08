"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports
from typing import Optional


class ClientProtocol(asyncio.Protocol): #coding info, working in network, etc...
    # login: str
    # server: 'Server'
    # transport: transports.Transport


    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        print(data)
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            #login:User
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").strip()
                if login.lower() in self.server.active_logins:
                    self.transport.write(f"Логин {login} занят, попробуйте другой".encode())
                    print(f"Ошибка: логин {login} уже занят")
                    self.connection_lost(None)
                else:
                    self.login = login
                    self.transport.write(
                        f"Привет, {self.login}!".encode()
                    )
                    asyncio.create_task(self.send_history())
        else:
            #self.transport.write(decoded)
            asyncio.create_task(self.send_message(decoded))

    async def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()

        async with self.server.msg_history_lock:
            self.server.msg_history.append(format_string)

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    async def send_history(self, n_last_messages=10):
        async with self.server.msg_history_lock:
            n_last_messages = min(n_last_messages, len(self.server.msg_history))
            last_messages = self.server.msg_history[-n_last_messages:]
        if n_last_messages > 0:
            self.transport.write(
                (f"Последние {n_last_messages} сообщений:\n" + "\n".join(last_messages)).encode()
            )



    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exc):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server():

    def __init__(self):
        self.clients = []
        self.msg_history = []
        self.msg_history_lock = asyncio.Lock()

    def create_protocol(self):
        return ClientProtocol(self)

    @property
    def active_logins(self):
        return [client.login.lower() for client in self.clients if client.login]


    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",  #address
            8888         #port - take around 9000 to 65000
        )





        print("Сервер запущен ... ")
        await coroutine.serve_forever()


process = Server()
try :
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
