from app.core.resolution.normalization import normalize_text, normalize_username


def test_normalize_text():
    assert normalize_text("Rahul Sharma!") == "rahulsharma"


def test_normalize_username():
    assert normalize_username("@Rahul_Dev23") == "rahuldev23"
