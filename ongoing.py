import json
import os
import subprocess
import tarfile
import shutil
import re
import sys
import pygraphviz as pgv
import csv
from picking_tree import get_reverse_dependency_tree

def get_onewalk_dep(g, pkg_name, pkg_version, working): 
    """
    - Description: 주어진 패키지의 종속 패키지들을 확인 + 정규화
    - Input: 지금까지 만든 graph, 검사하고 싶은 패키지 이름, 버전
    - Output: 'name: version (json)' 형식으로 만들어진 dictionary 
    """

    #print(f"+++++ get_onewalk_dep for {pkg_name}")
    dep_dict = {}
    try:
        dep_result = subprocess.run(['npm', 'view', pkg_name, 'dependencies', '--json'], capture_output=True, text=True, check=True)
        #view 한 의존성 저장
        dep_dict = json.loads(dep_result.stdout)

    except subprocess.CalledProcessError as e:
        #print(f"Error occurred while fetching dependencies for {pkg_name}: {e}")
        return g, working, dep_dict

    except json.JSONDecodeError as e:
        #print(f"JSON decode error: {e}")
        return g, working, dep_dict

    #결과값 없으면 탈출
    if not isinstance(dep_dict, dict):
        #print(f"[-] get_onewalk_dep(): No dependencies for {pkg_name}.")
        return False
    for name, version in dep_dict.items():
        # 특수 문자를 제거하고 숫자만 추출
        version_numbers = re.findall(r'\d+', version)
        #버전 정보가 있을 경우, n.n.n 저장
        if version_numbers:
            version_str = ".".join(version_numbers)
            dep_dict[name] = version_str
        else:
            # 버전 정보가 없을 경우, 0.0.0으로 지정
            dep_dict[name] = "0.0.0"
    return g, working, dep_dict
        

def make_subgraph(g, pkg_name, pkg_version, working, dep_dict):
    """
    - Description: pkg_name에 맞는 서브그래프를 그리고 working 리스트 업데이트
    - Input: 전체 그래프 g, upstream 패키지 이름, 버전, 
    - Output:
    ~ upstream: 'pkg_name@pkg_version'
    ~ downstream: 'name@version'
  
    """ 


    upstream_str = f"{pkg_name}@{pkg_version}"

    for name, version in dep_dict.items():
        #정규표현화된 버전정보를 working 리스트에 저장
        downstream_str = f"{name}@{version}"
        #새로운 subgraph를 만들기전 이미 있는 그래프인지 아닌지 확인
        if g.get_subgraph(name): # <- 특정패키지 O
            #print(f"Subgraph '{name}' exists.") 
            
            #해당 서브그래프에 버전이 이미 있는지 확인하고 없으면 추가합니다.
            if downstream_str not in g.get_subgraph(name).nodes(): # <-특정패키지 O, but 특정버전 X!!!
                
                g.get_subgraph(name).add_node(downstream_str)
                #print(f"Subgraph node '{version} of {name}' is just made.")
                working.append(downstream_str)
            else: # <-특정패키지 O, and 특정버전 O!!!
                print(f"Subgraph node '{version} of {name}' already exists.")
                # 얘는 특정 패키지의 특정 버전이 있는 경우임..! 엣지만 만든다면 여기서 사이클을 막을 수있음!! 얘만 암것두 안하고 다음 for문으로 넘어가는 방식으로 해결함

        # 이 패키지 이름으로 만들어진 서브그래프가 없음        
        else:
            print(f"Subgraph {name} does not exist.")

            working.append(downstream_str)
            
            #서브그래프 없으니 새롭게 만들기. 패키지 name이 subgraph의 이름이 되고, 패키지 version이 노드의 이름이 된다.
            subgraph_name = name
            g.add_subgraph(name=subgraph_name)
            g.get_subgraph(subgraph_name).graph_attr['label'] = f"*{name}*"  # 라벨은 시각화를 위한 듯
            
            # Add nodes with versions to the subgraph
            #자기 자신이면 노드 생성 X
            g.get_subgraph(subgraph_name).add_node(downstream_str)


        #서브그래프는 있어도 자식노드와 연결시키는 엣지는 없을 수 있음
        for sg in g.subgraphs(): #모든 서브그래프를 반복적으로 확인
            if sg.name == pkg_name:
        # 노드 찾기 및 연결
                if sg.has_node(upstream_str):
                    #진짜 그래프의 노드끼리 연결
                    parent = g.get_subgraph(pkg_name).get_node(upstream_str)
                    #print(f"부모 확인: {parent}")
                    child = g.get_subgraph(name).get_node(downstream_str)
                    #print(f"자식 확인: {child}")
                    g.add_edge(g.get_subgraph(pkg_name).get_node(upstream_str), g.get_subgraph(name).get_node(downstream_str))

    return g, working

 
