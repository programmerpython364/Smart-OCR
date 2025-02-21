from dotenv import load_dotenv
import os
import google.generativeai as genai
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationSummaryBufferMemory
from langchain.llms.base import LLM
from langchain_core.output_parsers import StrOutputParser


load_dotenv()
token = os.getenv("AI_API_TOKEN")
genai.configure(api_key=token)


class GeminiLLM(LLM):
    model: str = "gemini-1.5-flash"  # 
    temperature: float = 0.8

    def _call(self, prompt: str, stop=None) -> str:

        model = genai.GenerativeModel(self.model)
        response = model.generate_content(prompt)
        return response.text if response else "لم أتمكن من إنشاء استجابة."

    @property
    def _llm_type(self) -> str:
        return "Gemini"
    
def chat_with_video(question, chain, memory):
    history = memory.load_memory_variables({}).get("history", "")
    response = chain.invoke({"history": history, "question": question})
    memory.save_context({"question": question}, {"output": response})
    return response

def initialize_llm():
    llm = GeminiLLM()
    
    memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=4096)
    
    prompt = PromptTemplate(
        input_variables=["history", "question"],
        template="""You are a helpful and kind AI. Your answers are not tall.
        Conversation history:
        {history}
        Human: {question}
        AI:"""
    )
    
    chain = prompt | llm | StrOutputParser()
    
    return chain, memory
    
    
    
    