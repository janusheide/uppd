from uppd import candidate


def test_candidate():
    assert candidate("foo==2")
    assert not candidate("foo===2")
    assert not candidate("foo>=2")
    assert not candidate("foo<=2")


