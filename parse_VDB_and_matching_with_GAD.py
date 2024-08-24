import os
import csv

def load_cve_ids(csv_path):
    """
    Load CVE IDs and related information from the given CSV file.
    """
    cve_data = {}
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            cve_id = row['CVE IDs']
            cve_data[cve_id] = {
                'Package Name': row['Package Name'],
                'Vulnerable Version Range': row['Vulnerable Version Range'],
                'Summary': row['Summary']
            }
    return cve_data

def extract_package_name_vdb(file_name):
    """
    Extract the Package Name(VDB) from the file name.
    The package name is the string between the last '_' and the '.js@@'.
    """
    # .js@@ 기준으로 파일 이름을 분리하고, 그 앞 부분을 가져옵니다.
    before_js_part = file_name.split('.js@@')[0]
    
    # 가장 마지막 '_'와 .js@@ 사이의 문자열을 추출합니다.
    package_name_vdb = before_js_part.split('_')[-1]
    
    return package_name_vdb

def find_old_files(base_dir, cve_data):
    """
    Find OLD files in the directory structure and match them with CVE IDs.
    """
    matched_cves = []
    found_cve_ids = set()

    for root, _, files in os.walk(base_dir):
        for file_name in files:
            if file_name.endswith('_OLD.vul'):
                parts = file_name.split('_')
                cve_id = parts[0]

                if cve_id in cve_data:
                    found_cve_ids.add(cve_id)

                    # 패키지 이름 추출
                    package_name_vdb = extract_package_name_vdb(file_name)

                    # 함수 이름 추출
                    function_name = file_name.split('@@')[1].split('_')[0]

                    file_path = os.path.join(root, file_name)
                    with open(file_path, 'r', encoding='utf-8') as file:
                        file_content = file.read().strip()
                    
                    matched_cves.append({
                        'CVE IDs': cve_id,
                        'Package Name(GAD)': cve_data[cve_id]['Package Name'],
                        'Package Name(VDB)': package_name_vdb,
                        'Vulnerable Version Range': cve_data[cve_id]['Vulnerable Version Range'],
                        'Function Name': function_name,
                        'OLD File Content': file_content,
                        'Summary': cve_data[cve_id]['Summary']
                    })

    return matched_cves, found_cve_ids

def save_matched_cves(output_csv, matched_cves):
    """
    Save the matched CVEs and their details to a new CSV file.
    """
    with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['CVE IDs', 'Package Name(GAD)', 'Package Name(VDB)', 'Vulnerable Version Range', 'Function Name', 'OLD File Content', 'Summary'])
        writer.writeheader()
        for row in matched_cves:
            writer.writerow(row)

def save_unmatched_cves(output_csv, cve_data, found_cve_ids):
    """
    Save the CVEs that were not found in the directory structure to a new CSV file.
    """
    with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['CVE IDs', 'Package Name', 'Vulnerable Version Range', 'Summary'])
        writer.writeheader()
        for cve_id, details in cve_data.items():
            if cve_id not in found_cve_ids:
                writer.writerow({
                    'CVE IDs': cve_id,
                    'Package Name': details['Package Name'],
                    'Vulnerable Version Range': details['Vulnerable Version Range'],
                    'Summary': details['Summary']
                })

if __name__ == "__main__":
    # CSV 파일과 폴더 경로 설정
    csv_path = 'GAD(CVEs)_results_for_npm.csv'
    base_dir = './vul_js'  # 사용자 폴더가 있는 디렉토리 경로
    output_csv_matched = 'matched_cves(both_GAD_and_VDB).csv'
    output_csv_unmatched = 'unmatched_cves(Only_in_GAD).csv'

    # 1. CSV 파일에서 CVE IDs 로드
    cve_data = load_cve_ids(csv_path)

    # 2. 폴더를 탐색하여 OLD 파일을 찾고 CVE ID와 일치시키기
    matched_cves, found_cve_ids = find_old_files(base_dir, cve_data)

    # 3. 일치하는 CVE를 포함한 CSV 파일 저장
    save_matched_cves(output_csv_matched, matched_cves)

    # 4. 폴더에 없지만 CSV 파일에만 존재하는 CVE를 저장
    save_unmatched_cves(output_csv_unmatched, cve_data, found_cve_ids)

    print(f"Matched CVEs saved to {output_csv_matched}")
    print(f"Unmatched CVEs saved to {output_csv_unmatched}")

