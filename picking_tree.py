import json
import os
import subprocess
import tarfile
import shutil
import re
import sys
import pygraphviz as pgv
import csv


def collect_dfs(tree_str, g, extracted_graph, visited):
	"""
    - Description: 입력으로 주어진 패키지와 버전에 대한 reverse dependency를 dfs 방식으로 탐방
    - Input: 어떤 트리를 뽑을 것인지 패키지 이름과 버전. dfs가 반복되며 downstream pkg name = tree_name
    - Output: 업데이트된 그래프
    """
    # tree_name에 해당하는 서브그래프 찾기
	tree_name, tree_version = tree_str.rsplit('@',1)
	downstream_subgraph = g.get_subgraph(tree_name)

	for edge in g.in_edges():
		# g에 있는 모든 
		upstream, downstream = edge
        # 엣지 정보 출력 또는 처리
		if downstream == tree_str:
		
			extracted_graph.add_edge(downstream, upstream)
			
			if not upstream in visited:
				visited.append(upstream)
				collect_dfs(upstream, g, extracted_graph, visited)
				

	return extracted_graph


def get_reverse_dependency_tree(tree_name, tree_version, g):
	"""
    - Description: 입력으로 주어진 패키지와 버전에 대한 디펜던시 그래프 생성
    - Input: 어떤 트리를 뽑을 것인지 패키지 이름과 버전
    - Output: 패키지 이름과 버전에 맞는 트리 
    """
	tree_str = f"{tree_name}@{tree_version}" #노드 이름이자 엣지구분방
	print(f"[+] TREE_NAME : {tree_name}")
	print(f"[+] TREE_VERSION : {tree_version}")
	print(f"[+] 리버스디펜던시 추출 : <<<{tree_name}@{tree_version}>>> 대상")
	extracted_graph = pgv.AGraph(directed=True)  # 새로운 그래프 생성
	visited = []
	visited.append(tree_str)
	extracted_graph = collect_dfs(tree_str, g, extracted_graph, visited)


	print(extracted_graph)
	return extracted_graph


