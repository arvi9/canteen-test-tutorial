from flask import (
    Flask, render_template, request,
    redirect, url_for, abort, session,
    jsonify,json
)
from flaskext.mysql import MySQL
from flask_cors import CORS, cross_origin
from datetime import datetime
from flask_mail import Mail, Message
from dateutil.relativedelta import *
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'F34TF$($e34D'


# Email configuration
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'iiitbangalore7@gmail.com'
app.config['MAIL_PASSWORD'] = 'vikaspriyaranjan'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

# Database Configuration
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '1234'
app.config['MYSQL_DATABASE_DB'] = 'mess'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)




@app.route('/shutdown')
@cross_origin()
def shutdown():
    shutdown_server()
    return 'Thank You for Using the Coffee App'

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


    #---------------------------------scanBLD API------------------------------------------------
@app.route('/scanBLD')
@cross_origin()
def buy_bld():
    
    id = request.args.get('id')
    # bld = request.args.get('bld') #bld 0-breakfast 1-lunch 2-dinner

    if not id:
        return jsonify({'message': "Please provide id", 'error': 1})

    conn = mysql.connect()
    cursor = conn.cursor()

    currentTimestamp = datetime.now()    
    currentDate = currentTimestamp.strftime('%Y-%m-%d')
    currentTime = currentTimestamp.strftime('%H:%M:%S')
    currentMonth = currentTimestamp.strftime('%Y-%m')
    currentHour = int(currentTimestamp.strftime('%H'))

    # nextmonth = currentTimestamp+relativedelta(months=+1)
    
    # print(currentMonth)
    # print(nextmonth.strftime('%Y-%m'))

    # print currentHour

    if currentHour >= 7 and currentHour <= 9:
        bld = str(0)    
        print bld
    elif currentHour >= 12 and currentHour <= 14:
        bld = str(1)
        print bld
    elif currentHour >= 19 and currentHour <= 21:
        bld = str(2)
        print bld
    else:
        return jsonify({'message': "Sorry !! You are at the wrong time in the Mess !!", 'error': 1})


    cursor.execute("SELECT * FROM mess_transaction WHERE DATE_FORMAT(mess_transaction_timestamp, '%Y-%m-%d') = '"+currentDate+"' AND mess_transaction_user_id = '"+id+"' AND mess_transaction_BLD = '"+bld+"'")
    result = cursor.fetchone()


    if result is None:
        cursor.execute("INSERT INTO mess_transaction(mess_transaction_user_id,mess_transaction_BLD) VALUES('"+id+"','"+bld+"')")
        cursor.execute("SELECT * FROM month_aggregation WHERE month_aggregation_user_id = '"+id+"' AND month_aggregation_month='"+currentMonth+"' ")
        row = cursor.fetchone()

        if row is None:
            if bld == '0':
                cursor.execute("INSERT INTO month_aggregation(month_aggregation_user_id,month_aggregation_month,month_aggregation_breakfast) VALUES('"+id+"','"+currentMonth+"',1)")
            elif bld == '1':
                cursor.execute("INSERT INTO month_aggregation(month_aggregation_user_id,month_aggregation_month,month_aggregation_lunch) VALUES('"+id+"','"+currentMonth+"',1)")
            elif bld == '2':
                cursor.execute("INSERT INTO month_aggregation(month_aggregation_user_id,month_aggregation_month,month_aggregation_dinner) VALUES('"+id+"','"+currentMonth+"',1)")            
        else:
            if bld == '0':
                breakfast = str(row[3]+1)
                cursor.execute("UPDATE month_aggregation SET month_aggregation_breakfast = "+breakfast+" WHERE month_aggregation_user_id = '"+id+"' AND month_aggregation_month='"+currentMonth+"' ")
            elif bld == '1':
                lunch = str(row[4]+1)
                cursor.execute("UPDATE month_aggregation SET month_aggregation_lunch = "+lunch+" WHERE month_aggregation_user_id = '"+id+"' AND month_aggregation_month='"+currentMonth+"' ")
            elif bld == '2':
                dinner = str(row[5]+1)
                cursor.execute("UPDATE month_aggregation SET month_aggregation_dinner = "+dinner+" WHERE month_aggregation_user_id = '"+id+"' AND month_aggregation_month='"+currentMonth+"' ")

    else:
        return jsonify({'message': "Not the first time! Have Fun!", 'error': 1})


    cursor.execute("SELECT food_cost_breakfast, food_cost_lunch, food_cost_dinner FROM food_cost WHERE food_cost_pk = (SELECT MAX(food_cost_pk) FROM (SELECT food_cost_pk FROM food_cost a WHERE '"+currentMonth+"' >= (SELECT food_cost_effective_from FROM food_cost b WHERE a.food_cost_pk = b.food_cost_pk)) t)")
    cost = cursor.fetchone()
    breakfast_cost = int(cost[0])
    lunch_cost = int(cost[1])
    dinner_cost = int(cost[2])

    cursor.execute("SELECT month_aggregation_breakfast,month_aggregation_lunch,month_aggregation_dinner FROM month_aggregation WHERE month_aggregation_user_id = '"+id+"' AND month_aggregation_month='"+currentMonth+"' ")
    number_of_bld = cursor.fetchone()

    dues = int(breakfast_cost*number_of_bld[0])+(lunch_cost*number_of_bld[1])+(dinner_cost*number_of_bld[2])

    cursor.execute("SELECT * FROM monthly_dues WHERE monthly_dues_month = '"+currentMonth+"' AND monthly_dues_user_id = '"+id+"' ")
    result = cursor.fetchone()   

    if result is None:
        query = "INSERT INTO monthly_dues(monthly_dues_user_id,monthly_dues_month,monthly_dues_amount) VALUES(%s,%s,%s)"
        param = (id,currentMonth,dues)
        cursor.execute(query,param)
    else:
        cursor.execute("SELECT monthly_dues_pk FROM monthly_dues WHERE monthly_dues_month = '"+currentMonth+"' AND monthly_dues_user_id = '"+id+"'")
        result = cursor.fetchone()
        monthly_dues_pk = int(result[0])
        query = "UPDATE monthly_dues SET monthly_dues_amount = %s WHERE monthly_dues_pk = %s"
        param = (dues,monthly_dues_pk)
        cursor.execute(query,param)

    conn.commit()
    conn.close()

    resp = {
        'message': "Thank you !",
        'error': 0,
        'result': {
            'user_name': get_name(id),
            'bld': bld
        }
        
    }

    return jsonify(resp)
