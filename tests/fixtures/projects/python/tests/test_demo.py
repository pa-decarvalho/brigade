import demo  # ty: ignore[import-not-found]  # its own project, not brigade's


def test_hello():
    assert demo.hello()
