import json
import os
import subprocess
import tarfile
import shutil
import re
import pygraphviz as pgv

nodes_str_list = []

def crawling_versions(package_name): # 패키지 전체 버전 가져오기 + node 만들기
    print("crawling_versions")
    valid_versions = []
    try:
        # npm view 명령으로 버전 정보를 JSON 형태로 가져옵니다.
        time_result = subprocess.run(['npm', 'view', package_name, 'time', '--json'], capture_output=True, text=True, check=True)
        package_times = json.loads(time_result.stdout)
        
        # '숫자.숫자.숫자' 형태의 버전만 필터링합니다.
        valid_versions = [version for version in package_times if re.match(r'^\d+\.\d+\.\d+$', version)]
        #print(valid_versions)
    except Exception as e:
            # 기타 예외 처리
        print(f"Error processing {name}: {e}")
    
    node_str = create_node(package_name, valid_versions)

    return node_str


def crawling_dependencies(package_name): #패키지 의존성 가져오기
    parsed_dependencies = {}
    try:
        dep_result = subprocess.run(['npm', 'view', package_name, 'dependencies', '--json'], capture_output=True, text=True, check=True)
        package_dependencies = json.loads(dep_result.stdout)
        #print(f"package_dependencies : {package_dependencies}")
        # package_dependencies가 딕셔너리인지 확인
        if not isinstance(package_dependencies, dict):
            print(f"No dependencies found for {package_name} or unexpected response format.")
            return parsed_dependencies
    # 특수 문자를 제거하고 버전 정보를 0.0.0 형식으로 변환하여 저장
        for name, version in package_dependencies.items():
            # 특수 문자를 제거하고 숫자만 추출하여 버전 정보로 저장
            version_numbers = re.findall(r'\d+', version)
            if version_numbers:
                version_str = ".".join(version_numbers)
                parsed_dependencies[name] = version_str
            else:
                # 버전 정보가 없을 경우 0.0.0으로 지정
                parsed_dependencies = "0.0.0"
        print(f"parsed_dependencies : {parsed_dependencies}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to get dependencies for {package_name}: {e}")
    except Exception as e:
        print(f"Error processing {package_name}: {e}")

    return parsed_dependencies

def create_node(package_name, valid_versions): # 노드로 만들기
    label = '|'.join(f'<{ver}> {ver}' for ver in valid_versions)
    node_str = f'"{package_name}" [\nlabel = "{label}"\nshape = "record"\n];'
    return node_str

def create_edge(package_name, package_version, new_pkg_name, new_pkg_ver):
    edge_str = f'"{package_name}":"<{package_version}> {package_version}" -> "{new_pkg_name}":"<{new_pkg_ver}> {new_pkg_ver}";'
    return edge_str

def deduplicate_node(package_name): #이미 만들어져있는 노드인지 체크
    global nodes_str_list
    pattern = r'\b' + re.escape(package_name) + r'\b'
    # 패턴 매칭 시도
    if re.search(pattern, text):
        print(f"'{package_name}' is found as a standalone word in the text.")
        return False
    else:
        print(f"'{package_name}' is NOT found as a standalone word in the text.")
        return True

def create_graph(nodes, edges): #그래프 만들기
    G = pgv.AGraph(directed=True)


def process_package(package_name, package_version):
    global nodes_str_list
    """주어진 패키지에 대해 모든 작업을 수행합니다."""
    #노드(= vertex, 정점) 만들기
    crawling_ver_result = crawling_versions(package_name) 
    nodes_str_list.append(crawling_ver_result)
    #print(f"nodes_str_list : {nodes_str_list}")

    #엣지(= 간선) 만들기
    crawling_dep_result = crawling_dependencies(package_name)
    
    if crawling_dep_result:
        if deduplicate_node:
            for new_pkg_name, new_pkg_ver in crawling_dep_result.items():
                create_edge(package_name, package_version, new_pkg_name, new_pkg_ver)
                #Transitive 반복
                process_package(new_pkg_name)
                print(f"new_pkg_name: {new_pkg_name}")
                print(f"new_pkg_ver: {new_pkg_ver}")

    #create_graph(node_str)
    

if __name__ == "__main__":
    input_file = "name.json"  # 입력 파일 이름 지정 
    with open(input_file, "r") as file:
        package_names = json.load(file)
    for package_name in package_names:
    # 여기에 패키지 이름에 대한 작업 수행
        #print(f"+++++++++ package_name : {package_name}")
        process_package(package_name)