#---------------------------------scanBLD API ends here----------------------------------------


#---------------------------------bulkBLD API------------------------------------------------
@app.route('/bulkBLD')
@cross_origin()
def buy_bulk_bld():
    
    id = request.args.get('id')
    # bld = request.args.get('bld') #bld 0-breakfast 1-lunch 2-dinner

    plates = request.args.get('plates')

    if not id:
        return jsonify({'message': "Please provide id", 'error': 1})

    conn = mysql.connect()
    cursor = conn.cursor()

    currentTimestamp = datetime.now()    
    currentDate = currentTimestamp.strftime('%Y-%m-%d')
    currentTime = currentTimestamp.strftime('%H:%M:%S')
    currentMonth = currentTimestamp.strftime('%Y-%m')
    currentHour = int(currentTimestamp.strftime('%H'))

    # nextmonth = currentTimestamp+relativedelta(months=+1)
    
    # print(currentMonth)
    # print(nextmonth.strftime('%Y-%m'))

    # print currentHour

    if currentHour >= 7 and currentHour <= 9:
        bld = str(0)    
        print bld
    elif currentHour >= 12 and currentHour <= 14:
        bld = str(1)
        print bld
    elif currentHour >= 19 and currentHour <= 21:
        bld = str(2)
        print bld
    else:
        return jsonify({'message': "Sorry !! You are at the wrong time in the Mess !!", 'error': 1})


    
    cursor.execute("INSERT INTO mess_transaction(mess_transaction_user_id,mess_transaction_BLD) VALUES('"+id+"','"+bld+"')")
    cursor.execute("SELECT * FROM month_aggregation WHERE month_aggregation_user_id = '"+id+"' AND month_aggregation_month='"+currentMonth+"' ")
    row = cursor.fetchone()

    if row is None:
        if bld == '0':
            cursor.execute("INSERT INTO month_aggregation(month_aggregation_user_id,month_aggregation_month,month_aggregation_breakfast) VALUES('"+id+"','"+currentMonth+"','"+plates+"')")
        elif bld == '1':
            cursor.execute("INSERT INTO month_aggregation(month_aggregation_user_id,month_aggregation_month,month_aggregation_lunch) VALUES('"+id+"','"+currentMonth+"','"+plates+"')")
        elif bld == '2':
            cursor.execute("INSERT INTO month_aggregation(month_aggregation_user_id,month_aggregation_month,month_aggregation_dinner) VALUES('"+id+"','"+currentMonth+"','"+plates+"')")            
    else:
        if bld == '0':
            breakfast = str(row[3]+plates)
            cursor.execute("UPDATE month_aggregation SET month_aggregation_breakfast = "+breakfast+" WHERE month_aggregation_user_id = '"+id+"' AND month_aggregation_month='"+currentMonth+"' ")
        elif bld == '1':
            lunch = str(row[4]+plates)
            cursor.execute("UPDATE month_aggregation SET month_aggregation_lunch = "+lunch+" WHERE month_aggregation_user_id = '"+id+"' AND month_aggregation_month='"+currentMonth+"' ")
        elif bld == '2':
            dinner = str(row[5]+plates)
            cursor.execute("UPDATE month_aggregation SET month_aggregation_dinner = "+dinner+" WHERE month_aggregation_user_id = '"+id+"' AND month_aggregation_month='"+currentMonth+"' ")


    cursor.execute("SELECT food_cost_breakfast, food_cost_lunch, food_cost_dinner FROM food_cost WHERE food_cost_pk = (SELECT MAX(food_cost_pk) FROM (SELECT food_cost_pk FROM food_cost a WHERE '"+currentMonth+"' >= (SELECT food_cost_effective_from FROM food_cost b WHERE a.food_cost_pk = b.food_cost_pk)) t)")
    cost = cursor.fetchone()
    breakfast_cost = int(cost[0])
    lunch_cost = int(cost[1])
    dinner_cost = int(cost[2])

    cursor.execute("SELECT month_aggregation_breakfast,month_aggregation_lunch,month_aggregation_dinner FROM month_aggregation WHERE month_aggregation_user_id = '"+id+"' AND month_aggregation_month='"+currentMonth+"' ")
    number_of_bld = cursor.fetchone()

    dues = int(breakfast_cost*number_of_bld[0])+(lunch_cost*number_of_bld[1])+(dinner_cost*number_of_bld[2])

    cursor.execute("SELECT * FROM monthly_dues WHERE monthly_dues_month = '"+currentMonth+"' AND monthly_dues_user_id = '"+id+"' ")
    result = cursor.fetchone()   

    if result is None:
        query = "INSERT INTO monthly_dues(monthly_dues_user_id,monthly_dues_month,monthly_dues_amount) VALUES(%s,%s,%s)"
        param = (id,currentMonth,dues)
        cursor.execute(query,param)
    else:
        cursor.execute("SELECT monthly_dues_pk FROM monthly_dues WHERE monthly_dues_month = '"+currentMonth+"' AND monthly_dues_user_id = '"+id+"'")
        result = cursor.fetchone()
        monthly_dues_pk = int(result[0])
        query = "UPDATE monthly_dues SET monthly_dues_amount = %s WHERE monthly_dues_pk = %s"
        param = (dues,monthly_dues_pk)
        cursor.execute(query,param)

    conn.commit()
    conn.close()

    resp = {
        'message': "Thank you !",
        'error': 0,
        'result': {
            'bld': bld
        }
        
    }

    return jsonify(resp)
