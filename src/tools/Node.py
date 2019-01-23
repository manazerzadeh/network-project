from src.tools.simpletcp.clientsocket import *


class Node:
    def __init__(self, server_address, set_root=False, set_register=False):
        """
        The Node object constructor.

        This object is our low-level abstraction for other peers in the network.
        Every node has a ClientSocket that should bind to the Node TCPServer address.

        Warnings:
            1. Insert an exception handler when initializing the ClientSocket; when a socket closed here we will face to
               an exception and we should detach this Node and clear its output buffer.

        :param server_address:
        :param set_root:
        :param set_register:
        """
        # todo: check set_root and set_register flag
        self.is_registered = set_register
        self.is_root = set_root  # todo: just to be sure... check this later!

        self.server_ip = Node.parse_ip(server_address[0])
        self.server_port = Node.parse_port(server_address[1])

        print("Server Address: ", server_address)

        self.out_buff = []
        # todo: insert exception handler... done
        try:
            self.socket = ClientSocket(self.server_ip, int(self.server_port), single_use=False)
        except:
            raise Exception('Exception while creating ClientSocket')  # todo: is this right?!... yes...fuck you!
        pass

    def send_message(self):
        """
        Final function to send buffer to the client's socket.

        :return:
        """
        for message in self.out_buff:
            self.socket.send(message)
        # todo: should the out_buff be clear after sending?
        self.out_buff.clear()
        pass

    def add_message_to_out_buff(self, message):
        """
        Here we will add a new message to the server out_buff, then in 'send_message' will send them.

        :param message: The message we want to add to out_buff
        :return:
        """
        # todo: i don't know for sure if this'll work!
        if type(message) != bytearray or type(message) != str:
            raise ValueError
        self.out_buff.append(message)

    def close(self):
        """
        Closing client's object.
        :return:
        """
        self.socket.close()

    def get_server_address(self):
        """

        :return: Server address in a pretty format.
        :rtype: tuple
        """
        return self.server_ip, self.server_port

    @staticmethod
    def parse_ip(ip):
        """
        Automatically change the input IP format like '192.168.001.001'.
        :param ip: Input IP
        :type ip: str

        :return: Formatted IP
        :rtype: str
        """
        return '.'.join(str(int(part)).zfill(3) for part in ip.split('.'))

    @staticmethod
    def parse_port(port):
        """
        Automatically change the input IP format like '05335'.
        :param port: Input IP
        :type port: str

        :return: Formatted IP
        :rtype: str
        """
        return str(int(port)).zfill(5)
