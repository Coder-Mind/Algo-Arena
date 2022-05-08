from flask import Flask, render_template, request, session, logging, url_for, redirect, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re, time, os
from passlib.hash import sha256_crypt
from datetime import date
import requests
import json
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta, TH
import csv






app = Flask(__name__)

app.secret_key = '12345'
  
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'algoarena'
  
mysql = MySQL(app)

expiry_type = 0
today = pd.datetime.today()
expiry_dates = []

if expiry_type == 0:
    # Weekly expiry
    for i in range(1,9):
         expiry_dates.append((today + relativedelta(weekday=TH(i))).date())
else:
    # Monthly expiry
    for i in range(1,9):
        x = (today + relativedelta(weekday=TH(i))).date()
        y = (today + relativedelta(weekday=TH(i+1))).date()
        if x.month != y.month :
            if x.day > y.day :
                expiry_dates.append(x)

end_of_month = datetime.today() + relativedelta(day=31)
last_exp_of_the_month= end_of_month + relativedelta(weekday=TH(-1))

last_exp_of_the_nxt_month = expiry_dates[-1]
cur_exp = expiry_dates[0]
nxt_exp = expiry_dates[1]

cur_exp = cur_exp.strftime("%d-%b-%Y")
nxt_exp = nxt_exp.strftime("%d-%b-%Y")
last_exp_of_the_month= last_exp_of_the_month.strftime("%d-%b-%Y")
last_exp_of_the_nxt_month = last_exp_of_the_nxt_month.strftime("%d-%b-%Y")

n_url = 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'
bn_url = 'https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY'

#Variables
NAMES = ['NIFTY','BANKNIFTY']
EXPIRY_DATES = [cur_exp, nxt_exp, last_exp_of_the_month]
CART_DICT={}            # Dictionary of Cart
HEADINGS = ("Buy", "Sell","OI", "Change_in_OI",  "Volume",  "IV",  "ltp", "CHNG", "strikePrice", "CHNG", "ltp", "IV", "Volume", "Change_in_OI", "OI", "Buy", "Sell")   #Headings of table of index.html page
OPTION1=["Buy", "Sell"]  #Dropdown where user can select buy or sell cart.html
OPTION2=["Call", "Put"]  #Dropdown where user can select Call or Put on index.html
#NAME1 selected indices by user on inputForm
#EXP_DATE selected expiry date by user on inputForm

n_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'}
bn_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'}


def fetch_oi(name, new_url, headers, expiry_dt):
    print("********", name, "*********")
    page = requests.get(new_url, headers=headers)
    dajs = json.loads(page.text)
    ce_values = [data['CE'] for data in dajs['records']['data'] if "CE" in data and data['expiryDate'] == expiry_dt]
    pe_values = [data['PE'] for data in dajs['records']['data'] if "PE" in data and data['expiryDate'] == expiry_dt]

    ce_dt = pd.DataFrame(ce_values).sort_values(['strikePrice'])
    pe_dt = pd.DataFrame(pe_values).sort_values(['strikePrice'])



    ce_dt1 = ce_dt[['openInterest', 'changeinOpenInterest', 'totalTradedVolume', 'impliedVolatility', 'lastPrice', 'change','bidQty', 'bidprice', 'askPrice', 'askQty','strikePrice']]
    ce_dt2 = ce_dt1.rename(columns={'openInterest' : 'OI_call','changeinOpenInterest' : 'Change_in_OI_call','totalTradedVolume' : 'Volume_call','impliedVolatility' : 'IV_call', 'lastPrice' :'ltp_call', 'change' : 'CHNG_call','bidQty' : 'bidQty_call', 'bidprice' :'bidprice_call', 'askPrice' : 'askPrice_call', 'askQty' : 'askQty_call'},inplace=False)
    pe_dt1 = pe_dt[['strikePrice','bidQty', 'bidprice', 'askPrice', 'askQty', 'change', 'lastPrice', 'impliedVolatility', 'totalTradedVolume', 'changeinOpenInterest', 'openInterest']]
    pe_dt2 = pe_dt1.rename(columns={'openInterest' : 'OI_put','changeinOpenInterest' : 'Change_in_OI_put','totalTradedVolume' : 'Volume_put','impliedVolatility' : 'IV_put', 'lastPrice' :'ltp_put', 'change' : 'CHNG_put','bidQty' : 'bidQty_put', 'bidprice' :'bidprice_put', 'askPrice' : 'askPrice_put', 'askQty' : 'askQty_put'},inplace=False)
    cp_df = pd.merge(ce_dt2,pe_dt2)

    
    cp_df['ltp_put']=cp_df['ltp_put'].apply(lambda x:round(x,2))

    print(cp_df)
    return cp_df
    
    print("******************")



