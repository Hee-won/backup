import json
import os
import subprocess
import tarfile
import shutil
import re
import sys
import pygraphviz as pgv
from collections import deque


def get_onewalk_dep(g, pkg_name, pkg_version, working): 
    print(f"+++++ get_onewalk_dep for {pkg_name}")

    dep_dict = {}
    """
    - Description: 주어진 패키지의 종속 패키지들을 확인 + 정규화
    - Input: 지금까지 만든 graph, 검사하고 싶은 패키지 이름, 버전
    - Output: 'name: version (json)' 형식으로 만들어진 dictionary 
    """
    try:
        dep_result = subprocess.run(['npm', 'view', pkg_name, 'dependencies', '--json'], capture_output=True, text=True, check=True)
        #view 한 의존성 저장
        dep_dict = json.loads(dep_result.stdout)
        print(f"dep_result.stdout = {dep_result.stdout}")
        print(f"[-] Before dep_dict = {dep_dict}")

    except subprocess.CalledProcessError as e:
        print(f"Error occurred while fetching dependencies for {pkg_name}: {e}")
        return g, working, dep_dict

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return g, working, dep_dict

    #결과값 없으면 탈출
    if not isinstance(dep_dict, dict):
        print(f"[-] get_onewalk_dep(): No dependencies for {pkg_name}.")
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
        
def add_subgraph_to_main_graph(main_graph, subgraph):
    """
    Description: 서브그래프의 노드와 엣지를 메인 그래프에 추가합니다.
    - Input: main_graph - 메인 그래프
             subgraph - 추가할 서브그래프
    """
    # 서브그래프의 노드를 메인 그래프에 추가
    for node in subgraph.nodes():
        main_graph.add_node(node)
    
    # 서브그래프의 엣지를 메인 그래프에 추가
    for edge in subgraph.edges():
        main_graph.add_edge(edge)

def make_subgraph(g, pkg_name, pkg_version, working, dep_dict): 
    print(f"[-] After dep_dict = {dep_dict}")
    for name, version in dep_dict.items():
        #정규표현화된 버전정보를 working 리스트에 저장
        pkg_str = f"{name}@{version}"
        working.append(pkg_str)

        #새로운 subgraph를 만들기전 이미 있는 그래프인지 아닌지 확인
        if g.get_subgraph(name):
            if name.get_node(version):
                pass
            name.add_node('version')

        #없다면 새롭게 만들기. 패키지 name이 subgraph의 이름이 되고, 패키지 version이 노드의 이름이 된다.
        subgraph_name = "name"
        g.subgraph(name=subgraph_name)
        subgraph = g.get_subgraph(subgraph_name)
        subgraph.graph_attr['label'] = name  # 라벨은 시각화를 위한 듯
        
        # Add nodes with versions to the subgraph
        subgraph.add_node(version)

        #서브그래프는 있어도 자식노드와 연결시키는 엣지는 없을 수 있음
        for sg in g.subgraphs():
            if sg.name == pkg_name:
        # 노드 찾기 및 연결
                if sg.has_node(pkg_version):
                    g.add_edge(pkg_version, version)
                    print(f"Edge added between {pkg_name}의 {pkg_version} and {name}의 {version}")
    
    return g, working

 
 
def process_package(g, working):
    """
    Description: 주어진 패키지(package_name)의 종속되어있는 패키지 정보를
    그래프 g에 노드, 간선 형태로 반복 업데이트
    - Input: g
    - Output: 
    """
    print(f"+++++ process_package ")


    if working != []:
        
        package_str = working.pop(0)
        print(f"+++++ package_str = {package_str}")
        package_name, package_version = package_str.rsplit('@',1)
        print(f"+++++ package_name = {package_name}")
        print(f"+++++ package_version = {package_version}")

        g, working, dep_dict = get_onewalk_dep(g, package_name, package_version, working)
        result = make_subgraph(g, package_name, package_version, working, dep_dict)

        g = result[0]
        working_pkg_list = result[1]


        g = process_package(g, working_pkg_list)
        

    # else:
    #     print(g)
    #     return g
    #     # sys.exit()
    print(g)
    return g

def create_graph(): #그래프 만들기
    G = pgv.AGraph(directed=True)
    return G

if __name__ == "__main__":
    # STEP 1. Select a target package
    package_name = "vue" # 우리는 우선적으로 한 패키지의 최신 버전만 간주.
    package_version = "3.4.21"
    #package_name = "express" # 우리는 우선적으로 한 패키지의 최신 버전만 간주.
    #package_version = "4.19.2"
    package_str = f"{package_name}@{package_version}"

    # STEP 2. Initialize graph for the target
    print("STEP 2")
    g = create_graph()
    package_subgraph = g.subgraph(name = package_name)
    package_subgraph.graph_attr['label'] = package_name
    package_subgraph.add_node(package_version)
    
    # STEP 3. transitive check
    print("STEP 3")
    working = []
    working.append(package_str)
    g = process_package(g, working)


    # 각 서브그래프를 메인 그래프에 추가
    for sg in g.subgraphs():
        add_subgraph_to_main_graph(g, sg)

    g.layout(prog="dot")  # use dot
    g.draw("simpledep.png")

# 지금은 노드에 xlabel이 있어서 버전알 수 있음. 1-n 버전의 경우 나중에는 edge에 버전을 준다
# 딕셔너리는 중복 키 이름 저장 안됨! -> 한 패키지 저장 후 버려야?