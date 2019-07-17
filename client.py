import socket
import time
import pdb


class ClientError(Exception):
    '''Class implements client exceptions'''
    pass


class Client:
    '''Class implements the client'''
    def __init__(self, host, port, timeout=None):
        try:
            self.sock = socket.create_connection((host, port), timeout=timeout)
        except socket.error:
            raise ClientError("Can't initialize the client")
            
    def _get_data(self):
        '''Read the server's response, concatenate into one string'''
        data = ''
        # read the portions of the received data
        while True:
            try:
                response = self.sock.recv(1024).decode('utf8')
                data = data + response
                if response.endswith('\n\n'):
                    break
            except socket.error:
                raise ClientError("Can't read the server's response")
        stat, msg = data.lower().split('\n', 1)
        msg = msg.rstrip()
        return stat, msg
    
    def put(self, key, value, timestamp=None):
        '''Send the server a metric'''
        if not timestamp:
            timestamp = str(int(time.time()))
            
        # send the command to the server
        try:
            self.sock.sendall(f'put {key} {value} {timestamp}\n'.encode('utf8'))
        except socket.error:
            raise ClientError("Can't put a metric to the server")
        
        # analyze the server's response
        stat, _ = self._get_data()
        
        # throw the exception unless status='ok'
        if stat != 'ok':
            raise ClientError('An error has been received from the server while sending a metric')
            
    def get(self, key):
        '''Receive a metric/metrics from the server'''
        try:
            self.sock.sendall(f'get {key}\n'.encode('utf8'))
        except socket.error:
            raise ClientError("Can't get a metric from the server")
        
        # analyze the server's response
        stat, msg = self._get_data()
        
        # throw the exception unless status='ok'
        if stat != 'ok':
            raise ClientError('An error has been received from the server while sending a metric')
        
        # no results have been returned by the server
        result = dict()
        if msg == '':
            return result
        
        # process the received metric/s
        for entry in msg.split('\n'):
            key, value, timestamp = entry.split(' ')
            if key not in result:
                result[key] = []
            result[key].append((int(timestamp), float(value)))
                                   
        return result
    
    def close(self):
        '''Close the opened socket'''
        try:
            self.sock.close()
        except socket.error:
            raise ClientError("Can't close the socket")


if __name__ == '__main__':
    print('Testing the client')
    test_client = Client('127.0.0.1', 10001)
    test_client.put('key', 100)
    print(test_client.get("*"))
    test_client.close()
