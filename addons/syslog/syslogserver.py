import socket
import redis
import os


UDP_IP = "0.0.0.0"
UDP_PORT = 514

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

r = redis.Redis()


def main():
    while True:
        data, addr = sock.recvfrom(1024)
        data = data.strip()
        r.publish(f"syslog.{addr[0]}", data)


def fork(func):
    pid = os.fork()
    if pid > 0:
        return
    os.chdir("/")
    os.setsid()
    os.umask(0)
    pid = os.fork()
    if pid > 0:
        return
    func()


if __name__ == "__main__":
    fork(main)
