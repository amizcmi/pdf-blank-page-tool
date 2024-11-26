"""
PDF空白页添加工具 v0.2
功能：
1. 支持单个/批量PDF处理
2. 支持添加空白页和解密功能
3. 支持自定义输出文件名
4. 支持多种页码范围输入格式
5. Web界面操作

版本说明：
- v0.2: 当前版本，完善功能和打包
- v0.1: 基础功能实现
"""

from flask import Flask, render_template, request, send_file
import PyPDF2
from datetime import datetime
import os
import tempfile
import zipfile
import io
import socket

app = Flask(__name__)
UPLOAD_FOLDER = tempfile.gettempdir()

def parse_page_numbers(page_string, total_pages=None):
    """解析页码字符串，支持逗号分隔和范围表示"""
    # 如果输入0，表示只解密文档
    if page_string.strip() == '0':
        return []
    
    if page_string.lower() == 'all' and total_pages is not None:
        return list(range(1, total_pages + 1))
    
    result = set()
    parts = page_string.split(',')
    for part in parts:
        if '-' in part:
            start, end = map(int, part.split('-'))
            result.update(range(start, end + 1))
        else:
            result.add(int(part))
    return sorted(list(result))

def get_pdf_page_count(pdf_path):
    """获取PDF的总页数"""
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            if pdf_reader.is_encrypted:
                try:
                    # 尝试使用空密码解密
                    pdf_reader.decrypt('')
                except:
                    raise Exception("PDF文件已加密且无法自动解密，请先解除PDF的加密保护")
            return len(pdf_reader.pages)
    except Exception as e:
        raise e

def add_blank_pages(pdf_path, page_numbers, custom_filename=None):
    pdf_writer = PyPDF2.PdfWriter()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # 获取原文件名（不含路径和扩展名）
    original_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    
    if custom_filename:
        # 确保文件名以.pdf结尾
        if not custom_filename.lower().endswith('.pdf'):
            custom_filename += '.pdf'
        output_filename = custom_filename
    else:
        # 如果是解密操作，使用"解密-原文件名.pdf"的格式
        if not page_numbers:  # 空列表表示只解密
            output_filename = f'解密-{original_filename}.pdf'
        else:
            output_filename = f'空白页-{original_filename}.pdf'
    
    output_path = os.path.join(UPLOAD_FOLDER, output_filename)
    
    # 如果文件已存在，在文件名后添加时间戳
    if os.path.exists(output_path):
        filename_without_ext = os.path.splitext(output_filename)[0]
        output_filename = f'{filename_without_ext}_{timestamp}.pdf'
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
    
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        if pdf_reader.is_encrypted:
            try:
                # 尝试使用空密码解密
                pdf_reader.decrypt('')
            except:
                raise Exception("PDF文件已加密且无法自动解密，请先解除PDF的加密保护")
        
        for i in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[i]
            pdf_writer.add_page(page)
            # 只有在不是解密模式时才添加空白页
            if page_numbers and i + 1 in page_numbers:
                pdf_writer.add_blank_page()
        
        with open(output_path, 'wb') as output_pdf:
            pdf_writer.write(output_pdf)
    
    return output_path

def get_local_ip():
    """获取本机局域网IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 1))  # 连接外网IP（不需要真实连接）
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return '127.0.0.1'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-page-count', methods=['POST'])
def get_page_count():
    if 'pdf_file' not in request.files:
        return {'error': '没有上传文件'}, 400
    
    file = request.files['pdf_file']
    if file.filename == '':
        return {'error': '没有选择文件'}, 400
    
    if file:
        temp_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(temp_path)
        try:
            page_count = get_pdf_page_count(temp_path)
            os.remove(temp_path)
            return {'page_count': page_count}
        except Exception as e:
            return {'error': str(e)}, 500

@app.route('/convert', methods=['POST'])
def convert():
    if 'pdf_file' not in request.files:
        return '没有上传文件', 400
    
    files = request.files.getlist('pdf_file')
    page_string = request.form['page_range']
    custom_filename = request.form.get('custom_filename', '').strip()
    
    if not files or files[0].filename == '':
        return '没有选择文件', 400
    
    # 如果只有一个文件，直接处理并返回PDF
    if len(files) == 1:
        file = files[0]
        temp_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(temp_path)
        
        try:
            total_pages = get_pdf_page_count(temp_path)
            page_numbers = parse_page_numbers(page_string, total_pages)
            output_path = add_blank_pages(temp_path, page_numbers, custom_filename)
            
            # 删除临时上传的文件
            os.remove(temp_path)
            
            # 读取处理后的文件并返回
            response = send_file(
                output_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=os.path.basename(output_path)
            )
            
            # 发送文件后删除它
            @response.call_on_close
            def cleanup():
                if os.path.exists(output_path):
                    os.remove(output_path)
            
            return response
            
        except Exception as e:
            return f'处理文件时出错：{str(e)}', 500
    
    # 如果是多个文件，创建ZIP
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for file in files:
            temp_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(temp_path)
            
            try:
                total_pages = get_pdf_page_count(temp_path)
                page_numbers = parse_page_numbers(page_string, total_pages)
                output_path = add_blank_pages(temp_path, page_numbers, None)
                
                # 将处理后的文件添加到ZIP中
                arcname = os.path.basename(output_path)
                zf.write(output_path, arcname)
                
                # 清理临时文件
                os.remove(temp_path)
                os.remove(output_path)
                
            except Exception as e:
                return f'处理文件 {file.filename} 时出错：{str(e)}', 500
    
    # 设置ZIP文件的名称
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    if custom_filename:
        zip_filename = f'{custom_filename}_{timestamp}.zip'
    else:
        zip_filename = f'PDF处理结果_{timestamp}.zip'
    
    # 返回ZIP文件
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_filename
    )

@app.route('/network-info')
def network_info():
    """获取网络信息"""
    port = app.config.get('SERVER_PORT', 5000)
    local_ip = get_local_ip()
    return {
        'localhost_url': f'http://localhost:{port}',
        'network_url': f'http://{local_ip}:{port}',
        'port': port,
        'local_ip': local_ip
    }

if __name__ == '__main__':
    app.run(debug=True)