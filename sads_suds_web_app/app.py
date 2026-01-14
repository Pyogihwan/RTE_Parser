from flask import Flask, render_template, request, send_file, redirect, url_for, flash, jsonify
import os
import tempfile
import shutil
from datetime import datetime
from autosar_pipeline import load_c_files_from_directory, run_pipeline

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Configure upload and output folders
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_directory():
    directory_path = request.form.get('directory_path', '').strip()
    
    if not directory_path:
        flash('디렉토리 경로를 입력해주세요.', 'error')
        return redirect(url_for('index'))
    
    if not os.path.exists(directory_path):
        flash(f'디렉토리를 찾을 수 없습니다: {directory_path}', 'error')
        return redirect(url_for('index'))
    
    if not os.path.isdir(directory_path):
        flash(f'유효한 디렉토리가 아닙니다: {directory_path}', 'error')
        return redirect(url_for('index'))
    
    try:
        # Load C files from directory
        source_files = load_c_files_from_directory(directory_path)
        
        if not source_files:
            flash('지정된 디렉토리에서 C 파일을 찾을 수 없습니다.', 'error')
            return redirect(url_for('index'))
        
        # Generate unique filename for output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"sads_suds_extract_{timestamp}.csv"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # Run pipeline
        build_config = {
            "output_csv": output_path,
            "print_issues": False
        }
        
        state = run_pipeline(source_files, build_config)
        
        # Prepare result data
        result = {
            'success': True,
            'csv_filename': output_filename,
            'total_files': len(source_files),
            'total_functions': len(state.functions),
            'total_variables': len(state.variables),
            'total_rte_interfaces': len(state.rte_interfaces),
            'swc_candidates': state.swc_candidates,
            'issues': state.issues,
            'csv_path': state.csv_path
        }
        
        return render_template('result.html', result=result)
        
    except Exception as e:
        flash(f'처리 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            flash('파일을 찾을 수 없습니다.', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'다운로드 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/api/process', methods=['POST'])
def api_process():
    """API endpoint for programmatic access"""
    data = request.get_json()
    directory_path = data.get('directory_path', '').strip()
    
    if not directory_path or not os.path.exists(directory_path) or not os.path.isdir(directory_path):
        return jsonify({'success': False, 'error': 'Invalid directory path'}), 400
    
    try:
        source_files = load_c_files_from_directory(directory_path)
        
        if not source_files:
            return jsonify({'success': False, 'error': 'No C files found'}), 400
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"sads_suds_extract_{timestamp}.csv"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        build_config = {"output_csv": output_path, "print_issues": False}
        state = run_pipeline(source_files, build_config)
        
        return jsonify({
            'success': True,
            'csv_filename': output_filename,
            'download_url': f'/download/{output_filename}',
            'total_files': len(source_files),
            'total_functions': len(state.functions),
            'total_variables': len(state.variables),
            'total_rte_interfaces': len(state.rte_interfaces),
            'swc_candidates': state.swc_candidates,
            'issues': state.issues
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
