import json
import os
import subprocess
import tarfile
import shutil
import re
import sys
import pygraphviz as pgv
from collections import deque


def get_onewalk_dep(pkg_name, pkg_version): 
    print(f"+++++ get_onewalk_dep for {pkg_name}")

    """
    - Description: 주어진 패키지의 종속 패키지들을 확인 + 정규화
    - Input: 지금까지 만든 graph, 검사하고 싶은 패키지 이름, 버전
    - Output: 'name: version (json)' 형식으로 만들어진 dictionary 
    """

    dep_result = subprocess.run(['npm', 'view', pkg_name, 'dependencies', '--json'], capture_output=True, text=True, check=True)
    #view 한 의존성 저장
    dep_dict = json.loads(dep_result.stdout)

    #결과값 없으면 탈출
    if not isinstance(dep_dict, dict):
        print(f"[-] get_onewalk_dep(): No dependencies for {pkg_name}.")
        return False
    for name, version in dep_dict.items():
        version_list = []
        # 특수 문자를 제거하고 숫자만 추출
        version_numbers = re.findall(r'\d+', version)
        #버전 정보가 있을 경우, n.n.n 저장
        if version_numbers:
            version_str = ".".join(version_numbers)
            dep_dict[name] = version_str
        else:
            # 버전 정보가 없을 경우, 0.0.0으로 지정
            version_list.append("0.0.0")
    
    visited_str = f"{package_name}@{package_version}"
    # 이미 방문한 적 없는지 확인
    if visited_str not in visited:
        visited.append(visited_str)

    return dep_dict, visited

def make_subgraph(g, dep_dict, parents_name, parents_version):
    print(f"+++++ make_subgraph for {parents_name}")
    print(f"+++++ dep_dict for {dep_dict}")
    """
    - Description: 패키지 이름인 subgraph 만들기
    - Input: 
    - Output: 패키지의 이름을 가지고 그 안에 버전이름 노드가 있는 그래프 리턴
    """
    # Create a subgraph with the package_name as the name
    for name, version in dep_dict.items():

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

        #엣지는 ..?
        #g.add_edge('version', 'parents_version')

    return g
 
 
def process_package(g, visited):
    """
    Description: 주어진 패키지(package_name)의 종속되어있는 패키지 정보를
    그래프 g에 노드, 간선 형태로 반복 업데이트
    - Input: g
    - Output: 
    """
    print("process_package")

    
    temp_dep_dict = {}

    #다음 depth의 children 받아오기
    result = get_onewalk_dep(pkg_name, pkg_version, visited)
    temp_dep_dict = result[0]
    visited = result[1]

    print(f"+++++ process_package ----- temp_dep_dict : {temp_dep_dict}")



    for name, version in temp_dep_dict.items():
        if "{name}@{version}" not in visited and
            g = make_subgraph(g, {name, version}, pkg_name, pkg_version)
    else

        process_package


    # While True:
        
    #     #다음으로 처리?해야하는 패키지 리스트에 저장
    #     working_pkg_list.append(temp_dep_dict)

    #     #해당 경로에서 다음 depth에 패키지가 있는 경우, 서브그래프 만들기
    #     if working_pkg_list != {} and visited != {}:

    #         



    #     #해당 경로에서 다음 depth 로 이동
    #     elif working_pkg_list == {} and temp_dep_dict != {}:
    #         for name, version in temp_dep_dict.items():
    #             process_package(g, name, version, visited)

    #         temp = working_pkg_list.popleft
    #         (g, temp.keys(), temp.values(),working_pkg_list)

    #         #초기화
    #         temp_dep_dict = {}

    #     #해당 경로에서 다음 depth에도 패키지가 없고 siblings도 없는 경우 = 끝남
    #     else:
    #         sys.exit()

def create_graph(): #그래프 만들기
    G = pgv.AGraph(directed=True)
    return G

if __name__ == "__main__":
    # STEP 1. Select a target package
    package_name = "express" # 우리는 우선적으로 한 패키지의 최신 버전만 간주.
    package_version = "4.19.2"
    package_str = f"{package_name}@{package_version}"

    # STEP 2. Initialize graph for the target
    print("STEP 2")
    g = create_graph()
    package_subgraph = g.subgraph(name = package_name)
    package_subgraph.graph_attr['label'] = package_name
    package_subgraph.add_node(package_version)
    
    # STEP 3. transitive check
    print("STEP 3")
    working_pkg_list = deque()

    # STEP 4. Process the selected package
    print("STEP 4")
    visited = []
    visited.append(package_str)
    print(f"visited = {visited}")
    print(f"g = {g}")
    process_package(g, visited)

    g.layout(prog="dot")  # use dot
    g.draw("simpledep.png")

# 지금은 노드에 xlabel이 있어서 버전알 수 있음. 1-n 버전의 경우 나중에는 edge에 버전을 준다
# 딕셔너리는 중복 키 이름 저장 안됨! -> 한 패키지 저장 후 버려야?