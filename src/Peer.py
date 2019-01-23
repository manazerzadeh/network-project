import threading
import time
from typing import *

from src.Stream import Stream
from src.Packet import Packet, PacketFactory
from src.UserInterface import UserInterface
from src.tools.Node import Node
from src.tools import utils
from src.tools.NetworkGraph import NetworkGraph

"""
    Peer is our main object in this project.
    In this network Peers will connect together to make a tree graph.
    This network is not completely decentralised but will show you some real-world challenges in Peer to Peer networks.
    
"""


class Peer:
    def __init__(self, server_ip, server_port, is_root=False, root_address=None):
        """
        The Peer object constructor.

        Code design suggestions:
            1. Initialise a Stream object for our Peer.
            2. Initialise a PacketFactory object.
            3. Initialise our UserInterface for interaction with user commandline.
            4. Initialise a Thread for handling reunion daemon.

        Warnings:
            1. For root Peer, we need a NetworkGraph object.
            2. In root Peer, start reunion daemon as soon as possible.
            3. In client Peer, we need to connect to the root of the network, Don't forget to set this connection
               as a register_connection.


        :param server_ip: Server IP address for this Peer that should be pass to Stream.
        :param server_port: Server Port address for this Peer that should be pass to Stream.
        :param is_root: Specify that is this Peer root or not.
        :param root_address: Root IP/Port address if we are a client.

        :type server_ip: str
        :type server_port: int
        :type is_root: bool
        :type root_address: tuple
        """
        self.userInterface = UserInterface()
        self.address = (server_ip, server_port)
        self.is_root = is_root
        self.root_address = root_address
        self.stream = Stream(server_ip, server_port)
        self.packetfactory = PacketFactory()
        self.start_user_interface()
        self.hello_sent_time = 0
        self.time_out_limit = 32
        self.last_hello_times = {}
        self.registered_nodes: List[Node] = []
        self.parent_address = (None, None)
        self.children_addresses: List[(str, str)] = []
        self.daemon_thread = threading.Thread(target=self.run_reunion_daemon)
        if is_root:
            self.daemon_thread.start()
            self.networkGraph = NetworkGraph(self)
        else:
            self.stream.add_node(root_address, set_register_connection=True)
            self.w8_for_back = False

            pass  # in peers not root handle run reunion_daeamon when joined the network

    def start_user_interface(self):
        """
        For starting UserInterface thread.

        :return:
        """
        threading.Thread(target=self.userInterface.run).start()
        pass

    def handle_user_interface_buffer(self):
        """
        In every interval, we should parse user command that buffered from our UserInterface.
        All of the valid commands are listed below:
            1. Register:  With this command, the client send a Register Request packet to the root of the network.
            2. Advertise: Send an Advertise Request to the root of the network for finding first hope.
            3. SendMessage: The following string will be added to a new Message packet and broadcast through the network.

        Warnings:
            1. Ignore irregular commands from the user.
            2. Don't forget to clear our UserInterface buffer.
        :return:
        """
        # todo: @mamdos handle this shit... OK baba!
        commands = self.userInterface.buffer
        is_sendMessage = False
        for index in range(len(commands)):
            if is_sendMessage:
                is_sendMessage = False
                new_broadcast_message = self.packetfactory.new_message_packet(commands[index], self.address)
                self.stream.add_message_to_out_buff(self.parent_address, new_broadcast_message.get_buf())
                for node in self.children_addresses:
                    self.stream.add_message_to_out_buff(node, new_broadcast_message.get_buf())
            if commands[index] == 'Register':
                std_root_addr = (self.root_address[0], Node.parse_port(self.root_address[1]))
                new_register_packet = self.packetfactory.new_register_packet('REQ', self.address, std_root_addr)
                self.stream.add_message_to_out_buff(self.root_address, new_register_packet.get_buf())
            elif commands[index] == 'Advertise':
                new_advertise_packet = self.packetfactory.new_advertise_packet('REQ', self.address)
                self.stream.add_message_to_out_buff(self.root_address, new_advertise_packet.get_buf())
            elif commands[index] == 'SendMessage': # todo: fix the message body pls!
                is_sendMessage = True
            commands.pop(index)
            index -= 1

        pass

    def run(self):
        """
        The main loop of the program.
        Code design suggestions:
            1. Parse server in_buf of the stream.
            2. Handle all packets were received from our Stream server.
            3. Parse user_interface_buffer to make message packets.
            4. Send packets stored in nodes buffer of our Stream object.
            5. ** sleep the current thread for 2 seconds **

        Warnings:
            1. At first check reunion daemon condition; Maybe we have a problem in this time
               and so we should hold any actions until Reunion acceptance.
            2. In every situation checkout Advertise Response packets; even is Reunion in failure mode or not

        :return:
        """
        while True:
            for buff in self.stream._server_in_buf:
                packet = PacketFactory.parse_buffer(buff)
                self.handle_packet(packet)
            self.handle_user_interface_buffer()
            self.stream.send_out_buf_messages()  # todo. what is register
            time.sleep(2)
        pass

    def run_reunion_daemon(self):
        """

        In this function, we will handle all Reunion actions.

        Code design suggestions:
            1. Check if we are the network root or not; The actions are identical.
            2. If it's the root Peer, in every interval check the latest Reunion packet arrival time from every node;
               If time is over for the node turn it off (Maybe you need to remove it from our NetworkGraph).
            3. If it's a non-root peer split the actions by considering whether we are waiting for Reunion Hello Back
               Packet or it's the time to send new Reunion Hello packet.

        Warnings:
            1. If we are the root of the network in the situation that we want to turn a node off, make sure that you will not
               advertise the nodes sub-tree in our GraphNode.
            2. If we are a non-root Peer, save the time when you have sent your last Reunion Hello packet; You need this
               time for checking whether the Reunion was failed or not.
            3. For choosing time intervals you should wait until Reunion Hello or Reunion Hello Back arrival,
               pay attention that our NetworkGraph depth will not be bigger than 8. (Do not forget main loop sleep time)
            4. Suppose that you are a non-root Peer and Reunion was failed, In this time you should make a new Advertise
               Request packet and send it through your register_connection to the root; Don't forget to send this packet
               here, because in the Reunion Failure mode our main loop will not work properly and everything will be got stock!

        :return:
        """

        while True:
            if self.is_root:
                # check if the reunion time_out has exceeded
                for address, starting_time in self.last_hello_times.items():
                    if time.time() - starting_time > self.time_out_limit / 2:
                        g_node = self.networkGraph.find_node(address[0], address[1])
                        # turn_off every child of the removing node
                        up_most_gnode = g_node
                        children_list = [g_node]
                        while children_list:
                            for obj in children_list:
                                children_list += obj.children
                                self.networkGraph.turn_off_node(obj.address)
                                children_list.remove(obj)
                        self.networkGraph.remove_node(up_most_gnode.address)
                    else:
                        pass

                pass
            else:  # normal node ... not root
                if self.w8_for_back:
                    if time.time() - self.hello_sent_time > self.time_out_limit:
                        self.w8_for_back = False
                        advertise_pac = self.packetfactory.new_advertise_packet('REQ', self.address)
                        self.stream.add_message_to_out_buff(self.root_address, advertise_pac.get_buf())
                        break
                    else:
                        pass
                else:  # send reunion hello again
                    self.w8_for_back = True
                    reunion_hello_packet = self.packetfactory.new_reunion_packet('REQ', self.address, [self.address])
                    self.stream.add_message_to_out_buff(self.parent_address, reunion_hello_packet.get_buf())
                    self.hello_sent_time = time.time()
            time.sleep(4)  # Fuck You!
        pass

    def send_broadcast_packet(self, broadcast_packet):
        """

        For setting broadcast packets buffer into Nodes out_buff.

        Warnings:
            1. Don't send Message packets through register_connections.

        :param broadcast_packet: The packet that should be broadcast through the network.
        :type broadcast_packet: Packet

        :return:
        """
        parsed_packet = broadcast_packet.get_buf()
        for node in self.stream.nodes:
            if node.get_server_address() != self.root_address:
                self.stream.add_message_to_out_buff(node.get_server_address(), parsed_packet)
        pass

    def handle_packet(self, packet):  # raise exception if it is not valid
        """
        This function act as a wrapper for other handle_###_packet methods to handle the packet.

        Code design suggestion:
            1. It's better to check packet validation right now; For example Validation of the packet length.

        :param packet: The arrived packet that should be handled.

        :type packet Packet
        """
        if packet.length != len(packet.get_body()):
            print('The length is not valid')
            raise Exception('The Length not valid Exception')
            # just... do the damn validation tests

        # Register packet
        if packet.get_type() == 1:
            self.__handle_register_packet(packet)
        elif packet.get_type() == 2:
            self.__handle_advertise_packet(packet)
        elif packet.get_type() == 3:
            self.__handle_join_packet(packet)
        elif packet.get_type() == 4:
            self.__handle_message_packet(packet)
        elif packet.get_type == 5:
            self.__handle_reunion_packet(packet)
        else:
            print('Packet type not valid')
        pass

    def __check_registered(self, source_address):
        """
        If the Peer is the root of the network we need to find that is a node registered or not.

        :param source_address: Unknown IP/Port address.
        :type source_address: tuple

        :return:
        """
        for node in self.registered_nodes:
            if source_address == node.get_server_address():
                return True
        return False
        pass

    def __handle_advertise_packet(self, packet):  # todo: check warning 3
        """
        For advertising peers in the network, It is peer discovery message.

        Request:
            We should act as the root of the network and reply with a neighbour address in a new Advertise Response packet.

        Response:
            When an Advertise Response packet type arrived we should update our parent peer and send a Join packet to the
            new parent.

        Code design suggestion:
            1. Start the Reunion daemon thread when the first Advertise Response packet received.
            2. When an Advertise Response message arrived, make a new Join packet immediately for the advertised address.

        Warnings:
            1. Don't forget to ignore Advertise Request packets when you are a non-root peer.
            2. The addresses which still haven't registered to the network can not request any peer discovery message.
            3. Maybe it's not the first time that the source of the packet sends Advertise Request message. This will happen
               in rare situations like Reunion Failure. Pay attention, don't advertise the address to the packet sender
               sub-tree.
            4. When an Advertise Response packet arrived update our Peer parent for sending Reunion Packets.

        :param packet: Arrived register packet

        :type packet Packet

        :return:
        """
        type = packet.get_body()[:3]
        if type == 'REQ':
            if self.is_root:
                if self.__check_registered(packet.get_source_server_address()):
                    father_address = self.networkGraph.find_live_node(packet.get_source_server_address()).address
                    self.networkGraph.add_node(packet.get_source_server_ip(), int(packet.get_source_server_port())
                                               , father_address)
                    resp_packet = PacketFactory.new_advertise_packet('RES', self.address, father_address)
                    self.stream.add_message_to_out_buff(packet.get_source_server_address(), resp_packet.get_buf())

                else:
                    raise Exception('Node was not registered')
            if not self.is_root:
                if utils.DEBUG: print("Advertise packet in the wrong address:", self.address)
        if type == 'RES':
            p_body = packet.get_body()[3:]
            add = p_body[3:18]
            port = p_body[18:]
            self.parent_address = (add, port)
            self.stream.add_node(self.parent_address, False)
            join_packet = self.packetfactory.new_join_packet(self.address)
            self.stream.add_message_to_out_buff(self.parent_address, join_packet.get_buf())
            self.daemon_thread.start()
        pass

    def __handle_register_packet(self, packet):
        """
        For registration a new node to the network at first we should make a Node with stream.add_node for'sender' and
        save it.

        Code design suggestion:
            1.For checking whether an address is registered since now or not you can use SemiNode object except Node.

        Warnings:
            1. Don't forget to ignore Register Request packets when you are a non-root peer.

        :param packet: Arrived register packet
        :type packet Packet
        :return:
        """
        p_type = packet.get_body()[:3]
        if self.is_root:
            if p_type == 'REQ':
                self.registered_nodes.append(self.stream.add_node(packet.get_source_server_address(), True))
            elif p_type == 'RES':
                pass
        else:
            if p_type == 'REQ':
                pass
            elif p_type == 'RES':
                if packet.get_body()[3:] == 'ACK':
                    advertise_packet = self.packetfactory.new_advertise_packet('REQ', self.address)
                    self.stream.add_message_to_out_buff(self.address, advertise_packet.get_buf())
                else:
                    raise Exception('The Register response is not valid')
            pass

    def __check_neighbour(self, address):
        """
        It checks is the address in our neighbours array or not.

        :param address: Unknown address

        :type address: tuple

        :return: Whether is address in our neighbours or not.
        :rtype: bool
        """
        if self.parent_address == address:
            return True
        for child in self.children_addresses:
            if child == address:
                return True
        return False

    def __handle_message_packet(self, packet):
        """
        Only broadcast message to the other nodes.

        Warnings:
            1. Do not forget to ignore messages from unknown sources.
            2. Make sure that you are not sending a message to a register_connection.

        :param packet: Arrived message packet

        :type packet Packet

        :return:
        """
        source_address = packet.get_source_server_address()
        new_message_packet = self.packetfactory.new_message_packet(packet.get_body(), self.address)
        if self.__check_neighbour(source_address):
            for node in self.stream.nodes:
                if node.get_server_address() != source_address and not node.is_registered:
                    self.stream.add_message_to_out_buff(node.get_server_address(), new_message_packet.get_buf())
        else:
            raise Exception('The source was unknown for me!')

    def __handle_reunion_packet(self, packet):
        """
        In this function we should handle Reunion packet that had just arrived.

        Reunion Hello:
            If you are root Peer you should answer with a new Reunion Hello Back packet.
            At first extract all addresses in the packet body and append them in descending order to the new packet.
            You should send the new packet to the first address in the arrived packet.
            If you are a non-root Peer append your IP/Port address to the end of the packet and send it to your parent.

        Reunion Hello Back:
            Check that you are the end node or not; If not only remove your IP/Port address and send the packet to the next
            address, otherwise you received your response from the root and everything is fine.

        Warnings:
            1. Every time adding or removing an address from packet don't forget to update Entity Number field.
            2. If you are the root, update last Reunion Hello arrival packet from the sender node and turn it on.
            3. If you are the end node, update your Reunion mode from pending to acceptance.


        :param packet: Arrived reunion packet
        :return:
        """
        p_type = packet.get_body()[:3]
        entry_num = int(packet.get_body()[3:5])
        nodes_array = []
        for i in range(entry_num):
            array_entry = (packet.get_body()[5+20*i:5+20*i+15], packet.get_body()[5+20*i+15:5+20*i+15+5])
            nodes_array.append(array_entry)
        if self.is_root:
            # update the time of the node/peer(fuck!) that the packet has received from
            if p_type == 'REQ':
                self.last_hello_times[nodes_array[0]] = time.time()
                send_to_node_address = nodes_array[-1]
                self.networkGraph.turn_on_node(send_to_node_address)
                nodes_array.reverse()
                new_reunion_back_packet = self.packetfactory.new_reunion_packet('RES', self.address, nodes_array)
                self.stream.add_message_to_out_buff(send_to_node_address,new_reunion_back_packet.get_buf())
            elif p_type == 'RES:':
                pass
            else:
                raise Exception('Reunion packet type is invalid (Root)')
        else:
            if p_type == 'REQ':
                nodes_array.append(self.address)
                new_reunion_back_packet = self.packetfactory.new_reunion_packet('REQ', self.address, nodes_array)
                send_to_node_address = self.parent_address
                self.stream.add_message_to_out_buff(send_to_node_address, new_reunion_back_packet.get_buf())

            elif p_type == 'RES':
                if entry_num == 1:
                    if nodes_array[0] == self.address: # we received the reunion back successfully
                        self.w8_for_back = False
                        print('Reunion Hello Back is received Successfully!')
                    else:
                        raise Exception('The destination of the Reunion Back was wrong!')
                else:
                    if nodes_array[0] == self.address:
                        nodes_array.remove(self.address)
                        send_to_node_address = nodes_array[0]
                        if self.__check_neighbour(send_to_node_address):
                            new_reunion_back_packet = self.packetfactory.new_reunion_packet('RES', self.address
                                                                                            , nodes_array)
                            self.stream.add_message_to_out_buff(nodes_array[0], new_reunion_back_packet.get_buf())
                        else:
                            raise Exception('The next address is not a neighbour or something has gone wrong!')
                    else:
                        raise Exception('The end node was not mine!')
            else:
                Exception('Reunion type is invalid (non-root)')

    def __handle_join_packet(self, packet):
        """
        When a Join packet received we should add a new node to our nodes array.
        In reality, there is a security level that forbids joining every node to our network. -> k@$3 @m@& baba!

        :param packet: Arrived register packet.


        :type packet Packet

        :return:
        """

        # for better security scenario, we can send a register request as a parent with the address of the new child
        # to the root to ask if this guy is validated to be in the network of not? and after receiving the ack from the
        # root, we'll accept the new peer as our child...

        packet_source_address = packet.get_source_server_address()
        self.stream.add_node(packet_source_address, False)
        self.children_addresses.append(packet_source_address)

    def __get_neighbour(self, sender):
        """
        Finds the best neighbour for the 'sender' from the network_nodes array.
        This function only will call when you are a root peer.

        Code design suggestion:
            1. Use your NetworkGraph find_live_node to find the best neighbour.

        :param sender: Sender of the packet
        :return: The specified neighbour for the sender; The format is like ('192.168.001.001', '05335').
        """
        return self.networkGraph.find_live_node(sender).address
        pass
