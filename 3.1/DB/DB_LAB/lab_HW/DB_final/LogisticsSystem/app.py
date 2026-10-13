from flask import Flask, render_template, request, redirect, url_for, flash
from database import DatabaseManager
import pyodbc
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 用于 Flash 消息的 Session 加密

def get_db():
    """辅助函数：获取数据库连接实例"""
    db = DatabaseManager()
    db.connect()
    return db

@app.route('/')
def index():
    return render_template('index.html')

# --- 修改部分 A: 修复 allocate 函数 (解决问题 1) ---
@app.route('/allocate', methods=['GET', 'POST'])
def allocate():
    db = get_db()
    if request.method == 'POST':
        try:
            weight = float(request.form['weight'])
            volume = float(request.form['volume'])
            destination = request.form['destination']
            vehicle_id = request.form['vehicle_id']

            db.create_order(weight, volume, destination, vehicle_id)
            flash('运单分配成功！', 'success')
            db.close()
            return redirect(url_for('allocate'))

        except pyodbc.ProgrammingError as e:
            # 专门捕获 SQL Server 的触发器错误 (RAISERROR)
            error_msg = str(e)
            # 提取 SQL 错误信息中的关键描述
            if "严重超载" in error_msg:
                flash('【操作拒绝】严重超载！分配导致超出车辆最大载重限制。', 'danger')
            else:
                flash(f'数据库错误: {error_msg}', 'danger')
                
        except pyodbc.Error as e:
            flash(f'系统错误: {e}', 'danger')
        except ValueError:
            flash('输入格式错误，重量和体积必须为数字。', 'danger')
    
    # GET 请求
    idle_vehicles = db.get_idle_vehicles()
    db.close()
    return render_template('allocate.html', vehicles=idle_vehicles)

@app.route('/entry', methods=['GET', 'POST'])
def entry():
    db = get_db()
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        if form_type == 'driver':
            name = request.form['name']
            license_grade = request.form['license_grade']
            phone = request.form['phone']
            fleet_id = request.form['fleet_id']
            
            if db.add_driver(name, license_grade, phone, fleet_id):
                flash('司机录入成功！', 'success')
            else:
                flash('司机录入失败，请检查数据。', 'danger')

        elif form_type == 'vehicle':
            plate = request.form['plate']
            try:
                max_weight = float(request.form['max_weight'])
                max_volume = float(request.form['max_volume'])
                fleet_id = request.form['fleet_id']
                
                if db.add_vehicle(plate, max_weight, max_volume, fleet_id):
                    flash('车辆录入成功！', 'success')
                else:
                    flash('车辆录入失败。', 'danger')
            except ValueError:
                flash('车辆载重和体积必须是数字。', 'danger')
        
        db.close()
        return redirect(url_for('entry'))

    # GET 请求：加载车队信息供下拉框使用
    fleets = db.get_fleets()
    db.close()
    return render_template('entry.html', fleets=fleets)

@app.route('/exception', methods=['GET', 'POST'])
def exception():
    db = get_db()
    if request.method == 'POST':
        try:
            vehicle_id = request.form['vehicle_id']
            driver_id = request.form['driver_id']
            event_type = request.form['event_type']
            occur_time = request.form['occur_time']
            fine_amount = float(request.form['fine_amount'])

            if db.add_abnormality(event_type, occur_time, fine_amount, driver_id, vehicle_id):
                flash('异常记录已保存。', 'success')
            else:
                flash('保存失败。', 'danger')
        except ValueError:
            flash('罚款金额格式错误。', 'danger')
        finally:
            db.close()
        return redirect(url_for('exception'))

    # GET 请求：加载车辆和司机列表
    vehicles = db.get_all_vehicles()
    drivers = db.get_all_drivers()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.close()
    return render_template('exception.html', vehicles=vehicles, drivers=drivers, current_time=current_time)

@app.route('/report')
def report():
    db = get_db()
    columns, rows = db.get_weekly_abnormalities()
    db.close()
    return render_template('report.html', columns=columns, rows=rows)

# --- 修改部分 B: 添加 signoff 路由 (解决问题 2) ---
@app.route('/signoff', methods=['GET', 'POST'])
def signoff():
    db = get_db()
    if request.method == 'POST':
        # 点击了“确认签收”按钮
        order_id = request.form['order_id']
        if db.complete_order(order_id):
            flash('运单已签收，车辆状态已更新。', 'success')
        else:
            flash('签收失败，请重试。', 'danger')
        db.close()
        return redirect(url_for('signoff'))

    # GET 请求：显示当前活跃的运单
    active_orders = db.get_active_orders()
    db.close()
    return render_template('signoff.html', orders=active_orders)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
