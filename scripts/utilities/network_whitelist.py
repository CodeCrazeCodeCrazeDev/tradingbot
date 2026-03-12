import socket
import sys

WHITELIST = {'8.8.8.8', '1.1.1.1'}  # Example allowed IPs

class NetworkWhitelist:
    def __init__(self, whitelist=WHITELIST):
        self.whitelist = whitelist

    def is_allowed(self, host):
        try:
            ip = socket.gethostbyname(host)
        except Exception:
            return False
        return ip in self.whitelist

# Example usage:
if __name__ == '__main__':
    nw = NetworkWhitelist()
    print('google.com allowed:', nw.is_allowed('google.com'))
    print('example.com allowed:', nw.is_allowed('example.com'))
