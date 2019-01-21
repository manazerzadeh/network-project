"""

    This is the format of packets in our network:
    


                                                **  NEW Packet Format  **
     __________________________________________________________________________________________________________________
    |           Version(2 Bytes)         |         Type(2 Bytes)         |           Length(Long int/4 Bytes)          |
    |------------------------------------------------------------------------------------------------------------------|
    |                                            Source Server IP(8 Bytes)                                             |
    |------------------------------------------------------------------------------------------------------------------|
    |                                           Source Server Port(4 Bytes)                                            |
    |------------------------------------------------------------------------------------------------------------------|
    |                                                    ..........                                                    |
    |                                                       BODY                                                       |
    |                                                    ..........                                                    |
    |__________________________________________________________________________________________________________________|

    Version:
        For now version is 1
    
    Type:
        1: Register
        2: Advertise
        3: Join
        4: Message
        5: Reunion
                e.g: type = '2' => Advertise packet.
    Length:
        This field shows the character numbers for Body of the packet.

    Server IP/Port:
        We need this field for response packet in non-blocking mode.



    ***** For example: ******

    version = 1                 b'\x00\x01'
    type = 4                    b'\x00\x04'
    length = 12                 b'\x00\x00\x00\x0c'
    ip = '192.168.001.001'      b'\x00\xc0\x00\xa8\x00\x01\x00\x01'
    port = '65000'              b'\x00\x00\\xfd\xe8'
    Body = 'Hello World!'       b'Hello World!'

    Bytes = b'\x00\x01\x00\x04\x00\x00\x00\x0c\x00\xc0\x00\xa8\x00\x01\x00\x01\x00\x00\xfd\xe8Hello World!'




    Packet descriptions:
    
        Register:
            Request:
        
                                 ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |------------------------------------------------|
                |                  IP (15 Chars)                 |
                |------------------------------------------------|
                |                 Port (5 Chars)                 |
                |________________________________________________| 23
                
                For sending IP/Port of the current node to the root to ask if it can register to network or not.

            Response:
        
                                 ** Body Format **
                 _________________________________________________
                |                  RES (3 Chars)                  |
                |-------------------------------------------------|
                |                  ACK (3 Chars)                  |
                |_________________________________________________| 6
                
                For now only should just send an 'ACK' from the root to inform a node that it
                has been registered in the root if the 'Register Request' was successful.
                
        Advertise:
            Request:
            
                                ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |________________________________________________| 3
                
                Nodes for finding the IP/Port of their neighbour peer must send this packet to the root.

            Response:

                                ** Packet Format **
                 ________________________________________________
                |                RES(3 Chars)                    |
                |------------------------------------------------|
                |              Server IP (15 Chars)              |
                |------------------------------------------------|
                |             Server Port (5 Chars)              |
                |________________________________________________| 23

                Root will response Advertise Request packet with sending IP/Port of the requester peer in this packet.
                
        Join:

                                ** Body Format **
                 ________________________________________________
                |                 JOIN (4 Chars)                 |
                |________________________________________________|
            
            New node after getting Advertise Response from root must send this packet to the specified peer
            to tell him that they should connect together; When receiving this packet we should update our
            Client Dictionary in the Stream object.


            
        Message:
                                ** Body Format **
                 ________________________________________________
                |             Message (#Length Chars)            |
                |________________________________________________|

            The message that want to broadcast to hole network. Right now this type only includes a plain text.
        
        Reunion:
            Hello:
        
                                ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |------------------------------------------------|
                |           Number of Entries (2 Chars)          |
                |------------------------------------------------|
                |                 IP0 (15 Chars)                 |
                |------------------------------------------------|
                |                Port0 (5 Chars)                 |
                |------------------------------------------------|
                |                 IP1 (15 Chars)                 |
                |------------------------------------------------|
                |                Port1 (5 Chars)                 |
                |------------------------------------------------|
                |                     ...                        |
                |------------------------------------------------|
                |                 IPN (15 Chars)                 |
                |------------------------------------------------|
                |                PortN (5 Chars)                 |
                |________________________________________________|
                
                In every interval (for now 20 seconds) peers must send this message to the root.
                Every other peer that received this packet should append their (IP, port) to
                the packet and update Length.

            Hello Back:
        
                                    ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |------------------------------------------------|
                |           Number of Entries (2 Chars)          |
                |------------------------------------------------|
                |                 IPN (15 Chars)                 |
                |------------------------------------------------|
                |                PortN (5 Chars)                 |
                |------------------------------------------------|
                |                     ...                        |
                |------------------------------------------------|
                |                 IP1 (15 Chars)                 |
                |------------------------------------------------|
                |                Port1 (5 Chars)                 |
                |------------------------------------------------|
                |                 IP0 (15 Chars)                 |
                |------------------------------------------------|
                |                Port0 (5 Chars)                 |
                |________________________________________________|

                Root in an answer to the Reunion Hello message will send this packet to the target node.
                In this packet, all the nodes (IP, port) exist in order by path traversal to target.
            
    
"""
# from struct import *
# from typing import *

