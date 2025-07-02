from kiteconnect import KiteTicker, KiteConnect


def test_unpacked_values(kiteticker):
    data = b"\x00\x02\x00\x04test\x00\x05abcde"
    packets = kiteticker._split_packets(data)
    assert packets == [b"test", b"abcde"]
    assert kiteticker._unpack_int(b"\x00\x00\x00d", 0, 4) == 100


def test_is_connected_false(kiteticker):
    assert not kiteticker.is_connected()

