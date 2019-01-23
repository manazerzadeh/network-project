from src.Peer import Peer
import threading
if __name__ == "__main__":
    server = Peer("127.000.000.001", 3652, is_root=True)
    threading.Thread(target=server.run).start()

    client = Peer("127.000.000.001", 35315, is_root=False,
                  root_address=("127.000.000.001", 3652))
    threading.Thread(target=client.run).start()