from src.tools import utils


class Packet:
    def __init__(self, buf: bytearray):
        """
        The decoded buffer should convert to a new packet.

        :param buf: Input buffer was just decoded.
        :type buf: bytearray
        """
        self.buf = buf

        self.version = int.from_bytes(buf[0:2], byteorder='big', signed=False)
        self.type = int.from_bytes(buf[2:4], byteorder='big', signed=False)
        self.length = int.from_bytes(buf[4:8], byteorder='big', signed=False)

        self.ip = utils.bytes_to_ip(buf[8:16])

        self.port = str(int.from_bytes(buf[16:20], byteorder='big', signed=False))

        if utils.DEBUG:
            print("DDD::version = " + str(self.version), '-type = ' + str(self.type) + '-len = ' + str(self.length) +
                  '-ip = ' + self.ip + '-port = ' + self.port)
            print(str(buf[20:]))

        self.body = buf[20:].decode()

    def get_header(self):
        """

        :return: Packet header
        :rtype: str
        """
        return str(self.version) + str(self.type) + str(self.length) + self.ip + self.port

    def get_version(self):
        """

        :return: Packet Version
        :rtype: int
        """
        return self.version

    def get_type(self):
        """

        :return: Packet type
        :rtype: int
        """
        return self.type

    def get_length(self):
        """

        :return: Packet length
        :rtype: int
        """
        return self.length

    def get_body(self):
        """

        :return: Packet body
        :rtype: str
        """
        return self.body

    def get_buf(self):
        """
        In this function, we will make our final buffer that represents the Packet with the Struct class methods.

        :return The parsed packet to the network format.
        :rtype: bytearray
        """
        b_version = utils.int_to_bytes(self.version, 2)
        b_type = utils.int_to_bytes(self.type, 2)
        b_length = utils.int_to_bytes(self.length, 4)
        b_ip = utils.ip_to_bytes(self.ip)
        b_port = utils.int_to_bytes(int(self.port), 4)
        b_body = self.body.encode()

        if utils.DEBUG:
            if bytearray(b_version + b_type + b_length + b_ip + b_port + b_body) == self.buf:
                print("DDD::U did it right! :))")
        return bytearray(b_version + b_type + b_length + b_ip + b_port + b_body)

    def get_source_server_ip(self):
        """

        :return: Server IP address for the sender of the packet.
        :rtype: str
        """
        return self.ip

    def get_source_server_port(self):
        """

        :return: Server Port address for the sender of the packet.
        :rtype: str
        """
        return self.port

    def get_source_server_address(self):
        """

        :return: Server address; The format is like ('192.168.001.001', '05335').
        :rtype: tuple
        """
        return self.ip, self.port


class PacketFactory:
    """
    This class is only for making Packet objects.
    """

    @staticmethod
    def parse_buffer(buffer: bytearray):
        """
        In this function we will make a new Packet from input buffer with struct class methods.

        :param buffer: The buffer that should be parse to a validate packet format

        :return new packet
        :rtype: Packet

        """
        return Packet(buffer)

    @staticmethod
    def new_reunion_packet(type: str, source_address: (str, str), nodes_array: list):
        """
        :param type: Reunion Hello (REQ) or Reunion Hello Back (RES)
        :param source_address: IP/Port address of the packet sender.
        :param nodes_array: [(ip0, port0), (ip1, port1), ...] It is the path to the 'destination'.

        :type type: str
        :type source_address: tuple
        :type nodes_array: list

        :return New reunion packet.
        :rtype Packet
        """
        # Packet Header info
        p_version = 1
        p_type = 5  # reunion packet
        p_length = 5 + 20 * len(nodes_array)
        p_ip, p_port = source_address

        b_version = utils.int_to_bytes(p_version, 2)
        b_type = utils.int_to_bytes(p_type, 2)
        b_length = utils.int_to_bytes(p_length, 4)
        b_ip = utils.ip_to_bytes(p_ip)
        b_port = utils.int_to_bytes(int(p_port), 4)
        header_bytes = b_version + b_type + b_length + b_ip + b_port

        number_of_entries = len(nodes_array)
        p_num_of_entries = '{0:02d}'.format(number_of_entries)
        # pack body
        # fmt = '3s' + '2s'
        # for i in range(number_of_entries):
        #     fmt += '15s' + '5s'
        body = type + p_num_of_entries

        # todo: double check this...
        if type == 'REQ':
            for i in range(len(nodes_array)):
                body += nodes_array[i][0] + nodes_array[i][1]
        elif type == 'RES':
            for i in range(len(nodes_array) - 1, -1, -1):
                body += nodes_array[i][0] + nodes_array[i][1]

        body_bytes = body.encode()

        packet_bytes = bytearray(header_bytes + body_bytes)
        return Packet(packet_bytes)

    @staticmethod
    def new_advertise_packet(type, source_server_address, neighbour=None):
        """
        :param type: Type of Advertise packet
        :param source_server_address Server address of the packet sender.
        :param neighbour: The neighbour for advertise response packet; The format is like ('192.168.001.001', '05335').

        :type type: str
        :type source_server_address: tuple
        :type neighbour: tuple

        :return New advertise packet.
        :rtype Packet

        """
        # Packet Header info
        p_version = 1
        p_type = 2  # advertise packet
        p_length = 3
        if type == 'RES':
            p_length = 3 + 20
        elif type == 'REQ':
            p_length = 3

        p_ip, p_port = source_server_address

        b_version = utils.int_to_bytes(p_version, 2)
        b_type = utils.int_to_bytes(p_type, 2)
        b_length = utils.int_to_bytes(p_length, 4)
        b_ip = utils.ip_to_bytes(p_ip)
        b_port = utils.int_to_bytes(int(p_port), 4)
        header_bytes = b_version + b_type + b_length + b_ip + b_port

        # packet body
        body = ''
        if type == 'RES':
            body += type
            if neighbour is not None:
                body = body + neighbour[0] + neighbour[1]
            else:
                print("there's a problem... the neighbour address in the advertise response can't be None.")
        elif type == 'REQ':
            body = type
        body_bytes = body.encode()

        packet_bytes = bytearray(header_bytes + body_bytes)
        return Packet(packet_bytes)

    @staticmethod
    def new_join_packet(source_server_address):
        """
        :param source_server_address: Server address of the packet sender.

        :type source_server_address: tuple

        :return New join packet.
        :rtype Packet

        """
        # Packet Header info
        p_version = 1
        p_type = 3  # advertise packet
        p_length = 4
        p_ip, p_port = source_server_address

        b_version = utils.int_to_bytes(p_version, 2)
        b_type = utils.int_to_bytes(p_type, 2)
        b_length = utils.int_to_bytes(p_length, 4)
        b_ip = utils.ip_to_bytes(p_ip)
        b_port = utils.int_to_bytes(int(p_port), 4)
        header_bytes = b_version + b_type + b_length + b_ip + b_port

        body = 'JOIN'
        body_bytes = body.encode()

        packet_bytes = bytearray(header_bytes + body_bytes)
        return Packet(packet_bytes)

    @staticmethod
    def new_register_packet(type, source_server_address, address=(None, None)):
        """
        :param type: Type of Register packet
        :param source_server_address: Server address of the packet sender.
        :param address: If 'type' is 'request' we need an address; The format is like ('192.168.001.001', '05335').

        :type type: str
        :type source_server_address: tuple
        :type address: tuple

        :return New Register packet.
        :rtype Packet

        """
        # Packet Header info
        p_version = 1
        p_type = 1  # register packet
        p_length = 23
        if type == 'REQ':
            p_length = 3 + 20
        elif type == 'RES':
            p_length = 6
        p_ip, p_port = source_server_address

        b_version = utils.int_to_bytes(p_version, 2)
        b_type = utils.int_to_bytes(p_type, 2)
        b_length = utils.int_to_bytes(p_length, 4)
        b_ip = utils.ip_to_bytes(p_ip)
        b_port = utils.int_to_bytes(int(p_port), 4)
        header_bytes = b_version + b_type + b_length + b_ip + b_port

        # Body
        body = type
        if type == 'REQ':
            if address is not None:
                body = body + address[0] + address[1]
            else:
                print("there's a problem... the address in the register request can't be None.")
        elif type == 'RES':
            body += 'ACK'
        body_bytes = body.encode()

        packet_bytes = bytearray(header_bytes + body_bytes)
        return Packet(packet_bytes)

    @staticmethod
    def new_message_packet(message, source_server_address):
        """
        Packet for sending a broadcast message to the whole network.

        :param message: Our message
        :param source_server_address: Server address of the packet sender.

        :type message: str
        :type source_server_address: tuple

        :return: New Message packet.
        :rtype: Packet
        """
        p_version = 1
        p_type = 4  # message packet
        p_length = len(message)
        p_ip, p_port = source_server_address

        b_version = utils.int_to_bytes(p_version, 2)
        b_type = utils.int_to_bytes(p_type, 2)
        b_length = utils.int_to_bytes(p_length, 4)
        b_ip = utils.ip_to_bytes(p_ip)
        b_port = utils.int_to_bytes(int(p_port), 4)
        header_bytes = b_version + b_type + b_length + b_ip + b_port

        # Body
        body = message
        body_bytes = body.encode()

        packet_bytes = bytearray(header_bytes + body_bytes)
        return Packet(packet_bytes)


"""
from Packet import *
nodes = [('192.168.001.002'  , '75000'),('192.168.001.003'  , '85000'),('192.168.001.004'  , '95000')]
type = 'REQ'
source = ('192.168.001.001'  , '65000')
p1 = PacketFactory.new_reunion_packet('REQ' , source , nodes)
p2 = PacketFactory.new_reunion_packet('RES' , source , nodes)

"""