def getOptionChain(name,exp_date):
    global g_df
    if(name=="NIFTY"):
        global NAME1
        NAME1=name
        global EXP_DATE
        EXP_DATE=exp_date
        g_df = fetch_oi(NAME1, n_url, n_headers, EXP_DATE)
        print(g_df)
        g_df = g_df.round(decimals = 2)
        g_df = g_df.reset_index()
        g_df = g_df.rename(columns={'index': 'col_id'})
        g_df = g_df.to_dict('records')
        # print(g_df)
    elif(name=="BANKNIFTY"):
        NAME1=name
        EXP_DATE=exp_date
        g_df = fetch_oi(NAME1, bn_url, bn_headers, EXP_DATE)
        print(g_df)
        g_df = g_df.round(decimals = 2)
        g_df = g_df.reset_index()
        g_df = g_df.rename(columns={'index': 'col_id'})
        g_df = g_df.to_dict('records')
        # print(g_df)
    return g_df


@app.route("/")
def home():
    return render_template("home.html")

# register
@app.route("/register", methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        aadhar = request.form['aadhar']
        password = request.form['password']
        confirm = request.form['confirm']
        secure_password = sha256_crypt.hash(str(password))

        if password == confirm and 'username' in request.form and 'password' in request.form and 'email' in request.form and 'aadhar' in request.form and 'phone' in request.form and 'confirm' in request.form:
            # Check if account exists using MySQL
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            account = cursor.fetchone()
            # If account exists show error and validation checks
            if account:
                flash("Account already exists!","danger")
                return render_template('register.html')
            else:
                #if account is new
                cursor.execute('INSERT INTO users VALUES (%s, %s, %s, %s, %s)', (username, phone, aadhar, email, secure_password))
                mysql.connection.commit()
                flash("Registration Successfull. You can login now!","success")
                return redirect(url_for('login'))

        else:
            flash("Password doesn't match or the fields are empty. Try again!","danger")
            return render_template('register.html')

    return render_template("register.html")

#login
@app.route("/login",methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        secure_password = sha256_crypt.hash(str(password))

        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        # Fetch one record and return result
        account = cursor.fetchone()
        

        # If account exists in accounts table in our database
        if account:
            if sha256_crypt.verify(password,account['secure_password']):
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                #session['id'] = account['id']
                session['email'] = account['email']
                session['phone'] = account['phone']
                session['username'] = account['username']
                # Redirect to home page
                
                return redirect(url_for('inputform'))
            else:
                #Incorrect
                flash("Invalid Credentials!","danger")
                return render_template("login.html")

            
        else:
            # Account doesnt exist
            flash("No such user!","danger")
            return render_template("login.html")

        
    return render_template("login.html")


#@app.route("/index")
#def index():
    # Check if user is loggedin
 #   if 'loggedin' in session:
        # User is loggedin show them the home page
  #      return render_template('index.html', name=session['username'],)
    # User is not loggedin redirect to login page
   # return redirect(url_for('login'))

@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   flash("You are now logged out!","success")
   return redirect(url_for('login'))

@app.route("/inputform", methods=['GET','POST'])
def inputform():
    return render_template("inputForm.html",names=NAMES,expirydts=EXPIRY_DATES)

@app.route("/index",methods=['POST'])
def index():
    if request.method == 'POST':
        name = request.form["name1"]
        exp_date = request.form["expiryDate"]
        g_df = getOptionChain(name,exp_date)
        return render_template("index.html",names=NAMES,expirydts=EXPIRY_DATES, headings = HEADINGS, gn_df=g_df, option2 = OPTION2)

#*******************************This is code Part*******************************************************************

df = pd.read_csv('code.csv')
df.to_csv('code.csv', index=None)  

lst = []
dic = {}
csv_col = ["codename","code"]
# A decorator used to tell the application
# which URL is associated function
@app.route('/form', methods =["GET", "POST"])
def form():
       # getting input with name = fname in HTML form
    code_name = request.form.get("cname")
       # getting input with name = lname in HTML form 
    code_value = request.form.get("cvalue")
    dic = {"codename":code_name,"code":code_value}
    
    lst.append(dic)
    csv_file = "code.csv"
    try:
        with open(csv_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_col)
            writer.writeheader()
            for i in range(1,len(lst)):
                writer.writerow(lst[i])
    except IOError:
        print("I/O error")
    
    data = pd.read_csv('code.csv')
    return render_template("form.html", tables=[data.to_html()], titles=[''])


#*******************************************************************************************************************
#@app.route('/form')
#def form():
#    return render_template('form.html')


@app.route("/cart", methods=['POST'])
def cart():
    if request.method == 'POST':
        strikePrice1 = request.form["strikePrice"]
        ltp1 = request.form["ltp1"]
        option1 = request.form["option1"]
        option2 = request.form["option2"]
        CART_DICT[strikePrice1]=[ltp1,option2,option1,NAME1,EXP_DATE]
        return render_template("/cart.html",cart_dict=CART_DICT, option1=OPTION1)
     
if __name__ == '__main__':
    app.run(debug=True)