import os
from langchain.llms import OpenAI
from agent.utils.common import error_return, success_return
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from string import Template



prompt = PromptTemplate(
    input_variables=["product"],
    template="What is a good name for a company that makes {product}?",
)

llm = OpenAI(temperature=0)

tools = load_tools([ "llm-math"], llm=llm)

agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)


class LangchainService:
    llm: None

    def __init__(self) -> None:
        self.llm = OpenAI(temperature=0.9)

    def get_suggestion(self, text):
        data = self.llm(text)
        return success_return(data)

    def get_suggestion_by_prompt(self, text):
        prompt = PromptTemplate(
            input_variables=["product"],
            template="What is a good name for a company that makes {product}?"
        )
        return success_return(prompt.format(product=text))

    def get_s(self, text):
        chain = LLMChain(llm=self.llm, prompt=prompt)
        chain.run(text)

    def get_bot(self, name):
        pass

    def upsert_knowledge(self, url, name, is_local):

        pass
