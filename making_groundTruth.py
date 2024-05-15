import json
import subprocess

def process_package(pkg_name):
    try:
        # npm view 명령 실행
        dep_result = subprocess.run(['npm', 'view', pkg_name, '--json'], 
                                    capture_output=True, text=True, check=True)
        dep_data = json.loads(dep_result.stdout)

        with open(f"./metadata/{pkg_name}_metadata.json", 'w') as outfile:
            json.dump(dep_data, outfile)

        # "_id" 정보 추출
        pkg_id = dep_data.get("_id")
        if pkg_id:
            # "_id" 정보에서 이름과 버전 추출
            current_name, current_version = pkg_id.rsplit("@", 1)
            print(f"Package Name: {current_name}, Version: {current_version}")

            # 버전 정보 저장
            with open(f"./versions/{current_name}@{current_version}_versionList.json", 'w') as version_file:
                json.dump(dep_data.get("versions"), version_file)
                print(f"Versions saved: {current_name}@{current_version}_versionList.json")

        pkg_dependency = dep_data.get("dependencies")
        if pkg_dependency:
            # 의존성 정보 저장
            dependencies = dep_data.get("dependencies", {})
            with open(f"./dependencies/{current_name}@{current_version}_dependencies.json", 'w') as dep_file:
                json.dump(dependencies, dep_file)
                print(f"Dependencies saved: {current_name}@{current_version}_dependencies.json")
        else:
            print(f"[+] No Dependencies : {current_name}@{current_version}")

    except subprocess.CalledProcessError as e:
        print(f"Error occurred while fetching information for {pkg_name}: {e}")

    except json.JSONDecodeError as e:
        print(f"JSON decode error occurred for {pkg_name}: {e}")

def main(json_file):
    # JSON 파일 읽기
    with open(json_file, 'r') as file:
        package_names = json.load(file)

    # 각 패키지에 대해 작업 수행
    for pkg_name in package_names:
        print(f"Processing package: {pkg_name}")
        process_package(pkg_name)

# JSON 파일 경로 지정
json_file = 'all_npm_package_names_24051.json'
main(json_file)