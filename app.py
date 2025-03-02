from flask import Flask, request, render_template, jsonify, send_file
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

# CSV 파일 경로 설정
CSV_FILE = 'names.csv'
ADMIN_PASSWORD = '3051330513'  # 관리자 비밀번호 설정

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            data = request.get_json()
            name = data.get('name')
            student_id = data.get('student_id')
            if name and student_id:
                # Check for existing entry before saving
                if check_existing_entry(name, student_id):
                    return jsonify(success=False, error="Already rented"), 400

                success = save_name_to_csv(name, student_id)
                if success:
                    return jsonify(success=True)
                else:
                    return jsonify(success=False, error="Failed to save data"), 500
            else:
                return jsonify(success=False, error="Name or student ID is missing"), 400
        except Exception as e:
            print(f"Exception occurred: {e}")
            return jsonify(success=False, error="Exception occurred"), 500
    return render_template('index.html')

@app.route('/admin')
def admin():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            if df.empty:
                raise pd.errors.EmptyDataError
            rows = df.to_dict(orient='records')
        except pd.errors.EmptyDataError:
            rows = []
        except Exception as e:
            print(f"Exception occurred while reading CSV: {e}")
            rows = []
    else:
        rows = []

    return render_template('admin.html', rows=rows)

@app.route('/check_password', methods=['POST'])
def check_password():
    data = request.get_json()
    password = data.get('password')
    if password == ADMIN_PASSWORD:
        return jsonify(success=True)
    else:
        return jsonify(success=False)

@app.route('/check_existing', methods=['POST'])
def check_existing():
    data = request.get_json()
    name = data.get('name')
    student_id = data.get('student_id')

    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            # Check if the entry exists in the CSV
            if '학번' in df.columns and '이름' in df.columns:
                exists = df[(df['학번'].astype(str) == str(student_id)) & (df['이름'] == name)].shape[0] > 0
                return jsonify(exists=exists)
            else:
                return jsonify(exists=False, error="Invalid CSV columns"), 500
        except Exception as e:
            print(f"Exception occurred while checking existing entry: {e}")
            return jsonify(exists=False, error="Error checking existing entry"), 500
    else:
        return jsonify(exists=False, error="CSV file not found"), 500

def check_existing_entry(name, student_id):
    """Check if a record with the given name and student_id exists in the CSV file."""
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            # Check for matching name and student_id
            if '학번' in df.columns and '이름' in df.columns:
                if not df[(df['학번'].astype(str) == str(student_id)) & (df['이름'] == name)].empty:
                    return True
            return False
        except Exception as e:
            print(f"Exception occurred while checking existing entry: {e}")
            return False
    return False

def save_name_to_csv(name, student_id):
    try:
        # 현재 시간을 문자열로 포맷, 초 단위까지 포함
        current_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        
        # 기존 CSV 파일이 있는 경우 읽어오기
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            if df.columns.tolist() != ['시간', '학번', '이름']:
                # 파일의 열이 예상과 다를 경우, 새로 생성
                df = pd.DataFrame(columns=['시간', '학번', '이름'])
        else:
            df = pd.DataFrame(columns=['시간', '학번', '이름'])

        # 새로 입력된 데이터를 DataFrame에 추가
        new_entry = pd.DataFrame({'시간': [current_time], '학번': [student_id], '이름': [name]})
        df = pd.concat([df, new_entry], ignore_index=True)

        # DataFrame을 CSV 파일로 저장
        df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')  # UTF-8로 인코딩, BOM 포함
        return True
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return False

@app.route('/download_csv')
def download_csv():
    if os.path.exists(CSV_FILE):
        return send_file(CSV_FILE, as_attachment=True)
    return "CSV 파일이 존재하지 않습니다.", 404

@app.route('/delete_row', methods=['POST'])
def delete_row():
    student_id = request.form.get('student_id')
    name = request.form.get('name')

    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            if '학번' in df.columns and '이름' in df.columns:
                # 특정 행 삭제
                df = df[~((df['학번'].astype(str) == str(student_id)) & (df['이름'] == name))]
                df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
                return '', 204
            else:
                return "CSV 파일의 열이 올바르지 않습니다.", 500
        except Exception as e:
            print(f"Exception occurred while deleting row: {e}")
            return "서버 오류", 500
    return "CSV 파일이 존재하지 않습니다.", 404

if __name__ == '__main__':
    app.run(debug=True)
