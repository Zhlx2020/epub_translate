import requests
import time
import random
import sys
import json

# 彩色日志输出工具函数（全部中文）
def log_info(msg):
    print(f"\033[92m[信息]\033[0m {msg}", flush=True)

def log_warn(msg):
    print(f"\033[93m[警告]\033[0m {msg}", flush=True)

def log_error(msg):
    print(f"\033[91m[错误]\033[0m {msg}", file=sys.stderr, flush=True)

def log_model(msg):
    print(f"\033[96m[模型]\033[0m {msg}", flush=True)

class NewApiTranslator:
    """
    支持从 JSON 文件读取所有参数的多模型自动切换翻译器
    """

    def __init__(self, key=None, language=None, api_base=None,encoding="utf-8",**kwargs):
        """
        :param config_json_path: 参数配置文件路径，内容为json格式。
        """
        # 读取JSON配置
        with open("config.json") as f:
            config = json.load(f)
        # 读取各参数（带默认值）
        self.key = config.get("key")
        self.language = config.get("language", "zh-hans")
        self.api_base = config.get("api_base", "https://miaogeapi.deno.dev/v1").rstrip("/")
        self.model = config.get("model", "openai-reasoning")
        self.temperature = config.get("temperature", 0.3)
        self.max_retries = config.get("max_retries", 3)
        self.model_pool = config.get("model_pool", [self.model])


        self.system_prompt = (
            "You are a professional translator specializing in Linux "
            "system administration, open-source software, and computer technology. Your task "
            "is to translate English technical content into accurate, professional, and "
            "modern Chinese.\n\n"
            "Translation guidelines:\n"
            "1. Keep technical terms, commands, system names, configuration items, file paths, shell scripts, and code snippets "
            "in their original form or use official/authoritative community standard translations. Do not invent new words or use phonetic transliterations.\n"
            "2. The translation should be clear, concise, and correct, making it easy for Chinese technical professionals to read and learn from.\n"
            "3. When there are multiple translations for a term, prefer those used in LDP, GNU, Debian, Arch Wiki, mainstream textbooks, and authoritative communities.\n"
            "4. Never translate configuration files, command-line parameters, code blocks, or output examples. Only translate and polish comments and explanatory text.\n"
            "5. For UI elements, menus, and buttons, use terminology from mainstream localized software.\n"
            "6. Preserve all original HTML tags and formatting.\n"
            "7. Output only the translated content, without any explanations or comments.\n"
            "8. Ensure consistency and professionalism throughout the entire translation."
        )
        self.success_count = 0
        self.fail_count = 0

    def translate(self, text):
        print(self.model_pool,self.api_base,self.language,self.temperature,self.key)
        """
        翻译单段文本，遇到错误自动切换模型，所有异常均捕获
        """
        for model_name in self.model_pool:
            for attempt in range(1, self.max_retries + 1):
                try:
                    log_model(f"当前使用模型: {model_name}，第 {attempt} 次尝试")
                    url = f"{self.api_base}/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {self.key}",
                        "Content-Type": "application/json"
                    }
                    # 构造API请求体
                    data = {
                        "model": model_name,
                        "temperature": self.temperature,
                        "messages": [
                            {"role": "system", "content": self.system_prompt},
                            {
                                "role": "user",
                                "content": (
                                    "Please translate the following English content into modern Chinese. "
                                    "Only output the translation, no explanations or extra comments:\n" + text
                                )
                            }
                        ]
                    }
                    log_info(f"正在翻译（{model_name}）：{text[:60].replace(chr(10), ' ')}{'...' if len(text)>60 else ''}")
                    resp = requests.post(url, headers=headers, json=data, timeout=60)
                    resp.raise_for_status()
                    result = resp.json()
                    if "choices" not in result or not result["choices"]:
                        raise Exception("返回结果中无 choices 字段")
                    translation = result["choices"][0]["message"]["content"]
                    self.success_count += 1
                    log_info("翻译成功")
                    return translation
                except Exception as e:
                    log_warn(f"模型 {model_name} 第 {attempt} 次尝试失败，错误信息：{e}")
                    time.sleep(1.5 + random.uniform(0, 2))
            log_warn(f"模型 {model_name} 连续 {self.max_retries} 次失败，切换到下一个模型。")
        self.fail_count += 1
        log_error("所有模型均已失败，本段输出占位内容！")
        return "[翻译失败]"

    def stats(self):
        """
        返回翻译成功/失败次数
        """
        return {
            "success_count": self.success_count,
            "fail_count": self.fail_count
        }