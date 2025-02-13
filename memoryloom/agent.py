from langfuse import Langfuse
from memoryloom.AlCaller import AICaller
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from typing import Literal, Optional
from memoryloom.message import Message
from memoryloom.logger import get_logger

logger = get_logger()

class BaseAgent(ABC):
    def __init__(self, ai_caller: AICaller, 
                 prompt: str = None,
                 prompt_type: Literal["text", "chat"] = None,
                 prompt_id: str = None,):
        self.llm = ai_caller
        self.langfuse_client = Langfuse()
        self.response = BaseModel
        self.agent_name = self.get_agent_name()
        self.prompt_id = self.agent_name

        self.cls_prompt()
        self.prompt_settings(prompt_id=prompt_id, prompt_type=prompt_type, prompt=prompt)
        self.init_prompt()
    
    @abstractmethod
    def get_agent_name(self):
        return "base"

    def process_history(self, history: list[Message]|str):
        if isinstance(history, str):
            return history
        else:
            history_str = "\n\n".join([f"{item.name}: {item.content}" for item in history])
            return history_str

    def validate_response(self, response: str):
        try:
            obj = self.response.model_validate_json(response)
            return obj
        except Exception as e:
            logger.error(str(e))
            return None

    @abstractmethod
    def get_prompt(self,input: Message|str, history: list[Message]|str):
        prompt = self.langfuse_client.get_prompt(self.prompt_id)
        compiled_prompt = prompt.compile(
            history = self.process_history(history),
            user_message = input if type(input) is str else str(input),
            output_schema = self.response.model_json_schema()
        )
        return compiled_prompt

    def generate(self, log_name:str="base", *args, **kwargs):
        prompt = self.langfuse_client.get_prompt(self.prompt_id)
        compiled_prompt = self.get_prompt(*args, **kwargs)
        
        generation = self.langfuse_client.generation(
            name=log_name,
            model=self.llm.model,
            input=compiled_prompt,
            prompt=prompt
        )
        output = self.call_llm(compiled_prompt)
        generation.end(output=output)
        return output
    
    def __call__(self, *args, **kwargs):
        return self.generate(log_name=self.agent_name, *args, **kwargs)
    
    def call_llm(self, prompt, max_tries=3):
        tries = 0
        output = None
        while tries < max_tries and output is None:
            response = self.llm.chat(prompt, stream=False)
            output = self.validate_response(response)
            tries += 1
        return output

    @abstractmethod
    def cls_prompt(self):
        self.__prompt_id__ = self.agent_name
        self.__prompt_type__ = "text"
        self.__prompt__ = "You are a helpful assistant."

    def prompt_settings(self, prompt_id: str=None,
                        prompt_type: Literal["text", "chat"]=None,
                        prompt: str=None):
        
        self.__prompt_id__ = self.__prompt_id__ if prompt_id is None else prompt_id
        self.__prompt_type__ = self.__prompt_type__ if prompt_type is None else prompt_type
        self.__prompt__ = self.__prompt__ if prompt is None else prompt


    def init_prompt(self):
        try:
            self.langfuse_client.get_prompt(self.prompt_id)
        except:
            self.langfuse_client.create_prompt(
                name=self.__prompt_id__,
                type=self.__prompt_type__,
                prompt=self.__prompt__,
                labels=["production"]
            )
    
    def set_response(self, response: BaseModel):
        self.response = response

class DayAgent(BaseAgent):
    def get_agent_name(self):
        return "day"
    
    def cls_prompt(self):
        self.__prompt_id__ = "day"
        self.__prompt_type__ = "text"
        self.__prompt__ = """
"""
