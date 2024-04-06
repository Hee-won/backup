import json
import os
import subprocess
import tarfile
import shutil
import re
import sys
import pygraphviz as pgv


def get_onewalk_dep(g, pkg_name, pkg_version): 
    print("get_onewalk_dep")
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


            #이미 graph에 패키지 이름, 버전이 저장되어있는 건 아닌지 확인 
            if g.has_node(name) in g and g.get_node(n).xlabel in g:
                break
            #확인 후 저장  
            dep_dict[name] = version_str
        else:
            # 버전 정보가 없을 경우, 0.0.0으로 지정
            version_list.append("0.0.0")

    return dep_dict

def make_graph(g, dep_dict, pkg_name): 
    """
    - Description: 노드&엣지 추가
    - Input: 그래프 g, 각 종속 패키지의 name: version (json) 형식의 dictionary
    - Output: 노드와 엣지가 추가된 그래프 
    """
    print("make_graph")   

    for name, version in dep_dict.items():

        g.add_node(name, xlabel=version)
        g.add_edge(pkg_name, name)

    return g

def process_package(g, pkg_name, pkg_version, working_pkg_list):
    working_pkg_list.pop(0)
    print(f"working_pkg_list ============ {working_pkg_list}")
    print("process_package")
    """
    Description: 주어진 패키지(package_name)의 종속되어있는 패키지 정보를
    그래프 g에 노드, 간선 형태로 업데이트
    """

    temp_dep_dict = get_onewalk_dep(g, pkg_name, pkg_version)
    if temp_dep_dict != {}:

        g = make_graph(g, temp_dep_dict, package_name)
        for name, version in temp_dep_dict.items():
            working_pkg_list.append(name)
            process_package(g, name, version, working_pkg_list)
    else:
        sys.exit()

def create_graph(): #그래프 만들기
    G = pgv.AGraph(directed=True)
    return G

if __name__ == "__main__":
    # STEP 1. Select a target package
    package_name = "express" # 우리는 우선적으로 한 패키지의 최신 버전만 간주.
    package_version = "4.19.2"
    working_pkg_list = [] #같은 depth인 수행해야하는 패키지들 저장용도 
    working_pkg_list.append(package_name)
    # STEP 2. Initialize graph for the target
    print("STEP 2")
    g = create_graph()
    g.add_node(package_name, xlabel=package_version)

    # STEP 3. Process the selected package
    print("STEP 3")

    process_package(g, package_name, package_version, working_pkg_list)
    g.layout(prog="dot")  # use dot
    g.draw("simpledep.png")

# 지금은 노드에 xlabel이 있어서 버전알 수 있음. 1-n 버전의 경우 나중에는 edge에 버전을 준다
# 딕셔너리는 중복 키 이름 저장 안됨! -> 한 패키지 저장 후 버려야?