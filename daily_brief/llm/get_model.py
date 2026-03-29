from langchain_core.messages import HumanMessage
from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

load_dotenv()

def get_model(provider: str = 'ollama'):
    model = ChatOllama(model="qwen3.5:cloud", format="json")
    if provider == 'groq':
        model = ChatGroq(model="openai/gpt-oss-120b")
    
    return model

if __name__ == "__main__":
    model = get_model('ollama')
    messages = [HumanMessage(content="Hello!")]
    result = model.invoke(messages)
    print(result)