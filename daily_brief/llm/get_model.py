from langchain_core.messages import HumanMessage
from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openrouter import ChatOpenRouter
from dotenv import load_dotenv
import yaml

load_dotenv()

def _load_config() -> dict:
    with open("daily_brief/config.yaml", 'r') as file:
        try:
            return yaml.safe_load(file)
        except yaml.YAMLError as exc:
            raise RuntimeError(f"Failed to load config file: {exc}")

def _make_ollama(model_name: str):
    reasoning = "high" if "gpt-oss" in model_name else None
    return ChatOllama(model=model_name, reasoning=reasoning)

def _make_groq(model_name: str):
    reasoning = "high" if "gpt-oss" in model_name else None
    return ChatGroq(model=model_name, reasoning_effort=reasoning)

def _make_openrouter(model_name: str):
    return ChatOpenRouter(model=model_name, reasoning={"effort": "high", "summary": "auto"})

_FACTORIES = {
    'ollama': _make_ollama,
    'groq': _make_groq,
    'openrouter': _make_openrouter,
}

def get_model(provider: str = 'ollama') -> BaseChatModel:
    config = _load_config()

    factory = _FACTORIES.get(provider)
    if factory is None:
        raise ValueError(f"Unknown provider: {provider}")

    models_to_try = [config[provider]['model'], config[provider]['fallback']]
    for model_name in models_to_try:
        try:
            return factory(model_name)
        except Exception as e:
            print(f"Error loading {model_name}: {e}")

    raise RuntimeError(f"All {provider} models failed: {models_to_try}")

if __name__ == "__main__":
    provider = ['ollama', 'groq', 'openrouter']

    for p in provider:
        model = get_model(p)
        messages = [HumanMessage(content="Hello!")]
        result = model.invoke(messages)

        print(f"{p}: {result.content}")