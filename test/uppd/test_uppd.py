from uppd import set_version

# def test_candidate():
#     assert candidate("foo>=1.2.3,!= 1.6,<=2")
#     assert candidate("foo==2")
#     assert not candidate("foo===2")
#     assert not candidate("foo>=2")
#     assert candidate("foo<=2")


def test_set_version():
    assert set_version(specifier="==0", version="1", match_operators=["=="]) == "==1"