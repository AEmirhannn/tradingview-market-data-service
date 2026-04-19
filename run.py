from tradingview_service import create_app
from tradingview_service.runtime import configure_runtime_env


configure_runtime_env()
app = create_app()


if __name__ == "__main__":
    config = app.config["APP_CONFIG"]
    app.run(host=config.host, port=config.port, load_dotenv=False)
