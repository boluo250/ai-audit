import json
import os
import re
import numpy as np
import requests
from openai import OpenAI
from transformers import AutoTokenizer, AutoModel
import torch

# 全局模型配置缓存
_model_config = None

def get_model(model_key: str) -> str:
    """直接从JSON读取模型名称"""
    global _model_config
    if _model_config is None:
        config_path = os.path.join(os.path.dirname(__file__), 'model_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                _model_config = json.load(f)
        except:
            _model_config = {}
    
    return _model_config.get(model_key, 'gpt-4o-mini')

class JSONExtractError(Exception):
    def __init__(self, ErrorInfo):
        super().__init__(self)
        self.errorinfo=ErrorInfo
    def __str__(self):
        return self.errorinfo

def ask_openai_common(prompt):
        api_base = os.environ.get('OPENAI_API_BASE', 'api.openai.com')  # Replace with your actual OpenAI API base URL
        api_key = os.environ.get('OPENAI_API_KEY')  # Replace with your actual OpenAI API key
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": get_model('openai_general'),  # 使用模型管理器获取OpenAI模型
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        response = requests.post(f'https://{api_base}/v1/chat/completions', headers=headers, json=data)
        try:
            response_josn = response.json()
        except Exception as e:
            return ''
        if 'choices' not in response_josn:
            return ''
        return response_josn['choices'][0]['message']['content']
def ask_openai_for_json(prompt):
    api_base = os.environ.get('OPENAI_API_BASE', 'api.openai.com')  # Replace with your actual OpenAI API base URL
    api_key = os.environ.get('OPENAI_API_KEY')  # Replace with your actual OpenAI API key
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": get_model('structured_json_extraction'),
        "response_format": { "type": "json_object" },
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant designed to output JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    # response = requests.post(f'https://{api_base}/v1/chat/completions', headers=headers, json=data)
    # # if response.status_code != 200:
    # #     print(response.text)
    
    # response_josn = response.json()
    # if 'choices' not in response_josn:
    #     return ''
    # # print(response_josn['choices'][0]['message']['content'])
    # return response_josn['choices'][0]['message']['content']
    while True:
        try:
            response = requests.post(f'https://{api_base}/v1/chat/completions', headers=headers, json=data)
            response_json = response.json()
            if 'choices' not in response_json:
                return ''
            response_content = response_json['choices'][0]['message']['content']
            if "```json" in response_content:
                try:
                    cleaned_json = extract_json_string(response_content)
                    break
                except JSONExtractError as e:
                    print(e)
                    print("===Error in extracting json. Retry request===")
                    continue
            else:
                try:
                    decoded_content = json.loads(response_content)
                    if isinstance(decoded_content, dict):
                        cleaned_json = response_content
                        break
                    else:
                        print("===Unexpected JSON format. Retry request===")
                        print(response_content)
                        continue
                except json.JSONDecodeError as e:
                    print("===Error in decoding JSON. Retry request===")
                    continue
                except Exception as e:
                    print("===Unexpected error. Retry request===")
                    print(e)
                    continue
        except Exception as e:
            print("===Error in requesting LLM. Retry request===")
    return cleaned_json

def extract_json_string(response):
    json_pattern = re.compile(r'```json(.*?)```', re.DOTALL)
    response = response.strip()
    extracted_json = re.findall(json_pattern, response)
    if len(extracted_json) > 1:
        print("[DEBUG]⚠️Error json string:")
        print(response)
        raise JSONExtractError("⚠️Return JSON format error: More than one JSON format found")
    elif len(extracted_json) == 0:
        print("[DEBUG]⚠️Error json string:")
        print(response)
        raise JSONExtractError("⚠️Return JSON format error: No JSON format found")
    else:
        cleaned_json = extracted_json[0]
        data_json = json.loads(cleaned_json)
        if isinstance(data_json, dict):
            return cleaned_json
        else:
            print("[DEBUG]⚠️Error json string:")
            print(response)
            raise JSONExtractError("⚠️Return JSON format error: input format is not a JSON")

def extract_structured_json(prompt):
    return ask_openai_for_json(prompt)
def detect_vulnerabilities(prompt):
    model = get_model('vulnerability_detection')
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"vul API调用失败。错误: {str(e)}")
        return ""
def analyze_code_assumptions(prompt):
    model = get_model('code_assumptions_analysis')
    api_key = os.environ.get('OPENAI_API_KEY','sk-0fzQWrcTc0DASaFT7Q0V0e7c24ZyHMKYgIDpXWrry8XHQAcj')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"Claude API调用失败。错误: {str(e)}")
        return ""

def ask_deepseek(prompt):
    model = 'deepseek-reasoner'
    # print("prompt:",prompt)
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    # print("api_base:",api_base)
    # print("api_key:",api_key)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"wokaai deepseek API调用失败。错误: {str(e)}")
        return ""








def clean_text(text: str) -> str:
    return str(text).replace(" ", "").replace("\n", "").replace("\r", "")

# 全局模型实例，避免重复加载
_embedding_model = None
_embedding_tokenizer = None