#---------------------------------bulkBLD API ends here----------------------------------------









@app.route('/getDues')
@cross_origin()
def get_dues():
    
    id = request.args.get('id')
    if not id:
        return jsonify({'message': "Please provide id", 'error': 1})

    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT month_aggregation_month,month_aggregation_breakfast,month_aggregation_lunch,month_aggregation_dinner,monthly_dues_amount FROM month_aggregation JOIN monthly_dues ON month_aggregation_user_id = monthly_dues_user_id AND month_aggregation_month = monthly_dues_month WHERE monthly_dues_user_id = '"+id+"' AND monthly_dues_amount >= 0 ORDER BY month_aggregation_month DESC")
    result = cursor.fetchall()
    # print result

    resp = {
        'message': "Thank you !",
        'error': 0,
        'result': {
            'user_name': get_name(id),
            'dueslist': result
        }        
    }
    return jsonify(resp)   


@app.route('/payDues')
@cross_origin()
def pay_dues():
    
    id = request.args.get('id')
    if not id:
        return jsonify({'message': "Please provide id", 'error': 1})

    month = request.args.get('month')
    if not month:
        return jsonify({'message': "Please provide id", 'error': 1})

    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT monthly_dues_pk FROM monthly_dues WHERE monthly_dues_month = '"+month+"' AND monthly_dues_user_id = '"+id+"'")
    result = cursor.fetchone()
    monthly_dues_pk = int(result[0])
    query = "UPDATE monthly_dues SET monthly_dues_amount = 0 WHERE monthly_dues_pk = %s"
    param = (monthly_dues_pk)
    cursor.execute(query,param)

    conn.commit()
    conn.close()

    resp = {
        'message': "Thank you !",
        'error': 0  
    }
    return jsonify(resp) 

