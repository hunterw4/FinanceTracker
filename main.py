from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import datetime

app = Flask(__name__)

Bootstrap5(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///bills.db"

app.config['SQLALCHEMY_BINDS'] = {
    'income': 'sqlite:///income.db',
    'savings': 'sqlite:///savings.db',
    'remaining_funds': 'sqlite:///remaining_funds.db'
}

db = SQLAlchemy(app)

today = datetime.datetime.now().strftime('%Y-%m-%d')
class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_name = db.Column(db.String(250), unique=True)
    bill_cost = db.Column(db.Integer, nullable=False)
    pay_status = db.Column(db.Integer, nullable=False)
    original_cost = db.Column(db.Integer, nullable=False)



class Income(db.Model):
    __bind_key__ = 'income'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Integer, unique=True)
    check = db.Column(db.Integer, nullable=False)

class RemainingFunds(db.Model):
    __bind_key__ = 'remaining_funds'
    id = db.Column(db.Integer, primary_key=True)
    funds = db.Column(db.Integer, nullable=False)


class Saving(db.Model):
    __bind_key__ = 'savings'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Integer, unique=True)
    savings = db.Column(db.String(250), nullable=False)
    total_savings = db.Column(db.String(250), nullable=False)


with app.app_context():
    latest_income = db.session.query(Income).order_by(Income.id.desc()).first()
    last_income = (
        db.session.query(Income)
        .order_by(Income.id.desc())
        .offset(1)
        .limit(1)
        .first()  # Execute the query and fetch the result
    )

    previous_income_check = last_income.check
    # Converting STR to INT to do calculations in the difference() function
    previous_str = previous_income_check.replace(',', '')
    previous_int = int(previous_str)


    if latest_income:
        latest_check = latest_income.check
        # Converting STR to INT to do calculations in the difference() function
        latest_str = latest_check.replace(',', '')
        latest_check_int = int(latest_str)


with app.app_context():
    latest_funds = db.session.query(RemainingFunds).order_by(RemainingFunds.id.desc()).first()
    previous_fund = (
        db.session.query(RemainingFunds)
        .order_by(RemainingFunds.id.desc())
        .offset(1)
        .limit(1)
        .first()  # Execute the query and fetch the result
    )

    previous_funds = previous_fund.funds

    if latest_funds:
        # Format the total_saved integer as a string with commas
        remaining_funds_str = '{:,}'.format(latest_funds.funds)

# Now, remaining_funds_str contains the integer formatted as a string with commas


with app.app_context():
    latest_savings = db.session.query(Saving).order_by(Saving.id.desc()).first()

    previous_saving = (
        db.session.query(Saving)
        .order_by(Saving.id.desc())
        .offset(1)
        .limit(1)
        .first()  # Execute the query and fetch the result
    )

    last_saving = previous_saving.savings
    if latest_savings:
        # Remove commas, convert to integers, and then format with commas
        savings_str = latest_savings.savings.replace(',', '')
        total_savings_str = latest_savings.total_savings.replace(',', '')

        total_saved = int(savings_str) + int(total_savings_str)

        # Format the total_saved integer back to a string with commas
        total_saved_str = '{:,}'.format(total_saved)
    # Converting STR to INT to do calculations in the difference() function
    previous_saving_str = last_saving.replace(',', '')
    previous_saving_int = int(previous_saving_str)


with app.app_context():
    db.create_all()


with app.app_context():
    most_recent_bill = Bill.query.order_by(Bill.id.desc()).first()

    if most_recent_bill:
        pay_status = most_recent_bill.pay_status
    else:
        # Handle the case where there are no records in the Bill table
        pay_status = None

# Ended up not using this method should delete
# 0 = New month nothing payed
# 1 = Half payed
# 2 = Fully payed

# text-success small pt-1 fw-bold (Increase HTML element)
# text-danger small pt-1 fw-bold (Decrease HTML element)

def difference(num1, num2, t_diff):
    if num1 > num2:
        icon = "text-success small pt-1 fw-bold"
        p_diff = int(abs(num1 - num2)/num2 * 100)
        t_diff = "Increase"
        return icon, p_diff, t_diff
    elif num1 < num2:
        icon = "text-danger small pt-1 fw-bold"
        p_diff = int(abs(num1 - num2) / num2 * 100)
        t_diff = "Decrease"
        return icon, p_diff, t_diff


# Gives remaining balance the same as the current check
balance = latest_check
remaining_balance = int(balance.replace(',', ''))

