import json
import os
import re
import numpy as np
import requests
from openai import OpenAI

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
    api_base = os.environ.get('OPENAI_API_BASE', 'api.openai.com')
    api_key = os.environ.get('OPENAI_API_KEY')
    
    # 优先使用本地Claude CLI
    try:
        import subprocess
        
        # 直接通过stdin传递prompt
        result = subprocess.run(['claude'], 
                              input=prompt,
                              capture_output=True, 
                              text=True, 
                              timeout=30)
        
        if result.returncode == 0:
            print("✅ 使用本地Claude CLI成功")
            return result.stdout.strip()
        else:
            print(f"⚠️ 本地Claude CLI失败: {result.stderr}")
    except FileNotFoundError:
        print("⚠️ 本地claude命令未找到，尝试API方式")
    except Exception as e:
        print(f"⚠️ 本地Claude CLI调用异常: {e}")
    
    # 如果本地CLI失败，回退到API方式
    if not api_key:
        print("⚠️ OPENAI_API_KEY environment variable is not set")
        return ''
    
    # 检查是否是Claude API
    if 'anthropic.com' in api_base:
        # Claude API格式
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        data = {
            "model": get_model('openai_general'),
            "max_tokens": 4000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        try:
            response = requests.post(f'{api_base}/v1/messages', headers=headers, json=data)
            response.raise_for_status()
            response_json = response.json()
            if 'content' in response_json and len(response_json['content']) > 0:
                return response_json['content'][0]['text']
            return ''
        except Exception as e:
            print(f"Claude API调用失败: {e}")
            return ''
    else:
        # OpenAI API格式
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": get_model('openai_general'),
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        try:
            # 处理URL，确保正确格式
            if api_base.startswith('http'):
                url = f'{api_base}/v1/chat/completions'
            else:
                url = f'https://{api_base}/v1/chat/completions'
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_json = response.json()
            if 'choices' in response_json and len(response_json['choices']) > 0:
                return response_json['choices'][0]['message']['content']
            return ''
        except Exception as e:
            print(f"OpenAI API调用失败: {e}")
            return ''
def ask_openai_for_json(prompt):
    api_base = os.environ.get('OPENAI_API_BASE', 'api.openai.com')  # Replace with your actual OpenAI API base URL
    api_key = os.environ.get('OPENAI_API_KEY')  # Replace with your actual OpenAI API key
    
    if not api_key:
        print("⚠️ OPENAI_API_KEY environment variable is not set")
        return ""
    
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
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 处理URL，确保正确格式
            if api_base.startswith('http'):
                url = f'{api_base}/v1/chat/completions'
            else:
                url = f'https://{api_base}/v1/chat/completions'
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_json = response.json()
            if 'choices' not in response_json:
                print(f"⚠️ Invalid API response (attempt {retry_count + 1}/{max_retries})")
                retry_count += 1
                continue
            response_content = response_json['choices'][0]['message']['content']
            if "```json" in response_content:
                try:
                    cleaned_json = extract_json_string(response_content)
                    return cleaned_json
                except JSONExtractError as e:
                    print(f"JSON extraction error (attempt {retry_count + 1}/{max_retries}): {e}")
                    retry_count += 1
                    continue
            else:
                try:
                    decoded_content = json.loads(response_content)
                    if isinstance(decoded_content, dict):
                        return response_content
                    else:
                        print(f"⚠️ Unexpected JSON format (attempt {retry_count + 1}/{max_retries})")
                        retry_count += 1
                        continue
                except json.JSONDecodeError as e:
                    print(f"JSON decode error (attempt {retry_count + 1}/{max_retries}): {e}")
                    retry_count += 1
                    continue
                except Exception as e:
                    print(f"Unexpected error (attempt {retry_count + 1}/{max_retries}): {e}")
                    retry_count += 1
                    continue
        except requests.exceptions.RequestException as e:
            print(f"API request error (attempt {retry_count + 1}/{max_retries}): {e}")
            retry_count += 1
            continue
        except Exception as e:
            print(f"Unexpected error in LLM request (attempt {retry_count + 1}/{max_retries}): {e}")
            retry_count += 1
            continue
    
    print(f"⚠️ Failed to get valid JSON response after {max_retries} attempts")
    return ""

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

def common_get_embedding(text: str):
    # 使用Claude API时，直接返回零向量作为embedding
    # 这样可以避免调用OpenAI的embedding API
    print(f"📝 使用零向量embedding (Claude配置模式)")
    return list(np.zeros(3072))  # 返回长度为3072的全0数组


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
        print(f"代理初始分析API调用失败。错误: {str(e)}")
        return ""


def extract_vulnerability_findings_json(prompt):
    """
    代理JSON提取 - 从自然语言中提取结构化JSON
    环境变量: AGENT_JSON_MODEL (默认: gpt-4o-mini)
    """
    model = get_model('vulnerability_findings_json_extraction')
    api_key = os.environ.get('OPENAI_API_KEY')
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
        print(f"代理JSON提取API调用失败。错误: {str(e)}")
        return ""


def determine_additional_context_needed(prompt):
    """
    代理信息查询 - 确定需要什么类型的额外信息
    环境变量: AGENT_INFO_QUERY_MODEL (默认: claude-3-sonnet-20240229)
    """
    model = get_model('additional_context_determination')
    api_key = os.environ.get('OPENAI_API_KEY')
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
        print(f"代理信息查询API调用失败。错误: {str(e)}")
        return ""




def perform_comprehensive_vulnerability_analysis(prompt):
    """
    代理最终分析 - 基于所有收集的信息做最终判断
    环境变量: AGENT_FINAL_MODEL (默认: claude-opus-4-20250514)
    """
    model = get_model('comprehensive_vulnerability_analysis')
    api_key = os.environ.get('OPENAI_API_KEY')
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
        print(f"代理最终分析API调用失败。错误: {str(e)}")
        return ""



