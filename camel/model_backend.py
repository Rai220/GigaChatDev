# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
from abc import ABC, abstractmethod
from typing import Any, Dict

import openai
import uuid, os, json
import tiktoken
from langchain.chat_models import GigaChat, ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
import time
from langchain.adapters.openai import *

from camel.typing import ModelType
from chatdev.statistics import prompt_cost
from chatdev.utils import log_and_print_online

class Wrapper:
    def __init__(self, wrapped_class):
        self.wrapped_class = wrapped_class

    def __getattr__(self, attr):
        original_func = getattr(self.wrapped_class, attr)

        def wrapper(*args, **kwargs):
            print(f"Calling function: {attr}")
            print(f"Arguments: {args}, {json.dumps(kwargs, ensure_ascii=False)}")
            result = original_func(*args, **kwargs)
            print(f"Response: {json.dumps(result, ensure_ascii=False)}")
            # Пишем в массив json
            if attr == "create":
                with open(f"logs/{os.environ['LANGCHAIN_PROJECT']}.jsonl", "a", encoding="utf-8") as f:
                    to_write = {"request": kwargs, "response": result}
                    #f.write(str(json.dumps(kwargs, ensure_ascii=False)) + "\n")
                    #f.write(str(json.dumps(result, ensure_ascii=False)) + "\n")
                    # Write beautified json
                    to_write["request"]["api_key"] = "sk-..."
                    to_write["response"]["api_key"] = "sk-..."
                    f.write(str(json.dumps(to_write, ensure_ascii=False, indent=4)) + "\n")
            else:
                print(f"Unknown function: {attr}")
            return result

        return wrapper

class ModelBackend(ABC):
    r"""Base class for different model backends.
    May be OpenAI API, a local LLM, a stub for unit tests, etc."""

    @abstractmethod
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        r"""Runs the query to the backend model.

        Raises:
            RuntimeError: if the return value from OpenAI API
            is not a dict that is expected.

        Returns
            Dict[str, Any]: All backends must return a dict in OpenAI format.
        """
        pass


