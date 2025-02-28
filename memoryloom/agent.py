
import os
import re
import json
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
            response = self.extract_json(response)
            obj = self.response.model_validate_json(response)
            return obj
        except Exception as e:
            logger.error(str(e))
            return None

    @abstractmethod
    def get_prompt(self, input: Message|str, history: list[Message]|str):
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

    def extract_json(self, text: str):
        try:
            if json.loads(text):
                return [text]
        except json.JSONDecodeError:
                pass
        
        pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        matches = re.findall(pattern, text, re.DOTALL)
        return matches

class RecordResponse(BaseModel):
    think:str = Field(..., description="思考过程")
    record:list[str] = Field(..., description="记录内容")

class RecordAgent(BaseAgent):
    def __init__(self, ai_caller: AICaller, 
                 prompt: str = None,
                 prompt_type: Literal["text", "chat"] = None,
                 prompt_id: str = None,):
        super().__init__(ai_caller, prompt, prompt_type, prompt_id)
        self.response = RecordResponse

    def get_agent_name(self):
        return "record"
    
    def cls_prompt(self):
        self.__prompt_id__ = "record"
        self.__prompt_type__ = "chat"
        self.__prompt__ = [
            {"role": "system", "content": """你是一个记录助手，无论用户说什么，你的工作都是将用户的话归纳总结。
             要求如下：
             1. 你最好能够站在 [{{user}}] 的视角，来总结出发生了什么事，但如果[]中为空或是其它无意义的值，就忽略这个要求。
             2. 总结需准确传达原文核心观点和关键细节，内容完整且重点突出。语言简洁明了，逻辑连贯，避免添加主观臆断和无关信息。
             3. 当用户信息为空或者其它无意义的值时，输出记录可以为空的list。
             4. 如果只用一条记录无法涵盖所有重要信息，可以给出多条记录。
             5. 最后输出的格式请按照这个json schema输出：
             {{output_schema}}"""},
            {"role": "user", "content": "{{input_history}}"}
        ]
    
    def get_prompt(self, record: Message|str, user_name:str=""):
        prompt = self.langfuse_client.get_prompt(self.prompt_id)
        compiled_prompt = prompt.compile(
            input_history = self.process_history(record),
            user = user_name,
            output_schema = self.response.model_json_schema()
        )
        return compiled_prompt

class SummaryResponse(BaseModel):
    think:str = Field(..., description="思考过程")
    summary:str = Field(..., description="总结内容")

class SummaryAgent(BaseAgent):
    def __init__(self, ai_caller: AICaller, 
                 prompt: str = None,
                 prompt_type: Literal["text", "chat"] = None,
                 prompt_id: str = None,):
        super().__init__(ai_caller, prompt, prompt_type, prompt_id)
        self.response = SummaryResponse

    def get_agent_name(self):
        return "summary"
    
    def cls_prompt(self):
        self.__prompt_id__ = "summmary"
        self.__prompt_type__ = "chat"
        self.__prompt__ = [
            {"role": "system", "content": """你是一个内容归纳助手，无论用户说什么，你的工作都是将用户的话归纳总结为一段文本。
             要求如下：
             1. 总结需准确传达原文核心观点和关键细节，内容完整且重点突出。语言简洁明了，逻辑连贯，避免添加主观臆断和无关信息。
             2. 丢弃掉不重要的信息，总结更重要的信息。
             3. 最后输出的格式请按照这个json schema输出：
             {{output_schema}}"""},
            {"role": "user", "content": "{{input_history}}"}
        ]

    def get_prompt(self, origin_text:str):
        prompt = self.langfuse_client.get_prompt(self.prompt_id)
        compiled_prompt = prompt.compile(
            input_history = origin_text,
            output_schema = self.response.model_json_schema()
        )
        return compiled_prompt

if __name__ == "__main__":
    llm = AICaller(
        model_name=os.environ.get("LLM_MODEL"),
        api_token=os.environ.get("LLM_API_KEY"),
        api_base=os.environ.get("LLM_API_BASE"),
        proxy=os.environ.get("LLM_PROXIES"),
    )
    recoder = RecordAgent(llm)
    res = recoder(record = "你好，我叫张三", user_name="张三")
    print(res)


