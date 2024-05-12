import json
import os
import subprocess
import tarfile
import shutil
import re
import sys
import pygraphviz as pgv
import csv


def collect_dfs(tree_name, tree_version, g, extracted_graph):
	"""
    - Description: 입력으로 주어진 패키지와 버전에 대한 reverse dependency를 dfs 방식으로 탐방
    - Input: 어떤 트리를 뽑을 것인지 패키지 이름과 버전. downstream pkg name = tree_name
    - Output: 업데이트된 그래프
    """
    # tree_name에 해당하는 서브그래프 찾기
    downstream_subgraph = = g.get_subgraph('tree_name')
	for node in downstream_subgraph.nodes():
    # tree_name라는 이름의 downstream_subgraph에 내가 찾고자하는 버전이 있는지 찾기
		if node == tree_version
			# if 에러 핸들링: 찾는 노드(버전)은 있는데 다운스트림과의 관계 외에 엣지로 연결된 게 없다면??????? <- 어쨌든 한개의 엣지는 있음!! 두개부터 없는겨
			# 'tree_version'라는 노드에서 나가는 엣지의 개수를 구합니다.
			if downstream_subgraph.out_degree('tree_version') < 2:
				continue
				
			# else 연결된 엣지 있는 경우, 밑의 코드 동작
			else:
				 
	    		# 엣지의 라벨 정보 = 패키지 이름을 가져옵니다.
	    		upstream_name = subgraph.get_edge(edge[0], edge[1]).attr['label']
	    		upstream_subgraph = g.get_subgraph('upstream_name')
	    		# 엣지에 연결된 다른 노드 = 패키지 버전를 가져옵니다.
				upstream_version = edge[1] if edge[0] == node_name else edge[0]
	    		downstream = f"{tree_name}@({tree_version})"
	            upstream = f"{upstream_name}@({upstream_version})"
	            #tree용 그래프에 엣지 연결
	            extracted_graph.add_edge(downstream, upstream)
	    		
	            # if 사이클 방지: 이미 extracted_graph에 있던 upstream 이라면 다음 걸로 넘어가기

	    		# else: extracted_graph에 없던 노드이고 다음 노드에 또 노드가 있다면 dfs로 탐방
	    		if 



def get_reverse_dependency_tree(tree_name, tree_version, g):
	"""
    - Description: 입력으로 주어진 패키지와 버전에 대한 디펜던시 그래프 생성
    - Input: 어떤 트리를 뽑을 것인지 패키지 이름과 버전
    - Output: 패키지 이름과 버전에 맞는 트리 

    """
    extracted_graph = pgv.AGraph(directed=True)  # 새로운 그래프 생성




    return extracted_graph


