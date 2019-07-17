import asyncio

response_ok = 'ok'
response_error = 'error'
response_sep = '\n'

command_put = 'put'
command_get = 'get'


class ServerError(Exception):
    """Raise should something go wrong"""
    pass


class Storage:
    """Internally stores metrics on the server"""

    def __init__(self):
        self._storage = {}

    def put(self, key, value, timestamp):
        if key not in self._storage:
            self._storage[key] = {}
        self._storage[key][timestamp] = value

    def get(self, key):
        data = self._storage
        if key != "*":
            data = {key: data.get(key, {})}
        result = {}
        for key, timestamp_data in data.items():
            result[key] = sorted(timestamp_data.items())

        return result


class Executor:
    """Processes the commands within the loop"""

    def __init__(self, storage):
        self.storage = storage

    def run(self, method, *params):
        if method == command_put:
            return self.storage.put(*params)
        elif method == command_get:
            return self.storage.get(*params)
        else:
            raise ServerError("Unknown command or malformed request")


class EchoServerProtocol(asyncio.Protocol):
    """Implements the methods required to run the loop"""
    storage = Storage()

    def __init__(self):
        super().__init__()
        self.executor = Executor(self.storage)
        self._buffer = bytes()

    @staticmethod
    def form_server_response(responses):
        """Form the response to be sent to the client"""
        rows = []
        for response in responses:
            if not response:
                continue
            for key, values in response.items():
                for timestamp, value in values:
                    rows.append(f"{key} {value} {timestamp}")
        result = response_ok + response_sep
        if rows:
            result += response_sep.join(rows) + response_sep
        return result + response_sep

    @staticmethod
    def parse_client_request(data):
        """Parse the request received from the client"""
        parts = data.split(response_sep)
        commands = []
        for part in parts:
            if not part:
                continue

            method, params = part.strip().split(" ", 1)
            if method == command_put:
                key, value, timestamp = params.split()
                commands.append((method, key, float(value), int(timestamp)))
            elif method == command_get:
                key = params
                commands.append((method, key))
            else:
                raise ServerError("Unknown command or malformed request")

        return commands

    def process_data(self, data):
        commands = self.parse_client_request(data)

        results = []
        for command in commands:
            response = self.executor.run(*command)
            results.append(response)

        return self.form_server_response(results)

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        self._buffer += data
        try:
            decoded_data = self._buffer.decode()
        except UnicodeDecodeError:
            return

        if not decoded_data.endswith(response_sep):
            return

        self._buffer = bytes()

        try:
            resp = self.process_data(decoded_data)
        except ServerError as err:
            self.transport.write(f'{response_error}{response_sep}{err}{response_sep}{response_sep}'.encode('utf8'))
            return

        self.transport.write(resp.encode('utf8'))


def run_server(host, port):
    """Start the server"""
    loop = asyncio.get_event_loop()
    server = loop.create_server(EchoServerProtocol, host, port)
    future = loop.run_until_complete(server)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    future.close()
    loop.run_until_complete(future.wait_closed())
    loop.close()


if __name__ == "__main__":
    run_server('127.0.0.1', 10001)