def process_package(g, working):
    """
    Description: 주어진 패키지(package_name)의 종속되어있는 패키지 정보를
    그래프 g에 노드, 간선 형태로 반복 업데이트
    - Input: g
    - Output: 
    """
    if working != []:
        
        package_str = working.pop(0)
        package_name, package_version = package_str.rsplit('@',1)


        g, working, dep_dict = get_onewalk_dep(g, package_name, package_version, working)
        result = make_subgraph(g, package_name, package_version, working, dep_dict)

        g = result[0]
        working_pkg_list = result[1]

        g = process_package(g, working_pkg_list)        

    return g

def combine_graphs(graph1, graph2):
    """
    - Description: 두 개의 그래프를 결합하여 새로운 그래프를 만듭니다.
    - Input: graph1는 새로운 그래프 graph2는 원래 있던 그래프
    - Output: 합친 그래프
    """
    combined_graph = graph1.copy()  # 첫 번째 그래프를 복사하여 새로운 그래프 생성
    # graph2의 모든 서브그래프를 반복하여 추가 <- 이렇게 해줘야 서브그래프의 모든 요소가 복제되어 combine됨. 안그러면 이름이 복제안되거나.. 
    for subgraph in graph2.subgraphs():
        subgraph_name = subgraph.name  # 서브그래프의 이름 가져오기
        subgraph_attr = subgraph.graph_attr  # 서브그래프의 속성 가져오기

        # 새로운 그래프에 동일한 이름과 속성으로 서브그래프 생성
        new_subgraph = combined_graph.add_subgraph(name=subgraph_name, **subgraph_attr)

        # 서브그래프의 노드와 엣지를 새로운 서브그래프에 추가
        for node in subgraph.nodes():
            new_subgraph.add_node(node, **subgraph.get_node(node).attr)
        for edge in subgraph.edges():
            new_subgraph.add_edge(*edge, **subgraph.get_edge(*edge).attr)
    return combined_graph


def create_graph(): #그래프 만들기
    G = pgv.AGraph(directed=True)
    return G




if __name__ == "__main__":
    # 사용자 입력을 받아서 뽑을 tree 정함
    if len(sys.argv) != 3:
        print("Usage: python3 script_name.py tree_package_name tree_package_version")
    else:
        tree_name = sys.argv[1]  # 첫 번째 인자는 패키지 이름
        tree_version = sys.argv[2]  # 두 번째 인자는 패키지 버전
        print(f"[+] TREE_NAME : {tree_name}")
        print(f"[+] TREE_VERSION : {tree_version}")

    # Select a target package
    g = create_graph()
    #포레스트를 구성할 패키지 정보가 담긴 csv 
    with open('VDB_npm.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # 첫 번째 행은 제외 (헤더라인)
        for row in reader:
            package_name = row[1]  # 두 번째 열의 값
            package_version = row[2]  # 세 번째 열의 값
            package_str = f"{package_name}@{package_version}"

            # Initialize graph for the target
            print("STEP 2")
            package_subgraph = g.subgraph(name = package_name)
            package_subgraph.graph_attr['label'] = package_name
            package_subgraph.add_node(package_str)

            # transitive check
            print("STEP 3")
            working = []
            working.append(package_str)
            this_graph = process_package(g, working)

            g = combine_graphs(this_graph, g)
            for sg in g.subgraphs():
                print(sg)
                print("Subgraph name:", sg.name)
            


    g.layout(prog="dot")  # use dot
    g.draw("popular_forest.png")

    # # tree 뽑는 과정 ing.. 
    reverse_dependency_tree = get_reverse_dependency_tree(tree_name, tree_version, g)

    reverse_dependency_tree.layout(prog="dot")
    reverse_dependency_tree.draw("reverse_dependency_tree.png")