@app.route("/", methods=["GET", "POST"])
def home():
    icon, p_diff, t_diff = difference(latest_check_int, previous_int, t_diff="")
    funds_icon, funds_diff, t_diff_funds = difference(latest_funds.funds, previous_funds, t_diff="")
    savings_icon, savings_diff, t_diff_savings = difference(total_saved, previous_saving_int, t_diff="")
    chart_data = {
        'savings': [],
        'revenue': [],
        'remaining_funds': [],
        'date': []
    }
    saving_hist = db.session.query(Saving)
    revenue_hist = db.session.query(Income)
    remaining_funds_hist = db.session.query(RemainingFunds)
    for bal in saving_hist:
        savings_value = bal.total_savings.replace(',', '')
        chart_data['savings'].append(bal.total_savings)
        chart_data['date'].append(bal.date)
    for rev in revenue_hist:
        revenue_value = rev.check.replace(',', '')
        chart_data['revenue'].append(revenue_value)
    for funds in remaining_funds_hist:
        chart_data['remaining_funds'].append(funds.funds)
    print(chart_data)

    if request.method == 'POST':
        bills = Bill.query.all()

        for bill in bills:
            bill.bill_cost = bill.original_cost  # Reset bill_cost to original_cost

        db.session.commit()
        return redirect(url_for('home'))
    # Counting the amount of bills, to then display on the index.html for the home page
    bills = Bill.query.all()
    count = 0
    for bill in bills:
        count += 1
        total_bills = count
    return render_template("index.html", latest_income=latest_check, total_saved=total_saved_str,
                           total_bills=total_bills, remaining_balance=remaining_funds_str, icon=icon, p_diff=p_diff, t_diff=t_diff,
                           funds_icon=funds_icon,funds_diff=funds_diff, t_diff_funds=t_diff_funds, savings_icon=savings_icon,
                           savings_diff=savings_diff, t_diff_savings=t_diff_savings, chart_data=chart_data)


@app.route("/add", methods=["GET", "POST"])
def add():
    # Adding a new bill to the DB via the form in the add.html
    if request.method == 'POST':
        new_bill = Bill(
            bill_name=request.form["bill_name"],
            bill_cost=request.form["bill_cost"],
            pay_status=0,
            original_cost=request.form["bill_cost"]
        )
        db.session.add(new_bill)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("add.html")


@app.route("/income", methods=["GET", "POST"])
def income():
    # Adding a new paycheck to the income DB
    if request.method == 'POST':
        new_check = Income(
            date=today,
            check=request.form["check"]
        )
        db.session.add(new_check)
        db.session.commit()
        # Using the same data from the check form to then use for the funds DB
        string_removal = request.form["check"]
        funds = string_removal.replace(',', '')
        new_funds = RemainingFunds(
            funds=funds
        )
        db.session.add(new_funds)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("income.html")




@app.route("/pay", methods=["GET", "POST"])
def pay():
    # Using the form to get the specific bill to pay
    if request.method == "POST":
        bill_id = request.form["id"]
        bill_to_update = db.session.query(Bill).get(bill_id)

        if "biweekly" in request.form:
            # Update bill_cost for bi-weekly payment
            bill_to_update.bill_cost = bill_to_update.original_cost / 2
            db.session.commit()
            # Subtracting the bill in this case the bi-weekly payment from the remaining funds
            fund_update = db.session.query(RemainingFunds).order_by(RemainingFunds.id.desc()).first()
            int_update = int(fund_update.funds) - bill_to_update.original_cost / 2
            fund_update.funds = int_update
            db.session.commit()
        if "delete" in request.form:
            db.session.delete(bill_to_update)
            db.session.commit()
        elif "pay_in_full" in request.form:
            # Update bill_cost for payment in full
            bill_to_update.bill_cost = 0
            db.session.commit()
            # Subtracting the total bill from the remaining funds
            fund_update = db.session.query(RemainingFunds).order_by(RemainingFunds.id.desc()).first()
            int_update = int(fund_update.funds) - bill_to_update.original_cost
            fund_update.funds = int_update
            db.session.commit()
        return redirect(url_for('home'))
    # Getting all the bill names to then add to the pay.html file to then loop through all the names therefor creating seperate cards for each bill
    result = db.session.execute(db.select(Bill).order_by(Bill.bill_name))
    bill_names = result.scalars().all()
    return render_template("pay.html", bill_names=bill_names)




@app.route("/savings", methods=["GET", "POST"])
def savings():
    # Using basically the same exact form and html elements from the income section and reusing it for the savings DB / card
    if request.method == 'POST':
        added_savings = Saving(
            date=today,
            savings=request.form["savings"],
            total_savings=total_saved
        )
        db.session.add(added_savings)
        db.session.commit()
        # Subtracting the contributed savings from the overall remaining funds
        saving_form = request.form["savings"]
        string_removal = saving_form.replace(',', '')
        saving_int = int(string_removal)
        fund_update = db.session.query(RemainingFunds).order_by(RemainingFunds.id.desc()).first()
        int_update = int(fund_update.funds) - saving_int
        fund_update.funds = int_update
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("savings.html")

@app.route("/withdraw", methods=["GET","POST"])
def withdraw():
    if request.method == "POST":
        withdraw_form = request.form["withdraw"]
        string_removal = withdraw_form.replace(',', '')
        withdraw_int = int(string_removal)
        print(withdraw_int)
        current_savings = db.session.query(Saving).order_by(Saving.id.desc()).first()
        current_savings_int = current_savings.total_savings.replace(',', '')
        int_update = int(current_savings_int) - withdraw_int
        str_update = '{:,}'.format(int_update)
        negative_symbol_withdraw = '-' + withdraw_form

        withdraw_amount = Saving(
            date=today,
            savings=negative_symbol_withdraw,
            total_savings=str_update
        )
        db.session.add(withdraw_amount)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("withdraw.html")


if __name__ == "__main__":
    app.run(debug=True)
