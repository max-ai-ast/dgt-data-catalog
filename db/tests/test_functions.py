import datetime


def _call(conn, expr: str):
    with conn.cursor() as cur:
        cur.execute(f"SELECT {expr}")
        return cur.fetchone()[0]


# --- clue.safe_to_date ---

def test_safe_to_date_valid(db):
    result = _call(db, "clue.safe_to_date('2024-01-15', 'YYYY-MM-DD')")
    assert result == datetime.date(2024, 1, 15)


def test_safe_to_date_null_input(db):
    assert _call(db, "clue.safe_to_date(NULL, 'YYYY-MM-DD')") is None


def test_safe_to_date_na_string(db):
    assert _call(db, "clue.safe_to_date('NA', 'YYYY-MM-DD')") is None


def test_safe_to_date_empty_string(db):
    assert _call(db, "clue.safe_to_date('', 'YYYY-MM-DD')") is None


def test_safe_to_date_invalid_string(db):
    assert _call(db, "clue.safe_to_date('not-a-date', 'YYYY-MM-DD')") is None


# --- clue.safe_json ---

def test_safe_json_valid(db):
    result = _call(db, """clue.safe_json('{"key": "value"}')""")
    assert result == {"key": "value"}


def test_safe_json_null_input(db):
    assert _call(db, "clue.safe_json(NULL)") is None


def test_safe_json_na_string(db):
    assert _call(db, "clue.safe_json('NA')") is None


def test_safe_json_empty_string(db):
    assert _call(db, "clue.safe_json('')") is None


def test_safe_json_invalid_string(db):
    assert _call(db, "clue.safe_json('not-json')") is None


# --- clue.nullif_na ---

def test_nullif_na_returns_null_for_na(db):
    assert _call(db, "clue.nullif_na('NA')") is None


def test_nullif_na_returns_null_for_empty(db):
    assert _call(db, "clue.nullif_na('')") is None


def test_nullif_na_passes_through_real_value(db):
    assert _call(db, "clue.nullif_na('some value')") == "some value"


# --- clue.extract_court_from_filename ---

def test_extract_court_from_filename_matching(db):
    result = _call(
        db,
        "clue.extract_court_from_filename('2024_Allegany County Circuit Court.csv')",
    )
    assert result == "Allegany County Circuit Court"


def test_extract_court_from_filename_no_match(db):
    result = _call(db, "clue.extract_court_from_filename('unrecognized_file.csv')")
    assert result == "Unknown Court"


# --- clue.calculate_file_hash ---

def test_calculate_file_hash_returns_md5(db):
    import hashlib
    content = "test content"
    expected = hashlib.md5(content.encode()).hexdigest()
    result = _call(db, f"clue.calculate_file_hash('{content}')")
    assert result == expected
