#!/usr/bin/env python
# encoding: utf-8

__author__ = "SYA-KE <syakesaba@gmail.com>"

# load me using load_module
# load_module("serialize")

import json
from scapy.all import *# for globals()

@conf.commands.register
def dump_packet_as_json_str(p,filename=None):
    """dump packet as json.

    @param p: Packet or PacketList
    @param filename: filename to dump to (if None, dump to str)
    @type command: str
    """
    s = _dump_packet_as_str(p)
    if filename is not None:
        json.dump(s, file(filename,"wb"),ensure_ascii=False)
        return
    else:
        return json.dumps(s, ensure_ascii=False)

def _dump_packet_as_str(p):
    if isinstance(p, PacketList):
        return [_dumps_json(pkt) for pkt in p]
    elif isinstance(p, Packet):
        return [_dumps_json(p)]
    raise TypeError("Packet or PacketList allowed for argument 1")

def _dumps_json(p):
    i = 0
    serialized = []
    if type(p) == tuple:#for traceroute packetlist
        p = p[0]
    layer = p.getlayer(i)
    while layer:
        serialized.append((layer.__class__.__name__,layer.fields))
        i += 1
        layer = p.getlayer(i)
    return serialized

@conf.commands.register
def load_packets_from_json_file(filename):
    """ laod json file as PacketList

    @param filename: filename to load json PacketList
    @type filename: str
    """
    f = file(filename,"rb")
    p = f.read()
    f.close()
    return PacketList(load_packets_from_json_str(p),name=filename)

@conf.commands.register
def load_packets_from_json_str(s):
    """ load json string as PacketList

    @param p: string to load json PacketList
    @type p: str
    """
    json_loaded = json.loads(s)
    return PacketList([_loads_json(pkt) for pkt in json_loaded])

def _loads_json(s):
    deserialized = None
    for i in range(len(s)):
        serialized = s[i]
        layer = globals().get(serialized[0] ,None)
        if layer is None:
        #    print "Could not read class '"+serialized[0]+"'"
            continue
        layer = layer()
        layer.fields = serialized[1]
        if deserialized is None:
            deserialized = layer
        else:
            deserialized = deserialized / layer
    return deserialized

PacketList.jsondump = dump_packet_as_json_str
Packet.jsondump = dump_packet_as_json_str

import unittest
import os

class SerializeTest(unittest.TestCase):

    def test_dumps_json(self):
        expected_raw = [[["IP",{"src":"192.168.1.1"}],]]
        expected = json.dumps(expected_raw, ensure_ascii=False)
        actual = IP(src="192.168.1.1").jsondump()
        self.assertEqual(expected, actual)

    def test_loads_json(self):
        t1 = Ether()/IP(src="192.168.1.1")/TCP(dport=80,flags="S")
        t1_json = t1.jsondump()
        json_loaded = json.loads(t1_json)[0]
        t2 = _loads_json(json_loaded)
        self.assertEqual(t1, t2)
        self.assertIsInstance(t1, Packet)
        self.assertIsInstance(t2, Packet)

    def test_dump_and_load(self):
        t1 = Ether()/IP(src="192.168.1.1")/TCP(dport=80,flags="S")
        t2 = Ether()/IP(src="192.168.1.1")/TCP(dport=80,flags="S")
        tj1 = t1.jsondump()
        tj2 = t2.jsondump()
        tt1 = load_packets_from_json_str(tj1)
        tt2 = load_packets_from_json_str(tj2)
        self.assertEqual(tt1.res, tt2.res)
        self.assertIsInstance(tt1, PacketList)
        self.assertIsInstance(tt2, PacketList)

    def test_packetlist(self):
        t1 = PacketList([
            Ether()/IP(src="192.168.1.1")/TCP(dport=81,flags="S"),
            Ether()/IP(src="192.168.2.1")/TCP(dport=82,flags="SA"),
            Ether()/IP(src="192.168.3.1")/TCP(dport=83,flags="A"),
        ])
        t2 = PacketList([
            Ether()/IP(src="192.168.1.1")/TCP(dport=81,flags="S"),
            Ether()/IP(src="192.168.2.1")/TCP(dport=82,flags="SA"),
            Ether()/IP(src="192.168.3.1")/TCP(dport=83,flags="A"),
        ])
        tj1 = t1.jsondump()
        tj2 = t2.jsondump()
        tt1 = load_packets_from_json_str(tj1)
        tt2 = load_packets_from_json_str(tj2)
        self.assertEqual(tt1.res, tt2.res)
        self.assertIsInstance(tt1, PacketList)
        self.assertIsInstance(tt2, PacketList)
        for i in range(3):
            self.assertEqual(tt1[i], tt2[i])

    def test_file(self):
        FILE1 = "testSerialize1"
        FILE2 = "testSerialize2"
        t1 = PacketList([
            Ether()/IP(src="192.168.1.1")/TCP(dport=81,flags="S"),
            Ether()/IP(src="192.168.2.1")/TCP(dport=82,flags="SA"),
            Ether()/IP(src="192.168.3.1")/TCP(dport=83,flags="A"),
        ])
        t2 = PacketList([
            Ether()/IP(src="192.168.1.1")/TCP(dport=81,flags="S"),
            Ether()/IP(src="192.168.2.1")/TCP(dport=82,flags="SA"),
            Ether()/IP(src="192.168.3.1")/TCP(dport=83,flags="A"),
        ])
        try:
            tj1 = t1.jsondump(FILE1)
            tj2 = t2.jsondump(FILE2)
            tt1 = load_packets_from_json_file(FILE1)
            tt2 = load_packets_from_json_file(FILE2)
        except Exception as e:
            raise e
        finally:
            os.remove(FILE1)
            os.remove(FILE2)
        self.assertEqual(tt1.res, tt2.res)
        self.assertIsInstance(tt1, PacketList)
        self.assertIsInstance(tt2, PacketList)

    def test_dnsqr(self):
        t1 = Ether()/IP()/DNS(opcode="QUERY", qd=DNSQR(qname='sip.cybercity.dk.', qtype="A", qclass="IN"))
        t1_json = t1.jsondump()
        json_loaded = json.loads(t1_json)[0]
        t2 = _loads_json(json_loaded)
        self.assertEqual(t1, t2)
        self.assertIsInstance(t1, Packet)
        self.assertIsInstance(t2, Packet)

if __name__ == "__main__":
    unittest.main()