@app.route('/changeFoodCost')
@cross_origin()
def change_FoodCost():
    
    breakfast = request.args.get('b')
    if not breakfast:
        return jsonify({'message': "Please provide breakfast cost", 'error': 1})

    lunch = request.args.get('l')
    if not lunch:
        return jsonify({'message': "Please provide lunch cost", 'error': 1})

    dinner = request.args.get('d')
    if not dinner:
        return jsonify({'message': "Please provide dinner cost", 'error': 1})

    conn = mysql.connect()
    cursor = conn.cursor()

    currentTimestamp = datetime.now()    
    currentMonth = currentTimestamp.strftime('%Y-%m')
    nextmonth = currentTimestamp+relativedelta(months=+1)
    nextmonth = nextmonth.strftime('%Y-%m')

    cursor.execute("SELECT food_cost_pk FROM food_cost WHERE food_cost_effective_from = '"+nextmonth+"'")
    result = cursor.fetchone()  
    


    if result is None:    
        cursor.execute("INSERT INTO food_cost(food_cost_breakfast,food_cost_lunch,food_cost_dinner,food_cost_effective_from) VALUES("+breakfast+","+lunch+","+dinner+",'"+nextmonth+"')")
    else:
        food_cost_pk = int(result[0])
        query = "DELETE FROM food_cost WHERE food_cost_pk= %s"
        param = (food_cost_pk)
        cursor.execute(query,param)
        cursor.execute("INSERT INTO food_cost(food_cost_breakfast,food_cost_lunch,food_cost_dinner,food_cost_effective_from) VALUES("+breakfast+","+lunch+","+dinner+",'"+nextmonth+"')")
    
    
    conn.commit()
    conn.close()

    resp = {
        'message': "Thank you !",
        'error': 0,
        'result': {
            'Effective From': nextmonth
        }
    }
    return jsonify(resp)   


@app.route('/mailFullDueReport')
@cross_origin()
def mailFullDueReport():
  
  id = request.args.get('id')
  if not id:
    return jsonify({'message': "Please provide id", 'error': 1})

  emailBody = request.args.get('emailBody')

  email = get_email_id(id)
  print email

  
  
  msg = Message('Dues Summary', sender = 'iiitbangalore7@gmail.com', recipients = [email])
  msg.html = '<table style="width:100%">'+emailBody+'</table>'
  mail.send(msg)
  return 'Mail sent'

def get_name(id):
    conn = mysql.connect()
    cursor =conn.cursor()
    cursor.execute("SELECT FullName from student where RollNo=%s", (id,))
    row = cursor.fetchone()

    if row is None:
        cursor.execute("SELECT FullName from employee where EmpID=%s", (id,))
        row = cursor.fetchone()

    conn.close()
    return row[0] if row else ""

def get_email_id(id):
    conn = mysql.connect()
    cursor =conn.cursor()
    cursor.execute("SELECT IIITBEmailID from student where RollNo=%s", (id,))
    row = cursor.fetchone()
    
    if row is None:
        cursor.execute("SELECT IIITBEmailID from employee where EmpID=%s", (id,))
        row = cursor.fetchone()
    
    conn.close()
    return row[0] if row else ""