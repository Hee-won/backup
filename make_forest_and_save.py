import json
import os
import subprocess
import tarfile
import shutil
import re
import sys
import pygraphviz as pgv
import csv
import datetime
from picking_tree import get_reverse_dependency_tree


def load_partial_forests(directory, g):
    """
    - Description: 주어진 디렉토리에서 'partial_forest'가 포함된 모든 JSON 파일을 찾아 읽고,
                   그 내용을 전체 그래프 g에 통합합니다.
    - Input: directory - JSON 파일이 저장된 디렉토리 경로, g - 전체 그래프 객체
    - Output: 통합된 전체 그래프 g
    """
    for filename in os.listdir(partial_forest_directory):
        if 'partial_forest' in filename and filename.endswith('.json'):
            print("Find partial forest")
            file_path = os.path.join(directory, filename)
            print(f"Loading {file_path}")
            
            # JSON 파일 읽기
            with open(file_path, 'r') as file:
                partial_forest = json.load(file)
            
            # 노드 추가
            for node in partial_forest.get("nodes", []):
                if not g.has_node(node):
                    g.add_node(node)
            
            # 엣지 추가
            for edge in partial_forest.get("edges", []):
                source, target = edge
                if not g.has_edge(source, target):
                    g.add_edge(source, target)
    if g is None:
        raise ValueError("Function 'load_partial_forests' returned None")
    return g

def read_dependencies(pkg_name, pkg_version):
    """
    - Description: 저장된 dependencies 폴더의 JSON 파일에서 의존성 정보 읽기
    - Input: 의존성을 알고싶은 패키지 이름과 버전
    - Output: 의존성 정보
    """
    # 첫 번째 폴더(dependencies)에서 파일을 찾기
    filename = f"{pkg_name.replace('/', '%')}@{pkg_version}_dependencies.json"
    file_path = os.path.join('dependencies', filename)
    
    # 파일이 없으면 두 번째 폴더(versions_new)에서 검색
    if not os.path.exists(file_path):
        print(f"Dependencies file not found in dependencies folder for {pkg_name}@{pkg_version}. \nSearching in versions_new folder...")
        file_path = os.path.join('versions_new', filename)
    
    # 최종적으로 파일이 존재하는지 확인하고 읽기
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Dependencies file not found in both folders for {pkg_name}@{pkg_version}")
        return {}
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return {}

