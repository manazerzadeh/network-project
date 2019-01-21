import time
import src.Node
from typing import *


class GraphNode:
    def __init__(self, address):
        """

        :param address: (ip, port)
        :type address: tuple

        """
        self.address = address
        self.alive = False
        self.children = []
        pass

    def set_parent(self, parent):
        self.parent = parent
        pass

    def set_address(self, new_address):
        self.address = new_address
        pass

    def __reset(self):
        self.address = None
        self.parent = None
        self.child = None
        pass

    def add_child(self, child):
        self.children.append(child)
        pass


class NetworkGraph:
    def __init__(self, root):
        self.root = root
        root.alive = True
        self.nodes = [root]

    def find_live_node(self, sender):
        """
        Here we should find a neighbour for the sender.
        Best neighbour is the node who is nearest the root and has not more than one child.

        Code design suggestion:
            1. Do a BFS algorithm to find the target.

        Warnings:
            1. Check whether there is sender node in our NetworkGraph or not; if exist do not return sender node or
               any other nodes in it's sub-tree.

        :param sender: The node address we want to find best neighbour for it.
        :type sender: tuple

        :return: Best neighbour for sender.
        :rtype: GraphNode
        """
        node_list: list[GraphNode] = []
        node_list.append(self.root)
        while (node_list):
            for node in node_list:
                if (len(node.children) < 2):  # is this syntax right?!
                    return node
                node_list += node.children
                node_list.remove(node)
        pass

    def find_node(self, ip, port):
        for node in self.nodes:
            if (node.server_ip == ip and self.server_port == port):
                return node
        return None
        pass

    def turn_on_node(self, node_address):
        node = self.find_node(node_address[0], node_address[1])
        node.alive = True
        pass

    def turn_off_node(self, node_address):
        node = self.find_node(node_address[0], node_address[1])
        node.alive = False
        pass

    def remove_node(self, node_address):
        node = self.find_node(node_address[0], node_address[1])
        self.nodes.remove(node)
        pass

    def add_node(self, ip, port, father_address):
        """
        Add a new node with node_address if it does not exist in our NetworkGraph and set its father.

        Warnings:
            1. Don't forget to set the new node as one of the father_address children.
            2. Before using this function make sure that there is a node which has father_address.

        :param ip: IP address of the new node.
        :param port: Port of the new node.
        :param father_address: Father address of the new node

        :type ip: str
        :type port: int
        :type father_address: tuple


        :return:
        """
        father = self.find_node(father_address)
        if (father != None):
            node = GraphNode((ip, port))
            node.set_parent(father)
            father.add_child(node)
        pass
