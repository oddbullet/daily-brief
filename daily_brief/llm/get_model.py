from langchain_core.messages import HumanMessage
from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openrouter import ChatOpenRouter
from dotenv import load_dotenv

load_dotenv()

def get_model(provider: str = 'ollama'):
    model = ChatOllama(model="gpt-oss:120b-cloud", reasoning='high')
    if provider == 'groq':
        model = ChatGroq(model="openai/gpt-oss-120b")
    
    if provider == 'openrouter':
        model = ChatOpenRouter(model="qwen/qwen3.6-plus:free")
    
    return model

if __name__ == "__main__":
    model = get_model('ollama')
    messages = [HumanMessage(content="Hello!")]
    result = model.invoke(messages)
    print(result)