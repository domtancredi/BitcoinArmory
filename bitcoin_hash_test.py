# -*- Mode: Python -*-

import struct
import hashlib

sha256 = hashlib.sha256

block_135687 = (
    '01000000eb10c9a996a2340a4d74eaab41421ed8664aa49d18538bab59010000000000005a2f06efa9f2bd804f17877537f2080030cadbfa1eb50e02338117cc'
    '604d91b9b7541a4ecfbb0a1a64f1ade70301000000010000000000000000000000000000000000000000000000000000000000000000ffffffff0804cfbb0a1a'
    '02360affffffff0100f2052a01000000434104c2239c4eedb3beb26785753463be3ec62b82f6acd62efb65f452f8806f2ede0b338e31d1f69b1ce449558d7061'
    'aa1648ddc2bf680834d3986624006a272dc21cac000000000100000003e8caa12bcb2e7e86499c9de49c45c5a1c6167ea4b894c8c83aebba1b6100f343010000'
    '008c493046022100e2f5af5329d1244807f8347a2c8d9acc55a21a5db769e9274e7e7ba0bb605b26022100c34ca3350df5089f3415d8af82364d7f567a6a297f'
    'cc2c1d2034865633238b8c014104129e422ac490ddfcb7b1c405ab9fb42441246c4bca578de4f27b230de08408c64cad03af71ee8a3140b40408a7058a1984a9'
    'f246492386113764c1ac132990d1ffffffff5b55c18864e16c08ef9989d31c7a343e34c27c30cd7caa759651b0e08cae0106000000008c4930460221009ec9aa'
    '3e0caf7caa321723dea561e232603e00686d4bfadf46c5c7352b07eb00022100a4f18d937d1e2354b2e69e02b18d11620a6a9332d563e9e2bbcb01cee559680a'
    '014104411b35dd963028300e36e82ee8cf1b0c8d5bf1fc4273e970469f5cb931ee07759a2de5fef638961726d04bd5eb4e5072330b9b371e479733c942964bb8'
    '6e2b22ffffffff3de0c1e913e6271769d8c0172cea2f00d6d3240afc3a20f9fa247ce58af30d2a010000008c493046022100b610e169fd15ac9f60fe2b507529'
    '281cf2267673f4690ba428cbb2ba3c3811fd022100ffbe9e3d71b21977a8e97fde4c3ba47b896d08bc09ecb9d086bb59175b5b9f03014104ff07a1833fd8098b'
    '25f48c66dcf8fde34cbdbcc0f5f21a8c2005b160406cbf34cc432842c6b37b2590d16b165b36a3efc9908d65fb0e605314c9b278f40f3e1affffffff0240420f'
    '00000000001976a914adfa66f57ded1b655eb4ccd96ee07ca62bc1ddfd88ac007d6a7d040000001976a914981a0c9ae61fa8f8c96ae6f8e383d6e07e77133e88'
    'ac00000000010000000138e7586e0784280df58bd3dc5e3d350c9036b1ec4107951378f45881799c92a4000000008a47304402207c945ae0bbdaf9dadba07bdf'
    '23faa676485a53817af975ddf85a104f764fb93b02201ac6af32ddf597e610b4002e41f2de46664587a379a0161323a85389b4f82dda014104ec8883d3e4f7a3'
    '9d75c9f5bb9fd581dc9fb1b7cdf7d6b5a665e4db1fdb09281a74ab138a2dba25248b5be38bf80249601ae688c90c6e0ac8811cdb740fcec31dffffffff022f66'
    'ac61050000001976a914964642290c194e3bfab661c1085e47d67786d2d388ac2f77e200000000001976a9141486a7046affd935919a3cb4b50a8a0c233c286c'
    '88ac00000000'
    ).decode ('hex_codec')

# from caesure/bitcoin.py.

def dhash (s):
    return sha256(sha256(s).digest()).digest()

# used to keep track of the parsing position when cracking packets
class position:
    def __init__ (self, val=0):
        self.val = val
    def __int__ (self):
        return self.val
    def __index__ (self):
        return self.val
    def incr (self, delta):
        self.val += delta
    def __repr__ (self):
        return '<pos %d>' % (self.val,)

# like struct.unpack_from, but it updates <position> as it reads
def unpack_pos (format, data, pos):
    result = struct.unpack_from (format, data, pos)
    pos.incr (struct.calcsize (format))
    return result

def unpack_var_int (d, pos):
    n0, = unpack_pos ('<B', d, pos)
    if n0 < 0xfd:
        return n0
    elif n0 == 0xfd:
        n1, = unpack_pos ('<H', d, pos)
        return n1
    elif n0 == 0xfe:
        n2, = unpack_pos ('<I', d, pos)
        return n2
    elif n0 == 0xff:
        n3, = unpack_pos ('<Q', d, pos)
        return n3

def unpack_block (data, pos=None):
    if pos is None:
        pos = position()
    version, prev_block, merkle_root, timestamp, bits, nonce = unpack_pos ('<I32s32sIII', data, pos)
    if version != 1:
        raise ValueError ("unsupported block version: %d" % (version,))
    count = unpack_var_int (data, pos)
    transactions = []
    for i in range (count):
        transactions.append (unpack_tx (data, pos))
    return prev_block, merkle_root, timestamp, bits, nonce, transactions

def unpack_tx (data, pos):
    # has its own version number
    version, = unpack_pos ('<I', data, pos)
    if version != 1:
        raise ValueError ("unknown tx version: %d" % (version,))
    txin_count = unpack_var_int (data, pos)
    inputs = []
    outputs = []
    for i in range (txin_count):
        outpoint = unpack_pos ('<32sI', data, pos)
        script_length = unpack_var_int (data, pos)
        script = data[pos.val:pos.val+script_length]
        pos.incr (script_length)
        sequence, = unpack_pos ('<I', data, pos)
        inputs.append ((outpoint, script, sequence))
    txout_count = unpack_var_int (data, pos)
    for i in range (txout_count):
        value, = unpack_pos ('<Q', data, pos)
        pk_script_length = unpack_var_int (data, pos)
        pk_script = data[pos.val:pos.val+pk_script_length]
        pos.incr (pk_script_length)
        outputs.append ((value, pk_script))
    lock_time, = unpack_pos ('<I', data, pos)
    return inputs, outputs, lock_time

def hexify (s):
    return s.encode ('hex_codec')

class BLOCK:
    def __init__ (self, prev_block, merkle_root, timestamp, bits, nonce, transactions):
        self.prev_block = prev_block
        self.merkle_root = merkle_root
        self.timestamp = timestamp
        self.bits = bits
        self.nonce = nonce
        self.transactions = transactions

parts = unpack_block (block_135687)
b = BLOCK (*parts)

print 'prev_block', hexify (b.prev_block)
print 'merkle_root', hexify (b.merkle_root)
print 'timestamp', b.timestamp
print 'bits', b.bits
print 'nonce', b.nonce

for inputs, outputs, lock_time in b.transactions:

    print 'inputs:'
    for (outpoint, index), script, sequence in inputs:
        print hexify (outpoint), index, hexify (script), sequence

    print 'outputs:'
    for value, script in outputs:
        print value, hexify (script)

    print lock_time    

print 'block header', hexify (block_135687[:80])
block_hash = dhash (block_135687[:80])
print 'block header hash', hexify (block_hash)
print 'reversed (as on block explorer)', hexify (block_hash[::-1])