def get_embedding_model():
    """获取embedding模型实例（单例模式）"""
    global _embedding_model, _embedding_tokenizer
    if _embedding_model is None:
        try:
            # 使用超轻量级模型
            model_name = os.getenv('EMBEDDING_MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2')
            print(f" 正在加载轻量级embedding模型: {model_name}")
            
            # 设置环境变量减少内存占用
            os.environ['TOKENIZERS_PARALLELISM'] = 'false'
            
            # 加载tokenizer和模型
            _embedding_tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir='./models'  # 指定缓存目录
            )
            _embedding_model = AutoModel.from_pretrained(
                model_name,
                cache_dir='./models'  # 指定缓存目录
            )
            
            # 设置为评估模式，减少内存占用
            _embedding_model.eval()
            
            # 强制使用CPU，避免GPU内存占用
            _embedding_model = _embedding_model.to('cpu')
            
            print(f"✅ 轻量级embedding模型加载完成")
            print(f"   模型维度: {_embedding_model.config.hidden_size}")
            
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            raise e
    return _embedding_model, _embedding_tokenizer

def common_get_embedding(text: str):
    """使用Hugging Face Transformers生成embedding"""
    try:
        # 获取模型和tokenizer
        model, tokenizer = get_embedding_model()
        
        # 文本预处理
        cleaned_text = clean_text(text)
        
        # 限制文本长度，减少内存占用
        if len(cleaned_text) > 1000:
            cleaned_text = cleaned_text[:1000]
            print(f"⚠️ 文本过长，已截断到1000字符")
        
        # 编码文本
        inputs = tokenizer(
            cleaned_text, 
            return_tensors='pt', 
            truncation=True, 
            padding=True, 
            max_length=512
        )
        
        # 生成embedding
        with torch.no_grad():
            outputs = model(**inputs)
            # 使用[CLS] token的embedding
            embedding = outputs.last_hidden_state[:, 0, :].squeeze()
        
        # 转换为列表格式
        return embedding.tolist()
        
    except Exception as e:
        print(f"❌ 本地embedding生成失败: {e}")
        # 获取模型维度作为fallback
        try:
            model, _ = get_embedding_model()
            model_dim = model.config.hidden_size
            return list(np.zeros(model_dim))
        except:
            # 如果连模型都无法获取，返回默认维度
            return list(np.zeros(384))  # all-MiniLM-L6-v2的默认维度


# ========== 漏洞检测多轮分析专用函数 ==========

def perform_initial_vulnerability_validation(prompt):
    """
    代理初始分析 - 执行初步漏洞检测分析
    环境变量: AGENT_INITIAL_MODEL (默认: claude-3-haiku-20240307)
    """
    model = get_model('initial_vulnerability_validation')
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', json=data, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return "API调用失败"

def perform_comprehensive_vulnerability_analysis(prompt):
    """
    执行综合漏洞分析
    环境变量: COMPREHENSIVE_ANALYSIS_MODEL (默认: claude-3-sonnet-20240229)
    """
    model = get_model('comprehensive_vulnerability_analysis')
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', json=data, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return "API调用失败"

def perform_additional_context_determination(prompt):
    """
    执行额外上下文确定
    环境变量: ADDITIONAL_CONTEXT_MODEL (默认: claude-3-haiku-20240307)
    """
    model = get_model('additional_context_determination')
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', json=data, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return "API调用失败"

def perform_final_vulnerability_extraction(prompt):
    """
    执行最终漏洞提取
    环境变量: FINAL_EXTRACTION_MODEL (默认: gpt-4o-mini)
    """
    model = get_model('final_vulnerability_extraction')
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', json=data, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return "API调用失败"

def perform_vulnerability_findings_json_extraction(prompt):
    """
    执行漏洞发现JSON提取
    环境变量: VULNERABILITY_FINDINGS_MODEL (默认: gpt-4o-mini)
    """
    model = get_model('vulnerability_findings_json_extraction')
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', json=data, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return "API调用失败"

def ask_openai_for_json(prompt: str) -> dict:
    """
    调用OpenAI API获取JSON响应
    环境变量: OPENAI_GENERAL_MODEL (默认: gpt-4.1)
    """
    model = get_model('openai_general')
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', json=data, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return "API调用失败"

def detect_vulnerabilities(prompt: str) -> str:
    """
    检测漏洞
    环境变量: VULNERABILITY_DETECTION_MODEL (默认: claude-sonnet-4-20250514)
    """
    model = get_model('vulnerability_detection')
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', json=data, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return "API调用失败"

def analyze_code_assumptions(prompt: str) -> str:
    """
    分析代码假设
    环境变量: CODE_ASSUMPTIONS_MODEL (默认: claude-sonnet-4-20250514)
    """
    model = get_model('code_assumptions_analysis')
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', json=data, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return "API调用失败"

def extract_structured_json(prompt: str) -> dict:
    """
    提取结构化JSON
    环境变量: STRUCTURED_JSON_MODEL (默认: gpt-4.1)
    """
    model = get_model('structured_json_extraction')
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', json=data, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return "API调用失败"