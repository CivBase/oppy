# Copyright 2014, 2015, Nik Kinkel
# See LICENSE for licensing information

'''
.. topic:: Details

    Crypto utility functions. Includes:

        - Constant time string comparisons
        - Wrappers around encryption/decryption operations
        - The "recognized" check for incoming cells
        - A couple methods for verifying TLS certificate properties (signatures
          and times)

'''
import hashlib
import hmac
import struct

from datetime import datetime
from itertools import izip

import OpenSSL

from Crypto.Cipher import AES
from Crypto.Util import asn1, Counter

from oppy.cell.cell import Cell
from oppy.cell.definitions import RECOGNIZED, EMPTY_DIGEST
from oppy.cell.fixedlen import EncryptedCell
from oppy.crypto.exceptions import UnrecognizedCell


def constantStrEqual(str1, str2):
    '''Do a constant-time comparison of str1 and str2, returning **True**
    if they are equal, **False** otherwise.

    Use built-in hmac.compare_digest if it's available, otherwise custom
    constant-time comparison.

    :param str str1: first string to compare
    :param str str2: second string to compare
    :returns: **bool** **True** if str1 == str2, **False** otherwise
    '''
    try:
        from hmac import compare_digest
        return compare_digest(str1, str2)
    # use our own constant time equality comparison if no stdlib version
    except ImportError:
        pass

    if len(str1) != len(str2):
        # we've already failed at this point, but loop through
        # all chars anyway
        res = 1
        comp1 = bytearray(str2)
        comp2 = bytearray(str2)
    else:
        res = 0
        comp1 = bytearray(str1)
        comp2 = bytearray(str2)
    
    for a, b in izip(comp1, comp2):
        res |= a ^ b

    return res == 0


def constantStrAllZero(s):
    '''Check if *s* consists of all zero bytes.

    :param str s: string to check
    :returns: **bool** **True** if *s* contains all zero bytes, **False**
        otherwise
    '''
    return constantStrEqual(s, '\x00' * len(s))


def makeAES128CTRCipher(key, initial_value=0):
    '''Create and return a new AES128-CTR cipher instance.

    :param str key: key to use for this cipher
    :param initial_value: initial_value to use
    :returns: **Crypto.Cipher.AES.AES**
    '''
    ctr = Counter.new(128, initial_value=initial_value)
    return AES.new(key, AES.MODE_CTR, counter=ctr)


def makeHMACSHA256(msg, key):
    '''Make a new HMAC-SHA256 with *msg* and *key* and return digest byte
    string.

    :param str msg: msg
    :param str key: key to use
    :returns: **str** HMAC digest
    '''
    t = hmac.new(msg=msg, key=key, digestmod=hashlib.sha256)
    return t.digest()


def makePayloadWithDigest(payload, digest=EMPTY_DIGEST):
    '''Make a new payload with *digest* inserted in the correct position.

    :param str payload: payload in which to insert digest
    :param str digest: digest to insert
    :returns: **str** payload with digest inserted into correct position
    '''
    DIGEST_START = 5
    DIGEST_END = 9
    return payload[:DIGEST_START] + digest + payload[DIGEST_END:]


def encryptCellToTarget(cell, crypt_path, target=2, early=False):
    '''Encrypt *cell* to the *target* relay in *crypt_path* and update
    the appropriate forward digest.

    :param cell cell: cell to encrypt
    :param list crypt_path: list of RelayCrypto instances available for
        encryption
    :param int target: target node to encrypt to
    :param bool early: if **True**, use a RELAY_EARLY cmd instead of a
        RELAY cmd
    :returns: **oppy.cell.fixedlen.EncryptedCell**
    '''
    assert target >= 0 and target < len(crypt_path)
    assert cell.rheader.digest == EMPTY_DIGEST

    # 1) update f_digest with cell payload bytes
    crypt_path[target].forward_digest.update(cell.getPayload())
    # 2) insert first four bytes into new digest position
    cell.rheader.digest = crypt_path[target].forward_digest.digest()[:4]
    # 3) encrypt payload
    payload = cell.getPayload()
    for node in xrange(target + 1):
        payload = crypt_path[node].forward_cipher.encrypt(payload)
    # 4) return encrypted relay cell with new payload
    return EncryptedCell.make(cell.header.circ_id, payload, early=early)


