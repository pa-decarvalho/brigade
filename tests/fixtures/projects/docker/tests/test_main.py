import demo  # ty: ignore[import-not-found]  # its own project, not brigade's


def test_main(capsys):
    demo.main()
    assert capsys.readouterr().out == "Hello from demo!\n"
