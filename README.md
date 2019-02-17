# network-project
A simple peer-to-peer network!
This network consists of clients and one Root which also acts as a DNS server and maintains the structure of whole network. 
Each client send register request to the root first, then gets it's father to join to by sending an advertise message to the root.
When connected each client sends a 'Reunion Hello' to his father to infrom the root, that specific client is active. In response, root
sends reunion hello back to that specific client. 
Following is the UML diagram of the network:
