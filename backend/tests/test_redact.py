from app.obs.tracing import redact

MASK = "[REDACTED]"


def test_openai_sk_key_masked():
    out = redact("key is sk-abc123DEF456ghijklmnop here")
    assert "sk-abc123" not in out
    assert MASK in out


def test_sk_proj_and_ant_variants_masked():
    assert "sk-proj-" not in redact("sk-proj-AbCd1234EfGh5678ij")
    assert "sk-ant-" not in redact("sk-ant-api03-XyZ9876543210abcd")


def test_bearer_token_masked():
    out = redact("Bearer eyJhbGciOiJIUzI1Ni1234567890abcdef")
    assert "eyJhbGci" not in out
    assert out.startswith("Bearer " + MASK)


def test_authorization_header_masked():
    out = redact("Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cC06abcdef")
    assert "eyJhbGci" not in out
    assert MASK in out


def test_cookie_header_masked():
    out = redact("Cookie: session=deadbeefcafebabe; theme=dark")
    assert "deadbeefcafebabe" not in out
    assert MASK in out


def test_set_cookie_header_masked():
    out = redact("Set-Cookie: sid=abc123secretvalue; HttpOnly")
    assert "abc123secretvalue" not in out
    assert MASK in out


def test_api_key_query_param_masked():
    out = redact("https://x.com/v1?api_key=supersecret123&page=2")
    assert "supersecret123" not in out
    assert "page=2" in out


def test_access_token_param_masked():
    out = redact("access_token=ya29.A0ARrdaM-secret-value")
    assert "ya29.A0ARrdaM-secret-value" not in out
    assert MASK in out


def test_github_token_masked():
    assert "gho_" not in redact("token gho_16C7e42F292c6912E7710c838347Ae178B4a")


def test_email_pii_masked():
    out = redact("contact jane.doe+test@example.co.uk for access")
    assert "jane.doe" not in out
    assert "@example" not in out
    assert MASK in out


def test_normal_text_untouched():
    text = "The agent clicked the Submit button on page 2 and waited 300ms."
    assert redact(text) == text


def test_normal_text_with_numbers_and_urls_untouched():
    text = "Navigated to https://books.toscrape.com/catalogue/page-3.html ok"
    assert redact(text) == text


def test_dict_secret_key_value_masked():
    out = redact({"Authorization": "Bearer abc.def.ghi", "step": "click"})
    assert out["Authorization"] == MASK
    assert out["step"] == "click"


def test_dict_token_key_masked_even_opaque_value():
    out = redact({"api_key": "OPAQUEnoPatternMatch", "ok": "fine"})
    assert out["api_key"] == MASK
    assert out["ok"] == "fine"


def test_nested_structure_masked():
    payload = {
        "headers": {"Cookie": "sid=topsecret999"},
        "items": ["sk-deadbeef12345678", "harmless"],
        "user": "alice@corp.example",
    }
    out = redact(payload)
    assert out["headers"]["Cookie"] == MASK
    assert "sk-deadbeef" not in out["items"][0]
    assert out["items"][1] == "harmless"
    assert "alice@corp.example" not in out["user"]


def test_authorization_with_inline_sk_fully_masked():
    out = redact("Authorization: sk-shouldNotLeak12345678")
    assert "sk-shouldNotLeak" not in out


def test_non_string_scalars_passthrough():
    assert redact(42) == 42
    assert redact(True) is True
    assert redact(None) is None
