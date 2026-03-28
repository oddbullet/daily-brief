from langchain_core.messages import HumanMessage
from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

load_dotenv()

model: BaseChatModel = ChatGroq(model="openai/gpt-oss-120b")

def init_model(provider: str):
    global model

    if provider == 'ollama':
        model = ChatOllama(model="qwen3.5:9b", reasoning=False)

if __name__ == "__main__":
    init_model('ollama')
    messages = [HumanMessage(content="Hello!")]
    result = model.invoke(messages)
    print(result)