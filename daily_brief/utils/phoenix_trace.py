def setup_tracing():
    try:
        from phoenix.otel import register
        register(
            project_name="daily-brief",
            protocol="http/protobuf",
            auto_instrument=True
        )
    except ImportError:
        pass  # Phoenix is an optional dep — silently skip when not installed
