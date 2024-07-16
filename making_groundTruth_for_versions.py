import os
import json
import subprocess
import re
import datetime

def read_processed_packages(log_file_path):
    """ 로그 파일에서 처리된 패키지 이름을 읽어 리스트로 반환합니다. """
    processed_packages = set()
    with open(log_file_path, 'r') as log_file:
        for line in log_file:
            if "as it has been processed already." in line:
                # "Skipping {패키지 이름} as it has been processed already." 로부터 패키지 이름 추출
                prefix = "Skipping "
                suffix = " as it has been processed already."
                start = line.find(prefix) + len(prefix)
                end = line.find(suffix)
                package_name = line[start:end].strip()
                if '%' in package_name:
                    package_name = package_name.replace('%', '/')
                processed_packages.add(package_name)
            elif "++++++++++ Processing package: " in line:
                # 일반 처리 로그에서 패키지 이름 추출
                _, package_name = line.split(':', 1)
                if '%' in package_name:
                    package_name = package_name.replace('%', '/')
                processed_packages.add(package_name.strip())
    print(processed_packages)
    return processed_packages


def process_versions_folder(input_folder_path, output_folder_path, processed_packages_by_log):
    # 입력 폴더 내 모든 파일을 읽어온다
    files = os.listdir(input_folder_path)
    
    for file in files:
        if file.endswith('_versionList.json'):
            # 파일 이름에서 패키지 이름과 버전을 추출한다
            file_base = file.rsplit('_', 1)[0]
            pkg_name, pkg_version = file_base.rsplit('@', 1)
            
            # 패키지 이름에 %가 있으면 /로 변경한다
            if '%' in pkg_name:
                pkg_name = pkg_name.replace('%', '/')

            # 패키지가 이미 처리된 경우 건너뛴다
            if pkg_name in processed_packages_by_log:
                print(f"Skipping {pkg_name} as it has been processed already.")
                continue
                
            # 현재 시간 가져오기
            current_time = datetime.datetime.now()

            # 현재 시간 출력
            print(f"\n\n현재 시간:", current_time)
            print(f"++++++++++ Processing package: {pkg_name}")

            # JSON 파일을 읽어 유효한 버전만 추출한다
            with open(os.path.join(input_folder_path, file), 'r') as f:
                versions = json.load(f)
            
            valid_versions = [v for v in versions if re.match(r'^\d+\.\d+\.\d+$', v)]
            
            for version in valid_versions:
                print(f"++++++++++ Processing version: {version}")
                # 결과를 저장할 파일 이름을 구성한다
                safe_pkg_name = pkg_name.replace('/', '%')
                output_file = os.path.join(output_folder_path, f"{safe_pkg_name}@{version}_dependencies.json")
                
                # 이미 같은 이름의 JSON 파일이 존재하면 건너뛴다
                if os.path.exists(output_file):
                    print(f"Skipping {output_file} as it already exists.")
                    continue
                
                # npm view 명령을 실행하여 결과를 저장한다
                command = ['npm', 'view', f'{pkg_name}@{version}', 'dependencies', '--json']
                try:
                    result = subprocess.run(command, capture_output=True, text=True, check=True)
                    dependencies = result.stdout.strip()
                    
                    # 명령어 실행 결과가 비어있는 경우
                    if not dependencies:
                        print(f"No dependencies found for {pkg_name}@{version}.")
                        continue

                    # JSON 디코딩 시도
                    try:
                        dep_json = json.loads(dependencies)
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error for {pkg_name}@{version}: {e}")
                        continue

                    # 결과를 파일에 저장
                    try:
                        with open(output_file, 'w') as out_f:
                            json.dump(dep_json, out_f)
                    except IOError as e:
                        print(f"Error writing to file {output_file}: {e}")
                
                except subprocess.CalledProcessError as e:
                    print(f"Error occurred while fetching dependencies for {pkg_name}@{version}: {e}")


if __name__ == "__main__":
    input_folder_path = './versions'
    output_folder_path = './versions_new'
    log_file_path = 'making_groundTruth_for_versions2.log'
    
    # 결과를 저장할 폴더가 존재하지 않으면 생성합니다.
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

    # 로그 파일에서 이미 처리된 패키지 이름을 읽어옵니다.
    processed_packages_by_log = read_processed_packages(log_file_path)
    
    # 버전 폴더 처리
    process_versions_folder(input_folder_path, output_folder_path, processed_packages_by_log)