def cellRecognized(payload, relay_crypto):
    '''Return **True** if this payload is *recognized*.

    .. note:: See tor-spec Section 6.1 for details about what it means for a
        cell to be *recognized*.

    :param str payload: payload to check if recognized
    :param oppy.crypto.relaycrypto.RelayCrypto relay_crypto: RelayCrypto
        instance to use for checking if payload is recognized
    :returns: **bool** **True** if this payload is recognized, **False**
        otherwise
    '''
    test_payload = payload
    recognized = test_payload[2:4]
    digest = test_payload[5:9]
    test_payload = makePayloadWithDigest(test_payload)

    if recognized != RECOGNIZED:
        return False

    test_digest = relay_crypto.backward_digest.copy()
    test_digest.update(test_payload)
    # no danger of timing attack here since we just
    # drop the cell if it's not recognized
    return test_digest.digest()[:4] == digest


def decryptCellUntilRecognized(cell, crypt_path, origin=2):
    '''Decrypt *cell* until it is recognized or we've tried all RelayCrypto's
    in *crypt_path*.

    Attempt to decrypt the cell one hop at a time. Stop if the cell is
    recognized. Raise an exception if the cell is not recognized at all.

    :param cell cell: cell to decrypt
    :param list, oppy.crypto.relaycrypto.RelayCrypto crypt_path: list of
        RelayCrypto instances to use for decryption
    :param int origin: the originating hop we think this cell came from
    :returns: the concrete RelayCell type of this decrypted cell
    '''
    assert 0 <= origin <= 2, 'We can only handle 3-hop paths'

    recognized = False
    payload = cell.getPayload()
    for node in xrange(len(crypt_path)):
        relay_crypto = crypt_path[node]
        payload = relay_crypto.backward_cipher.decrypt(payload)
        if cellRecognized(payload, relay_crypto):
            recognized = True
            origin = node
            break

    if recognized:
        updated_payload = makePayloadWithDigest(payload)
        crypt_path[origin].backward_digest.update(updated_payload)
        if cell.header.link_version < 4:
            cid = struct.pack('!H', cell.header.circ_id)
        else:
            cid = struct.pack('!I', cell.header.circ_id)
        cmd = struct.pack('!B', cell.header.cmd)

        dec = Cell.parse(cid + cmd + payload)
        return (dec, origin)
    else:
        raise UnrecognizedCell()


def verifyCertSig(id_cert, cert_to_verify, algo='sha1'):
    '''Verify that the SSL certificate *id_cert* has signed the TLS cert
    *cert_to_verify*.

    :param id_cert: Identification Certificate
    :type id_cert: OpenSSL.crypto.X509
    :param cert_to_verify: certificate to verify signature on
    :type cert_to_verify: OpenSSL.crypto.X509
    :param algo: algorithm to use for certificate verification
    :type algo: str

    :returns: **bool** **True** if the signature of *cert_to_verify* can be
        verified from *id_cert*, **False** otherwise
    '''
    cert_to_verify_ASN1 = OpenSSL.crypto.dump_certificate(
                                OpenSSL.crypto.FILETYPE_ASN1, cert_to_verify)

    der = asn1.DerSequence()
    der.decode(cert_to_verify_ASN1)
    cert_to_verify_DER = der[0]
    cert_to_verify_ALGO = der[1]
    cert_to_verify_SIG = der[2]

    sig_DER = asn1.DerObject()
    sig_DER.decode(cert_to_verify_SIG)

    sig = sig_DER.payload

    # first byte is number of unused bytes. should be zero
    assert sig[0] == '\x00'
    sig = sig[1:]

    try:
        OpenSSL.crypto.verify(id_cert, sig, cert_to_verify_DER, algo)
        return True
    except OpenSSL.crypto.Error:
        return False


# XXX should we check that the time is not later than the current time?
def validCertTime(cert):
    '''Verify that TLS certificate *cert*'s time is not earlier than
    cert.notBefore and not later than cert.notAfter.

    :param OpenSSL.crypto.X509 cert: TLS Certificate to verify times of
    :returns: **bool** **True** if cert.notBefore < now < cert.notAfter,
        **False** otherwise
    '''
    now = datetime.now()
    validAfter = datetime.strptime(cert.get_notBefore(), '%Y%m%d%H%M%SZ')
    validUntil = datetime.strptime(cert.get_notAfter(), '%Y%m%d%H%M%SZ')
    return validAfter < now < validUntil
