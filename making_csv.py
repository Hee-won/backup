import json
import os
import csv
import re
import datetime
import glob

def read_json_file(json_file_path):
    """ JSON 파일 읽기 """
    with open(json_file_path, 'r') as file:
        return json.load(file)


def get_versions(pkg_name, versions_folder):
    """ 버전 리스트 파일 읽기 및 처리 """
    version_pattern = re.compile(r'^\d+\.\d+\.\d+$')  # n.n.n 형식만 매칭
    versions_list = []

    # 해당 패키지 이름을 포함하는 모든 버전 리스트 파일 검색
    version_files = glob.glob(os.path.join(versions_folder, f"{pkg_name.replace('/', '%')}@*_versionList.json"))
    for version_file in version_files:
        with open(version_file, 'r') as f:
            versions = json.load(f)
            # n.n.n 형식의 버전만 필터링
            filtered_versions = [v for v in versions if version_pattern.match(v)]
            versions_list.extend(filtered_versions)

    return versions_list

def write_to_csv(data, output_csv_path):
    """ CSV 파일로 데이터 쓰기 """
    with open(output_csv_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for row in data:
            writer.writerow(row)

def main(json_file_path, versions_folder, output_csv):
    # JSON 파일에서 패키지 이름 읽기
    package_names = read_json_file(json_file_path)

    # CSV 파일 헤더
    with open(output_csv, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Package Name", "Versions"])

    # 각 패키지에 대해 메타데이터 존재 여부 및 버전 처리
    for pkg_name in package_names:
        # 현재 시간 가져오기
        current_time = datetime.datetime.now()

        # 현재 시간 출력
        print(f"\n\n현재 시간:", current_time)
        print(f"Processing package: {pkg_name}")
      
        versions = get_versions(pkg_name, versions_folder)
        if versions:
            print(f"versions of {pkg_name}: {versions}")
            # CSV에 데이터 추가
            write_to_csv([[pkg_name, ", ".join(versions)]], output_csv)
        else:
            print(f"No valid versions found for {pkg_name}")


# 파일 경로 설정
json_file_path = 'all_npm_package_names_240515_ORIGINAL3.json'
versions_folder = './versions'
output_csv = 'info_packages3.csv'

# 스크립트 실행
if __name__ == "__main__":
    main(json_file_path, versions_folder, output_csv)

