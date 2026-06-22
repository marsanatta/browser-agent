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


def test_json_stringified_api_key_masked():
    out = redact('{"api_key":"supersecretvalue","step":"click"}')
    assert "supersecretvalue" not in out
    assert MASK in out
    assert '"step":"click"' in out


def test_json_stringified_jwt_value_masked():
    out = redact('{"jwt":"eyJabc123.eyJdef456.sigGHI789"}')
    assert "eyJabc123" not in out
    assert "sigGHI789" not in out


def test_raw_jwt_masked():
    out = redact("the token is eyJhbGciOiJIUzI1Ni.eyJzdWIiOiIxMjM0.SflKxwRJSMeKKF2QT4")
    assert "eyJhbGci" not in out
    assert MASK in out


def test_aws_access_key_masked():
    out = redact("aws key AKIAIOSFODNN7EXAMPLE in config")
    assert "AKIAIOSFODNN7EXAMPLE" not in out
    assert MASK in out


def test_slack_token_masked():
    assert "xoxb-" not in redact("xoxb-123456789012-abcdEFGHijklMNOP")


def test_google_api_key_masked():
    assert "AIza" not in redact("AIzaSyA1234567890abcdefghijklmnopqrstuv")


def test_github_pat_fine_grained_masked():
    out = redact("github_pat_11ABCDE0Y0abcdefghij_KLMNOPQRSTUVWXYZ1234567890")
    assert "github_pat_" not in out


def test_pem_private_key_block_masked():
    pem = (
        "key:\n-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEpAIBAAKCAQEAabc123\nlinetwo456\n"
        "-----END RSA PRIVATE KEY-----\nrest"
    )
    out = redact(pem)
    assert "MIIEpAIBAAKCAQEAabc123" not in out
    assert "BEGIN RSA PRIVATE KEY" not in out
    assert "rest" in out


def test_bytes_value_decoded_and_masked():
    out = redact(b'{"api_key":"secretbytesvalue"}')
    assert "secretbytesvalue" not in out
    assert MASK in out


def test_bytearray_value_masked():
    out = redact(bytearray(b"Bearer eyJhbGci.payloadpart.sigpart"))
    assert "eyJhbGci" not in out


def test_undecodable_bytes_masked():
    out = redact(b"\xff\xfe\xfa\xfb")
    assert isinstance(out, str)


def test_prose_with_email_not_mangled_beyond_email():
    text = "Email alice@example.com about the page-2 results, then click Submit."
    out = redact(text)
    assert "alice@example.com" not in out
    assert "about the page-2 results, then click Submit." in out
