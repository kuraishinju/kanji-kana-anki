from project import view_score, valid_choice, validate_user, validate_username, fetch_id, check_kanji, parse_kanji

def test_validate_username():
    assert validate_username("Franco") == True
    assert validate_username("1") == False
    assert validate_username("Hello!!!") == False
    assert validate_username("asdfghjklim") == False

def test_validate_user():
    assert validate_user("Marga") == True
    assert validate_user("Gina") == True
    assert validate_user("Luna") == True
    assert validate_user("Franco") == False

def test_view_score():
    assert view_score(1, "Marga") == "Marga has 30 total points with 100% correct answers in 1 game total."
    assert view_score(2, "Gina") == "Gina has 25 total points with 88% correct answers in 2 games total."
    assert view_score(3, "Luna") == "No scores to view."

def test_fetch_id():
    assert fetch_id("Marga") == 1
    assert fetch_id("Gina") == 2
    assert fetch_id("Luna") == 3

def test_valid_choice():
    assert valid_choice(1) == True
    assert valid_choice(5) == False
    assert valid_choice(3) == True
    assert valid_choice(0) == False

def test_check_kanji():
    assert check_kanji("終わり") == True
    assert check_kanji("タバコ") == False
    assert check_kanji("まわり") == False

def test_parse_kanji():
    assert parse_kanji("けいけん・する") == "けいけん"
    assert parse_kanji("いえ") == "いえ"
