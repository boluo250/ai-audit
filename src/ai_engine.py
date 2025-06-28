import os
from typing import List

from reasoning import VulnerabilityScanner
from validating import VulnerabilityChecker


class AiEngine(object):
    """
    重构后的AI引擎，整合漏洞扫描和漏洞检查功能
    
    主要功能：
    - 漏洞扫描：通过 VulnerabilityScanner 执行
    - 漏洞检查：通过 VulnerabilityChecker 执行
    - 计划处理：执行项目分析计划
    """

    def __init__(self, planning, taskmgr, lancedb, lance_table_name, project_audit):
        """
        初始化AI引擎
        
        Args:
            planning: 计划处理器
            taskmgr: 任务管理器
            lancedb: 向量数据库
            lance_table_name: 数据库表名
            project_audit: 项目审计信息
        """
        self.planning = planning
        self.project_taskmgr = taskmgr
        self.lancedb = lancedb
        self.lance_table_name = lance_table_name
        self.project_audit = project_audit
        
        # 初始化扫描和检查模块
        self.vulnerability_scanner = VulnerabilityScanner(project_audit)
        self.vulnerability_checker = VulnerabilityChecker(project_audit, lancedb, lance_table_name)

    def do_planning(self):
        """执行项目分析计划"""
        self.planning.do_planning()
    
    def do_scan(self, is_gpt4=False, filter_func=None):
        """执行漏洞扫描"""
        return self.vulnerability_scanner.do_scan(self.project_taskmgr, is_gpt4, filter_func)

    def check_function_vul(self):
        """执行漏洞检查"""
        return self.vulnerability_checker.check_function_vul(self.project_taskmgr)


if __name__ == "__main__":
    pass 