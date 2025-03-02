from concurrent.futures import ThreadPoolExecutor
import json
import re
import threading
import time
from typing import List
import requests
import tqdm
from sklearn.metrics.pairwise import cosine_similarity
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import warnings
import urllib3
warnings.filterwarnings('ignore', category=urllib3.exceptions.NotOpenSSLWarning)
from dao.entity import Project_Task
from prompt_factory.prompt_assembler import PromptAssembler
from prompt_factory.core_prompt import CorePrompt
from openai_api.openai import *
class AiEngine(object):

    def __init__(self, planning, taskmgr,lancedb,lance_table_name,project_audit):
        # Step 1: 获取results
        self.planning = planning
        self.project_taskmgr = taskmgr
        self.lancedb=lancedb
        self.lance_table_name=lance_table_name
        self.project_audit=project_audit
    def do_planning(self):
        self.planning.do_planning()
    def extract_title_from_text(self,input_text):
        try:
            # Regular expression pattern to capture the value of the title field
            pattern = r'"title"\s*:\s*"([^"]+)"'
            
            # Searching for the pattern in the input text
            match = re.search(pattern, input_text)

            # Extracting the value if the pattern is found
            if match:
                return match.group(1)
            else:
                return "Logic Error"
        except Exception as e:
            # Handling any exception that occurs and returning a message
            return f"Logic Error"

    def process_task_do_scan(self,task, filter_func = None, is_gpt4 = False):
        
        response_final = ""
        response_vul = ""

        # print("query vul %s - %s" % (task.name, task.rule))

        result = task.get_result(is_gpt4)
        business_flow_code = task.business_flow_code
        if_business_flow_scan = task.if_business_flow_scan
        function_code=task.content
        
        # 要进行检测的代码粒度
        code_to_be_tested=business_flow_code if if_business_flow_scan=="1" else function_code
        if result is not None and len(result) > 0 and str(result).strip() != "NOT A VUL IN RES no":
            print("\t skipped (scanned)")
        else:
            to_scan = filter_func is None or filter_func(task)
            if not to_scan:
                print("\t skipped (filtered)")
            else:
                print("\t to scan")
                if os.getenv("SCAN_MODE","COMMON_VUL")=="OPTIMIZE":  
                    prompt=PromptAssembler.assemble_optimize_prompt(code_to_be_tested)
                elif os.getenv("SCAN_MODE","COMMON_VUL")=="COMMON_PROJECT":
                    prompt=PromptAssembler.assemble_prompt_common(code_to_be_tested)
                elif os.getenv("SCAN_MODE","COMMON_VUL")=="PURE_SCAN":
                    prompt=PromptAssembler.assemble_prompt_pure(code_to_be_tested)
                elif os.getenv("SCAN_MODE","COMMON_VUL")=="SPECIFIC_PROJECT":
                    # 构建提示来判断业务类型
                    business_type=task.recommendation
                    print(f"[DEBUG] business_type: {business_type}")
                    # 数据库中保存的形式是xxxx,xxxxx,xxxx... 转成assemble_prompt_for_specific_project可以接收的数组形式
                    business_type_list=business_type.split(',')
                    print(f"[DEBUG] business_type_list: {business_type_list}")
                    prompt = PromptAssembler.assemble_prompt_for_specific_project(code_to_be_tested, business_type_list)
                    print(f"[DEBUG] Generated prompt: {prompt}")
                response_vul=ask_claude(prompt)
                print(f"[DEBUG] Claude response: {response_vul}")
                response_vul = response_vul if response_vul is not None else "no"                
                self.project_taskmgr.update_result(task.id, response_vul, "","")
    def do_scan(self, is_gpt4=False, filter_func=None):
        # self.llm.init_conversation()

        tasks = self.project_taskmgr.get_task_list()
        if len(tasks) == 0:
            return

        # 定义线程池中的线程数量
        max_threads = int(os.getenv("MAX_THREADS_OF_SCAN", 5))

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(self.process_task_do_scan, task, filter_func, is_gpt4) for task in tasks]
            
            with tqdm(total=len(tasks), desc="Processing tasks") as pbar:
                for future in as_completed(futures):
                    future.result()  # 等待每个任务完成
                    pbar.update(1)  # 更新进度条

        return tasks
    def process_task_check_vul(self, task:Project_Task):
        print("\n" + "="*80)
        print(f"🔍 开始处理任务 ID: {task.id}")
        print("="*80)
        
        # 用于收集所有分析结果
        analysis_collection = []
        
        starttime = time.time()
        result = task.get_result(False)
        result_CN = task.get_result_CN()
        category_mark = task.get_category()
        
        if result_CN is not None and len(result_CN) > 0 and result_CN != "None" and category_mark is not None and len(category_mark)>0:
            print("\n🔄 该任务已处理完成，跳过...")
            return
            
        print("\n🔍 开始漏洞确认流程...")
        print(f"📝 原始扫描结果长度: {len(result)}")
        
        function_code = task.content
        if_business_flow_scan = task.if_business_flow_scan
        business_flow_code = task.business_flow_code
        business_flow_context = task.business_flow_context
        
        code_to_be_tested = business_flow_code+"\n"+business_flow_context if if_business_flow_scan=="1" else function_code
        print(f"\n📊 分析代码类型: {'业务流程代码' if if_business_flow_scan=='1' else '函数代码'}")
        
        # 第一轮分析
        print("\n=== 第一轮分析开始 ===")
        print("📝 正在分析潜在漏洞...")
        prompt = PromptAssembler.assemble_vul_check_prompt(code_to_be_tested, result)
        
        with open("prompt.txt", "w") as file:
            file.write(prompt)
        print("💾 提示词已保存到 prompt.txt")

        initial_response = common_ask_confirmation(prompt)
        if not initial_response or initial_response == "":
            print(f"❌ Error: Empty response received for task {task.id}")
            return
        
        print("\n📊 Initial Analysis Result Length:")
        print("-" * 80)
        print(len(initial_response))
        print("-" * 80)

        # 收集初始分析结果
        analysis_collection.append("=== 初始分析结果 ===")
        analysis_collection.append(initial_response)

        # 对initial_response进行process_round_response处理
        initial_result_status = self.process_round_response(initial_response)
        analysis_collection.append("=== 初始分析状态 ===")
        analysis_collection.append(initial_result_status)

        # 提取所需信息
        required_info = self.extract_required_info(initial_response)
        if required_info:
            analysis_collection.append("=== 需要进一步分析的信息 ===")
            analysis_collection.extend(required_info)

        if "no" in initial_result_status:
            print("\n🛑 Initial analysis shows clear 'no vulnerability' - stopping further analysis")
            response_final = "no"
            final_response = "Analysis stopped after initial round due to clear 'no vulnerability' result"
            
            # 格式化所有收集的结果
            formatted_results = "\n\n".join(analysis_collection)
            
            self.project_taskmgr.update_result(task.id, result, response_final, final_response)
            self.project_taskmgr.update_category(task.id, formatted_results)
            
            endtime = time.time()
            time_cost = endtime - starttime
            print("\n=== Task Summary ===")
            print(f"⏱️ Time cost: {time_cost:.2f} seconds")
            print(f"📝 Analyses performed: 1")
            print(f"🏁 Final status Length: {len(response_final)}")
            print("=" * 80 + "\n")
            return
        
        # 使用新的方法进行上下文增强，可以控制轮数
        combined_code = self.enhance_context_with_additional_info(code_to_be_tested, initial_response, rounds=2)
        
        # 进行三轮确认
        confirmation_results = []
        response_final = None
        final_response = None
        
        for i in range(3):
            if response_final == "no":  # 如果已经确认为 no，直接跳过后续循环
                break
            
            print(f"\n📊 Round {i+1}/3 Analysis:")
            prompt = PromptAssembler.assemble_vul_check_prompt_final(combined_code, result)
            round_response = common_ask_confirmation(prompt)
            
            print("-" * 80)
            print(f"Round {i+1} Analysis Length:")
            print(len(round_response))
            print("-" * 80)
            
            # 收集每轮分析结果
            analysis_collection.append(f"=== 第 {i+1} 轮分析结果 ===")
            analysis_collection.append(round_response)
            
            # 使用新的方法处理每轮的结果
            result_status = self.process_round_response(round_response)
            analysis_collection.append(f"=== 第 {i+1} 轮分析状态 ===")
            analysis_collection.append(result_status)
            
            confirmation_results.append(result_status)
            
            # 如果发现一个明确的 "no"，立即确认为不存在漏洞
            if "no" in result_status:
                print("\n🛑 Clear 'no vulnerability' detected - stopping further analysis")
                response_final = "no"
                final_response = f"Analysis stopped after round {i+1} due to clear 'no vulnerability' result"
                continue
        
        # 只有在没有提前退出（找到明确的 no）的情况下才进行多数投票
        if response_final != "no":
            # 统计结果
            yes_count = sum(1 for r in confirmation_results if "yes" in r or "confirmed" in r)
            no_count = sum(1 for r in confirmation_results if "no" in r and "vulnerability" in r)
            
            if yes_count >= 2:
                response_final = "yes"
                print("\n⚠️ Final Result: Vulnerability Confirmed (2+ positive confirmations)")
            elif no_count >= 2:
                response_final = "no"
                print("\n✅ Final Result: No Vulnerability (2+ negative confirmations)")
            else:
                response_final = "not sure"
                print("\n❓ Final Result: Not Sure (inconclusive results)")
            
            final_response = "\n".join([f"Round {i+1} Analysis:\n{resp}" for i, resp in enumerate(confirmation_results)])
        
        # 添加最终结论
        analysis_collection.append("=== 最终结论 ===")
        analysis_collection.append(f"结果: {response_final}")
        analysis_collection.append(f"详细说明: {final_response}")
        
        # 格式化所有收集的结果
        formatted_results = "\n\n".join(analysis_collection)
        
        self.project_taskmgr.update_result(task.id, result, response_final, final_response)
        self.project_taskmgr.update_category(task.id, formatted_results)
        
        endtime = time.time()
        time_cost = endtime - starttime
        
        print("\n=== Task Summary ===")
        print(f"⏱️ Time cost: {time_cost:.2f} seconds")
        print(f"📝 Analyses performed: {len(confirmation_results)}")
        print(f"🏁 Final status Length: {len(response_final)}")
        print("=" * 80 + "\n")

    def enhance_context_with_additional_info(self, code_to_be_tested, initial_response, rounds=1):
        """
        增强代码上下文，通过多轮提取所需信息和获取额外上下文
        
        Args:
            code_to_be_tested: 原始代码
            initial_response: 初始分析结果
            rounds: 需要执行的轮数
            
        Returns:
            str: 增强后的代码上下文
        """
        combined_code = code_to_be_tested
        current_response = initial_response
        
        for round_num in range(rounds):
            required_info = self.extract_required_info(current_response)
            
            if not required_info:
                print(f"\n🔍 第 {round_num+1} 轮: 无需额外信息")
                break
            
            print(f"\n=== 额外信息收集 - 第 {round_num+1} 轮 ===")
            print("🔎 需要补充的上下文信息:")
            for i, info in enumerate(required_info, 1):
                print(f"{i}. {info}")
            
            print("\n📥 正在获取额外上下文...")
            additional_context = self.get_additional_context(required_info)
            
            if additional_context:
                print(f"\n📦 已获取额外上下文 (长度: {len(additional_context)} 字符)")
                if len(additional_context) < 500:
                    print("\n额外上下文详情:")
                    print("-" * 80)
                    print(len(additional_context))
                    print("-" * 80)
                
                # 更新组合代码，包含所有历史信息
                combined_code = f"""Original Code:
                    {code_to_be_tested}

                    Analysis Round {round_num}:
                    {current_response}

                    Additional Context Round {round_num+1}:
                    {additional_context}"""
                
                # 如果需要继续进行下一轮，可以对新的组合代码再次进行分析
                if round_num < rounds - 1:
                    prompt = PromptAssembler.assemble_vul_check_prompt(combined_code, "")
                    current_response = common_ask_confirmation(prompt)
                    print(f"\n📊 Intermediate Analysis Result (Round {round_num+1}) Length:")
                    print("-" * 80)
                    print(len(current_response))
                    print("-" * 80)
            else:
                print("\n⚠️ No additional context found, stopping context enhancement")
                break
        
        return combined_code

    def process_round_response(self, round_response):
        """
        处理每轮分析的响应，提取结果状态
        
        Args:
            round_response: 当前轮次的响应
            
        Returns:
            str: 提取的结果状态
        """
        prompt_translate_to_json = PromptAssembler.brief_of_response()
        
        round_json_response = str(common_ask_for_json(round_response+"\n"+prompt_translate_to_json))
        print("\n📋 JSON Response Length:")
        print(len(round_json_response))
        
        try:
            response_data = json.loads(round_json_response)
            result_status = response_data.get("result", "").lower()
            print("\n🎯 Extracted Result Status Length:")
            print(len(result_status))
            return result_status
        except json.JSONDecodeError:
            print("\n⚠️ JSON Decode Error - marking as 'not sure'")
            return "not sure"

    def get_related_functions(self,query,k=3):
        query_embedding = common_get_embedding(query)
        table = self.lancedb.open_table(self.lance_table_name)
        return table.search(query_embedding).limit(k).to_list()
    
    def extract_related_functions_by_level(self, function_names: List[str], level: int) -> str:
        """
        从call_trees中提取指定函数相关的上下游函数信息并扁平化处理
        
        Args:
            function_names: 要分析的函数名列表
            level: 要分析的层级深度
            
        Returns:
            str: 所有相关函数内容的拼接文本
        """
        def get_functions_from_tree(tree, current_level=0, max_level=level, collected_funcs=None, level_stats=None):
            """递归获取树中指定层级内的所有函数信息"""
            if collected_funcs is None:
                collected_funcs = []
            if level_stats is None:
                level_stats = {}
                
            if not tree or current_level > max_level:
                return collected_funcs, level_stats
                    
            # 添加当前节点的函数信息
            if tree['function_data']:
                collected_funcs.append(tree['function_data'])
                # 更新层级统计
                level_stats[current_level] = level_stats.get(current_level, 0) + 1
                    
            # 递归处理子节点
            if current_level < max_level:
                for child in tree['children']:
                    get_functions_from_tree(child, current_level + 1, max_level, collected_funcs, level_stats)
                        
            return collected_funcs, level_stats

        all_related_functions = []
        statistics = {
            'total_layers': level,
            'upstream_stats': {},
            'downstream_stats': {}
        }
        
        # 使用集合进行更严格的去重
        seen_functions = set()  # 存储函数的唯一标识符
        unique_functions = []   # 存储去重后的函数
        
        # 遍历每个指定的函数名
        for func_name in function_names:
            # 在call_trees中查找对应的树
            for tree_data in self.project_audit.call_trees:
                if tree_data['function'] == func_name:
                    # 处理上游调用树
                    if tree_data['upstream_tree']:
                        upstream_funcs, upstream_stats = get_functions_from_tree(tree_data['upstream_tree'])
                        all_related_functions.extend(upstream_funcs)
                        # 合并上游统计信息
                        for level, count in upstream_stats.items():
                            statistics['upstream_stats'][level] = (
                                statistics['upstream_stats'].get(level, 0) + count
                            )
                            
                    # 处理下游调用树
                    if tree_data['downstream_tree']:
                        downstream_funcs, downstream_stats = get_functions_from_tree(tree_data['downstream_tree'])
                        all_related_functions.extend(downstream_funcs)
                        # 合并下游统计信息
                        for level, count in downstream_stats.items():
                            statistics['downstream_stats'][level] = (
                                statistics['downstream_stats'].get(level, 0) + count
                            )
                        
                    # 添加原始函数本身
                    for func in self.project_audit.functions_to_check:
                        if func['name'].split('.')[-1] == func_name:
                            all_related_functions.append(func)
                            break
                                
                    break
        
        # 增强的去重处理
        for func in all_related_functions:
            # 创建一个更精确的唯一标识符，包含函数名和内容的hash
            func_identifier = f"{func['name']}_{hash(func['content'])}"
            if func_identifier not in seen_functions:
                seen_functions.add(func_identifier)
                unique_functions.append(func)
        
        # 拼接所有函数内容，包括状态变量
        combined_text_parts = []
        for func in unique_functions:
            # 查找对应的状态变量
            state_vars = None
            for tree_data in self.project_audit.call_trees:
                if tree_data['function'] == func['name'].split('.')[-1]:
                    state_vars = tree_data.get('state_variables', '')
                    break
            
            # 构建函数文本，包含状态变量
            function_text = []
            if state_vars:
                function_text.append("// Contract State Variables:")
                function_text.append(state_vars)
                function_text.append("\n// Function Implementation:")
            function_text.append(func['content'])
            
            combined_text_parts.append('\n'.join(function_text))
        
        combined_text = '\n\n'.join(combined_text_parts)
        
        # 打印统计信息
        print(f"\nFunction Call Tree Statistics:")
        print(f"Total Layers Analyzed: {level}")
        print("\nUpstream Statistics:")
        for layer, count in statistics['upstream_stats'].items():
            print(f"Layer {layer}: {count} functions")
        print("\nDownstream Statistics:")
        for layer, count in statistics['downstream_stats'].items():
            print(f"Layer {layer}: {count} functions")
        print(f"\nTotal Unique Functions: {len(unique_functions)}")
        
        return combined_text


    def check_function_vul(self):
        # self.llm.init_conversation()
        tasks = self.project_taskmgr.get_task_list()
        # 用codebaseQA的形式进行，首先通过rag和task中的vul获取相应的核心三个最相关的函数
        for task in tqdm(tasks,desc="Processing tasks for update business_flow_context"):
            if task.score=="1":
                continue
            if task.if_business_flow_scan=="1":
                # 获取business_flow_context
                code_to_be_tested=task.business_flow_code
            else:
                code_to_be_tested=task.content
            related_functions=self.get_related_functions(code_to_be_tested,5)
            related_functions_names=[func['name'].split('.')[-1] for func in related_functions]
            combined_text=self.extract_related_functions_by_level(related_functions_names,6)
            # 更新task对应的business_flow_context
            self.project_taskmgr.update_business_flow_context(task.id,combined_text)
            self.project_taskmgr.update_score(task.id,"1")
            

        if len(tasks) == 0:
            return

        # 定义线程池中的线程数量, 从env获取
        max_threads = int(os.getenv("MAX_THREADS_OF_CONFIRMATION", 5))

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(self.process_task_check_vul, task) for task in tasks]

            with tqdm(total=len(tasks), desc="Checking vulnerabilities") as pbar:
                for future in as_completed(futures):
                    future.result()  # 等待每个任务完成
                    pbar.update(1)  # 更新进度条

        return tasks

    def extract_required_info(self, claude_response):
        """Extract information that needs further investigation from Claude's response"""
        prompt = """
        Please extract all information points that need further understanding or confirmation from the following analysis response.
        If the analysis explicitly states "no additional information needed" or similar, return empty.
        If the analysis mentions needing more information, extract these information points.
        
        Analysis response:
        {response}
        """
        
        extraction_result = ask_claude(prompt.format(response=claude_response))
        if not extraction_result or extraction_result.isspace():
            return []
        
        # If response contains negative phrases, return empty list
        if any(phrase in extraction_result.lower() for phrase in ["no need", "not needed", "no additional", "no more"]):
            return []
        
        return [extraction_result]

    def get_additional_context(self, query_contents):
        """获取额外的上下文信息"""
        if not query_contents:
            print("❌ 没有查询内容，无法获取额外上下文")
            return ""
        
        print(f"🔍 正在查询 {len(query_contents)} 条相关信息...")
        related_functions = []
        for query in query_contents:
            results = self.get_related_functions(query, k=10)
            if results:
                print(f"✅ 找到 {len(results)} 个相关函数")
                related_functions.extend(results)
            else:
                print("⚠️ 未找到相关函数")
        
        if related_functions:
            function_names = [func['name'].split('.')[-1] for func in related_functions]
            print(f"📑 正在提取 {len(function_names)} 个函数的上下文...")
            return self.extract_related_functions_by_level(function_names, 2)
        
        print("❌ 未找到任何相关函数")
        return ""

if __name__ == "__main__":
    pass