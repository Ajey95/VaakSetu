from app.config import AppMode, Settings


def test_synthetic_mode_reports_missing_provider_credentials_without_blocking_startup():
    settings = Settings(app_mode=AppMode.SYNTHETIC)

    report = settings.provider_readiness()

    assert report["twilio"].configured is False
    assert report["twilio"].blocking is False
    assert report["twilio"].mode == "synthetic"
    assert "TWILIO_ACCOUNT_SID" in report["twilio"].missing


def test_real_mode_marks_missing_telephony_credentials_as_blocking():
    settings = Settings(app_mode=AppMode.REAL)

    report = settings.provider_readiness()

    assert report["twilio"].configured is False
    assert report["twilio"].blocking is True
    assert report["stt"].blocking is True
    assert report["llm"].blocking is True


def test_optional_data_services_never_block_realtime_startup():
    settings = Settings(app_mode=AppMode.REAL)

    report = settings.provider_readiness()

    assert report["database"].blocking is False
    assert report["graph"].blocking is False
    assert report["external_data"].blocking is False


def test_official_uk_external_data_needs_no_general_search_key():
    settings = Settings(app_mode=AppMode.REAL, external_data_mode="real")
    readiness = settings.provider_readiness()["external_data"]
    assert readiness.configured is True
    assert readiness.mode == "official_uk"
    assert readiness.missing == ()