def read_versionList(pkg_name, pkg_version):
    """
    - Description: 저장된 versions 폴더의 JSON 파일에서 버전 정보 읽기 for semver
    - Input: 어떤 버전이 있는지 알고싶은 패키지 이름과 버전
    - Output: 버전 정보
    """

    """ 저장된 JSON 파일에서 버전 정보 읽기 """
    filename = f"{pkg_name.replace('/', '%')}@{pkg_version}_versionList.json"
    try:
        with open(os.path.join('versions', filename), 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Dependencies file not found for {pkg_name}@{pkg_version}")
        return {}
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return {}

def get_latest_version(version_range, all_versions):
    """
    - Description: 주어진 패키지의 종속 패키지들을 semantic versioning화
    - Input: package.json에 있는 버전정보, npm에 올라온 모든 버전 metadata 정보
    - Output: 
    """
    try:
        # Node.js 스크립트에서 semver.maxSatisfying을 사용하여 최신 버전을 찾음
        # Destfying 논문처럼 바꿔줘야함
        node_script = f"""
        const semver = require('semver');
        const versions = {json.dumps(all_versions)};
        const range = '{version_range}';
        console.log(semver.maxSatisfying(versions, range));
        """
        result = subprocess.run(['node', '-e', node_script], capture_output=True, text=True, check=True)
        latest_version = result.stdout.strip()
        print(f"[+] latest_version: {latest_version}")
        return latest_version
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        return None

def get_onewalk_dep(g, pkg_name, pkg_version, working):
    """
    - Description: 주어진 패키지의 종속 패키지들을 확인 + 정규화
    - Input: 지금까지 만든 graph, 검사하고 싶은 패키지 이름, 버전
    - Output: 'name: version (json)' 형식으로 만들어진 dictionary 
    """

    print(f"+++++ get_onewalk_dep for {pkg_name}")
    dep_dict = {}
    try:
        dep_result = read_dependencies(pkg_name, pkg_version)
        print(f"+++++ dep_result: {dep_result}")
        # view 한 의존성 저장
        dep_dict = dep_result

    except subprocess.CalledProcessError as e:
        print(f"Error occurred while fetching dependencies for {pkg_name}: {e}")
        return g, working, dep_dict

    except json.JSONDecodeError as e:
        # 다음 디펜던시가 없어서 발생
        print(f"JSON decode error: {e}")
        return g, working, dep_dict

    # 결과값 없으면 탈출
    if not isinstance(dep_dict, dict):
        #print(f"[-] get_onewalk_dep(): No dependencies for {pkg_name}.")
        return g, working, dep_dict

    for name, version_range in dep_dict.items():
        try:
            # npm view 명령어를 사용하여 모든 버전을 가져오기
            dep_result = subprocess.run(['npm', 'view', name, 'versions', '--json'], capture_output=True, text=True, check=True)
            all_versions = json.loads(dep_result.stdout)

            # 최신 버전 가져오기
            latest_version = get_latest_version(version_range, all_versions)

            if latest_version:
                dep_dict[name] = latest_version
            else:
                dep_dict[name] = "0.0.0"
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while fetching versions for {name}: {e}")
            dep_dict[name] = "0.0.0"
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            dep_dict[name] = "0.0.0"

    return g, working, dep_dict

        

def make_subgraph(g, pkg_name, pkg_version, working, dep_dict):
    """
    - Description: pkg_name에 맞는 서브그래프를 그리고 working 리스트 업데이트
    - Input: 전체 그래프 g, upstream 패키지 이름, 버전, 
    - Output:
    ** upstream 정보: 'pkg_name@pkg_version'
    ** downstream 정보: 'name@version'
  
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
        else:
            #이 패키지 이름으로 만들어진 서브그래프가 없음 = 처음 나온 패키지라는 뜻!
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

def create_graph(): 
    """
    - Description: 그래프 만들기
    - Input: 
    - Output: 초기화된 그래프 g
    """
    G = pgv.AGraph(directed=True)
    return G


# 그래프를 JSON 형식으로 직렬화하여 저장
def save_graph_as_json(G):
    """
    - Description: 그래프를 변환해서 json 형태로 저장
    - Input: 모든 패키지 info가 추가된 그래프 g
    - Output: json 파일 (return 값 없음)
    """
    # 
    graph_dict = {
        'nodes': list(G.nodes()),
        'edges': list(G.edges())
    }

    with open("entire_forest.json", 'w') as f:
        json.dump(graph_dict, f)  # JSON 파일로 저장

def process_packages_from_csv(lines_to_process, g):
    """
    - Description: csv의 패키지이름과 패키지버전 정보를 읽어 transitive하게 그래프 g를 만듭니다.
    - Input: 모든 패키지 info가 있는 csv, 초기화되어있는 그래프 g
    - Output: 모든 패키지 info가 추가된 그래프 g
    """

    for row in lines_to_process:
        package_name = row[0]  # 첫 번째 열의 값은 the package name
        package_versions = row[1:]  # All subsequent columns are versions
        #print(f"[[[process_packages_from_csv]]] package_name : {package_name}")
        #print(f"[[[process_packages_from_csv]]] package_versions : {package_versions}")

        # 각 버전에 대해 개별 노드를 생성
        for version_group in package_versions:
            versions = version_group.split(',')  # 쉼표로 구분된 버전들을 개별적으로 분리
            for version in versions:
                #print(f"[[[process_packages_from_csv]]] version : {version}")
                version = version.strip()
                # 현재 시간 가져오기
                current_time = datetime.datetime.now()
                print(f"\n\n현재 시간:", current_time)
                package_str = f"{package_name}@{version}"
                print(f"Processing {package_str}")

                package_subgraph = g.subgraph(name = package_name)
                package_subgraph.graph_attr['label'] = package_name
                package_subgraph.add_node(package_str)

                # Prepare to check dependencies and process them 전의적의존성 체크
                working = []
                working.append(package_str)
                this_graph = process_package(g, working)
                g = combine_graphs(this_graph, g)

    # After processing all rows, save the graph structure
    save_graph_as_json(g)

    # Additional processing or output
    for sg in g.subgraphs():
        print(sg)
        print("Subgraph name:", sg.name)

    return g


def seperate_csv(csv_path, csv_line, g): 
    """
    - Description: input으로 csv 파일과 라인 번호를 받아 라인 10씩 쪼갠 값을 리턴
    - Input: csv 파일 주소, line 수
    - Output: 
    """
    try:
        with open(csv_path, mode='r', encoding='utf-8', newline='') as file:
            reader = csv.reader(file)
            for _ in range(csv_line - 1):  # 시작 라인까지 스킵
                next(reader)

            lines_to_process = []

            for line_number, row in enumerate(reader, start=csv_line):
                lines_to_process.append(row)

                if len(lines_to_process) == 10:
                    # 10줄을 다 모으면 process_packages_from_csv 함수 호출
                    #print(f"[+++++++++++++++] lines_to_process = {lines_to_process}")
                    g = process_packages_from_csv(lines_to_process, g)
                    #print(f"[+++++++++++++++] ggggggggggggggggggggggggggggggggggggggg = {g}")
                    lines_to_process = []
                    current_line = line_number + 1  # 현재 라인 번호를 업데이트

            # 남은 줄이 있다면 마지막으로 처리
            if lines_to_process:
                #print(f"[+++++++++++++++] last lines_to_process = {lines_to_process}")
                g = process_packages_from_csv(lines_to_process,g)
                #print(f"Middle ggggggggggggggggggggggggggggggggggggggg : {g}")
        return g
    except FileNotFoundError:
        print(f"Error: File '{csv_path}' not found.")
    except csv.Error as e:
        print(f"Error processing CSV file at line {csv_line}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":

    # partial_forest.json 파일들이 있는 디렉토리 경로 설정
    partial_forest_directory = './'

    # 사용자 입력을 받아서 뽑을 tree 정함
    if len(sys.argv) != 3:
        print("[ERROR] Usage: python3 script_name.py tree_package_name tree_package_version\n This code returns the downstream graph that depends on 'tree_package_name'@'tree_package_version'")
    
    else:
        tree_name = sys.argv[1]  # 첫 번째 인자는 패키지 이름
        tree_version = sys.argv[2]  # 두 번째 인자는 패키지 버전
        print(f"[+] TREE_NAME : {tree_name}")
        print(f"[+] TREE_VERSION : {tree_version}")

    g = create_graph()

    # partial_forest들을 전체 그래프 g에 통합
    g = load_partial_forests(partial_forest_directory, g)

    #포레스트를 구성할 패키지 정보가 담긴 csv
    csv_path = './info_packages/info_packages8.csv'
    g = seperate_csv(csv_path, 2, g)
    if g is None:
        raise ValueError("'load_partial_forests' returned None")

    print(f"Last ggggggggggggggggggggggggggggggggggggggg : {g}")

    # 최종적으로 그래프를 레이아웃하고 저장
    if g is not None:
        g.layout(prog="dot")  # use dot
        g.draw("popular_forest.pdf")  # Save as PDF format
    else:
        print("Error: Graph 'g' is None")

    #tree 뽑는 과정 ing..
    print("tree 뽑는 과정 ing..")
    reverse_dependency_tree = get_reverse_dependency_tree(tree_name, tree_version, g)

    if reverse_dependency_tree is not None:
        reverse_dependency_tree.layout(prog="dot")
        reverse_dependency_tree.draw("reverse_dependency_tree.pdf")
        print("SUCCESS :D")


    """
    - Description: 
    - Input: 
    - Output: 
    """