class OpenAIModel(ModelBackend):
    r"""OpenAI API in a unified ModelBackend interface."""

    def __init__(self, model_type: ModelType, model_config_dict: Dict) -> None:
        super().__init__()
        self.model_type = model_type
        self.model_config_dict = model_config_dict
        self.openai = ChatOpenAI(model=self.model_type.value, timeout=600)
        self.openai.client = Wrapper(self.openai.client)

    def run(self, *args, **kwargs) -> Dict[str, Any]:
        string = "\n".join([message["content"] for message in kwargs["messages"]])
        encoding = tiktoken.encoding_for_model(self.model_type.value)
        # encoding = tiktoken.encoding_for_model("cl100k_base")
        num_prompt_tokens = len(encoding.encode(string))
        gap_between_send_receive = 15 * len(kwargs["messages"])
        num_prompt_tokens += gap_between_send_receive

        num_max_token_map = {
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
            "gpt-3.5-turbo-0613": 4096,
            "gpt-3.5-turbo-16k-0613": 16384,
            "gpt-4": 8192,
            "gpt-4-0613": 8192,
            "gpt-4-32k": 32768,
            "gpt-4-1106-preview": 4096,
        }
        num_max_token = num_max_token_map[self.model_type.value]
        num_max_completion_tokens = num_max_token - num_prompt_tokens
        self.model_config_dict["max_tokens"] = num_max_completion_tokens
        for _ in range(1, 5):
            try:
                messages = convert_openai_messages(kwargs["messages"])
                # response = openai.ChatCompletion.create(
                #     *args,
                #     **kwargs,
                #     model=self.model_type.value,
                #     **self.model_config_dict
                # )
                resp = self.openai(messages)
                response = {
                    "id": uuid.uuid4().hex,
                    "choices": [
                        {
                            "message": convert_message_to_dict(resp),
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 1,
                        "completion_tokens": 1,
                        "total_tokens": 1,
                    },
                }

                if self.model_type.value == "gpt-4":
                    time.sleep(10)  # Cooldown, or limit exception
                break
            except Exception as e:
                log_and_print_online("OpenAI API Error: {}".format(e))
                time.sleep(60)

        cost = prompt_cost(
            self.model_type.value,
            0,  # num_prompt_tokens=response["usage"]["prompt_tokens"],
            0,  # num_completion_tokens=response["usage"]["completion_tokens"],
        )

        # log_and_print_online(
        #     "**[OpenAI_Usage_Info Receive]**\nprompt_tokens: {}\ncompletion_tokens: {}\ntotal_tokens: {}\ncost: ${:.6f}\n".format(
        #         response["usage"]["prompt_tokens"],
        #         response["usage"]["completion_tokens"],
        #         response["usage"]["total_tokens"],
        #         cost,
        #     )
        # )
        if not isinstance(response, Dict):
            raise RuntimeError("Unexpected return from OpenAI API")
        return response


class GigaModel(ModelBackend):
    r"""GigaChat API in a unified ModelBackend interface."""

    def __init__(self, model_type: ModelType, model_config_dict: Dict) -> None:
        super().__init__()
        self.model_type = model_type
        self.model_config_dict = model_config_dict
        self.giga = GigaChat(
            verify_ssl_certs=False,
            profanity=False,
            temperature=1.3,
            max_tokens=3000,
            base_url="http://10.18.144.130:8000",
            model="GigaR-29b-463k-24-mini-epoch5",
            timeout=1300,
            access_token="",
            verbose=True
        )

    def run(self, *args, **kwargs) -> Dict[str, Any]:
        args_messages = kwargs["messages"]
        # string = "\n".join([message["content"] for message in kwargs["messages"]])
        # encoding = tiktoken.encoding_for_model(self.model_type.value)
        # num_prompt_tokens = len(encoding.encode(string))
        # gap_between_send_receive = 15 * len(kwargs["messages"])
        # num_prompt_tokens += gap_between_send_receive

        # num_max_token_map = {
        #     "giga": 4096
        # }
        # num_max_token = num_max_token_map[self.model_type.value]
        # num_max_completion_tokens = num_max_token - num_prompt_tokens
        # self.model_config_dict['max_tokens'] = num_max_completion_tokens
        # retry_count = 0
        # for i in range(1, 5):
        try:
            # response = openai.ChatCompletion.create(*args, **kwargs,
            #                                     model=self.model_type.value,
            #                                     **self.model_config_dict)
            messages = []
            for m in args_messages:
                if m["role"] == "user":
                    messages.append(HumanMessage(content=m["content"]))
                elif m["role"] == "system":
                    messages.append(SystemMessage(content=m["content"]))
                elif m["role"] == "assistant":
                    messages.append(AIMessage(content=m["content"]))
            resp = self.giga(messages)

            # Rename <code> to ``` - ```
            content = resp.content.replace("<code>{python}", "```python").replace("</code>", "```")

            response = {
                "id": 1,
                "usage": {},
                "choices": [
                    {
                        "message": {"content": content, "role": "assistant"},
                        "finish_reason": "stop",
                    }
                ],
            }
        except Exception as e:
            log_and_print_online("GigaChat API Error: {}".format(e))

        # cost = prompt_cost(
        #         self.model_type.value,
        #         num_prompt_tokens=response["usage"]["prompt_tokens"],
        #         num_completion_tokens=response["usage"]["completion_tokens"]
        # )

        # log_and_print_online(
        #     "**[OpenAI_Usage_Info Receive]**\nprompt_tokens: {}\ncompletion_tokens: {}\ntotal_tokens: {}\ncost: ${:.6f}\n".format(
        #         response["usage"]["prompt_tokens"], response["usage"]["completion_tokens"],
        #         response["usage"]["total_tokens"], cost))
        # if not isinstance(response, Dict):
        #     raise RuntimeError("Unexpected return from OpenAI API")
        return response


class StubModel(ModelBackend):
    r"""A dummy model used for unit tests."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()

    def run(self, *args, **kwargs) -> Dict[str, Any]:
        ARBITRARY_STRING = "Lorem Ipsum"

        return dict(
            id="stub_model_id",
            usage=dict(),
            choices=[
                dict(
                    finish_reason="stop",
                    message=dict(content=ARBITRARY_STRING, role="assistant"),
                )
            ],
        )


class ModelFactory:
    r"""Factory of backend models.

    Raises:
        ValueError: in case the provided model type is unknown.
    """

    @staticmethod
    def create(model_type: ModelType, model_config_dict: Dict) -> ModelBackend:
        default_model_type = ModelType.GIGA

        if model_type in {
            ModelType.GPT_3_5_TURBO,
            ModelType.GPT_4,
            ModelType.GPT_4_32k,
            None,
        }:
            model_class = OpenAIModel
        elif model_type == ModelType.STUB:
            model_class = StubModel
        elif model_type == ModelType.GIGA:
            model_class = GigaModel
        else:
            raise ValueError("Unknown model")

        if model_type is None:
            model_type = default_model_type

        # log_and_print_online("Model Type: {}".format(model_type))
        inst = model_class(model_type, model_config_dict)
        return inst
