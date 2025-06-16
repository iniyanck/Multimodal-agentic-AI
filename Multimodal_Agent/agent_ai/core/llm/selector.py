import json
import os
import importlib

class LLMSelector:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'llm_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.llms = self.config['llms']
        self.default = self.config.get('default', list(self.llms.keys())[0])

    def get_llm_choice(self):
        # Use config file only, no prompt
        llm_name = self.config.get('default', list(self.llms.keys())[0])
        return llm_name, self.llms[llm_name]

    def get_llm_client(self, llm_name, llm_info):
        provider = llm_info['provider']
        model = llm_info['model']
        api_key = llm_info['api_key']
        if provider == 'google':
            genai = importlib.import_module('google.generativeai')
            genai.configure(api_key=api_key)
            return genai.GenerativeModel(model)
        elif provider == 'openai':
            openai = importlib.import_module('openai')
            class OpenAIClient:
                def generate_content(self, contents, generation_config=None):
                    prompt = contents[0] if isinstance(contents, list) else contents
                    response = openai.ChatCompletion.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        api_key=api_key
                    )
                    return type('obj', (object,), {'text': response['choices'][0]['message']['content']})
            return OpenAIClient()
        elif provider == 'anthropic':
            anthropic = importlib.import_module('anthropic')
            class AnthropicClient:
                def generate_content(self, contents, generation_config=None):
                    prompt = contents[0] if isinstance(contents, list) else contents
                    client = anthropic.Anthropic(api_key=api_key)
                    response = client.messages.create(
                        model=model,
                        max_tokens=1024,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return type('obj', (object,), {'text': response.content[0].text})
            return AnthropicClient()
        else:
            raise ValueError(f"Unknown provider: {provider}")
