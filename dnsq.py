import sys
import socket

sa = sys.argv
lsa = len(sys.argv)
if lsa != 2:
    print("Usage: python {} FQDN.".format(sa[0]))
    print("Example: python {} www.t-mobile.com".format(sa[0]))
    sys.exit(1)

addr1 = socket.gethostbyname(sa[1])
print ("{0} resolves to {1}".format(sa[1],addr1))
