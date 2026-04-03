from phoenix.otel import register

def setup_tracing():
    register(
        project_name="daily-brief",
        protocol="http/protobuf",
        auto_instrument=True
    )
