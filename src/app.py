from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.express as px
import plotly.graph_objects as go
import json
from forms import ExpenseForm, IncomeForm
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    expenses = db.relationship('Expense', backref='user', lazy=True)
    incomes = db.relationship('Income', backref='user', lazy=True)
    credits = db.relationship('Credit', backref='user', lazy=True)
    investments = db.relationship('Investment', backref='user', lazy=True)
    budgets = db.relationship('Budget', backref='user', lazy=True)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1-12 for each month
    year = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    @property
    def spent_amount(self):
        start_date = datetime(self.year, self.month, 1)
        if self.month == 12:
            end_date = datetime(self.year + 1, 1, 1)
        else:
            end_date = datetime(self.year, self.month + 1, 1)
        
        expenses = Expense.query.filter(
            Expense.user_id == self.user_id,
            Expense.category == self.category,
            Expense.date >= start_date,
            Expense.date < end_date
        ).all()
        
        return sum(expense.amount for expense in expenses)

    @property
    def remaining_amount(self):
        return self.amount - self.spent_amount

    @property
    def percentage_used(self):
        if self.amount == 0:
            return 100
        return (self.spent_amount / self.amount) * 100

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    payment_mode = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Credit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    paid = db.Column(db.Boolean, default=False)
    credit_limit = db.Column(db.Float, nullable=True)  # New field for credit limit
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    @property
    def credit_utilization(self):
        """Calculate credit utilization percentage"""
        if not self.credit_limit or self.credit_limit == 0:
            return 0
        return (self.amount / self.credit_limit) * 100

class Investment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    returns = db.Column(db.Float, nullable=False)
    current_value = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    expense_form = ExpenseForm()
    income_form = IncomeForm()
    
    if request.method == 'POST':
        # Calculate current totals
        total_income = sum(income.amount for income in current_user.incomes)
        total_expenses = sum(expense.amount for expense in current_user.expenses)
        total_investments = sum(investment.amount for investment in current_user.investments)
        total_credits = sum(credit.amount for credit in current_user.credits if not credit.paid)
        total_committed = total_expenses + total_investments + total_credits

        if expense_form.validate_on_submit():
            new_expense_amount = expense_form.amount.data
            category = expense_form.category.data
            
            # Check if this expense would exceed the budget for this category
            current_date = datetime.now()
            budget = Budget.query.filter_by(
                user_id=current_user.id,
                category=category,
                month=current_date.month,
                year=current_date.year
            ).first()
            
            if budget:
                if budget.spent_amount + new_expense_amount > budget.amount:
                    flash(f'Warning: This expense would exceed your budget for {category}! Budget: ₹{budget.amount:.2f}, Already spent: ₹{budget.spent_amount:.2f}', 'warning')
            
            # Check if total would exceed income
            if total_committed + new_expense_amount > total_income:
                flash('Cannot add expense! Total expenses, investments, and credits would exceed total income. Available balance: ₹{:.2f}'.format(total_income - total_committed), 'danger')
                return redirect(url_for('dashboard'))

            expense = Expense(
                amount=new_expense_amount,
                category=category,
                description=expense_form.description.data,
                payment_mode=expense_form.payment_mode.data,
                user_id=current_user.id
            )
            db.session.add(expense)
            db.session.commit()
            flash('Expense added successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        if income_form.validate_on_submit():
            income = Income(
                amount=income_form.amount.data,
                source=income_form.source.data,
                user_id=current_user.id
            )
            db.session.add(income)
            db.session.commit()
            flash('Income added successfully!', 'success')
            return redirect(url_for('dashboard'))

    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(5).all()
    incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).limit(5).all()
    credits = Credit.query.filter_by(user_id=current_user.id, paid=False).order_by(Credit.due_date).all()
    investments = Investment.query.filter_by(user_id=current_user.id).order_by(Investment.date.desc()).all()

    # Calculate totals
    total_expenses = sum(expense.amount for expense in current_user.expenses)
    total_income = sum(income.amount for income in current_user.incomes)
    total_credits = sum(credit.amount for credit in current_user.credits if not credit.paid)
    total_investments = sum(investment.amount for investment in current_user.investments)
    total_committed = total_expenses + total_investments + total_credits
    balance = total_income - total_committed

    # Check for credits near limit
    for credit in credits:
        if credit.credit_limit and credit.credit_utilization >= 50:
            flash('Warning: Credit "{}" is at {:.1f}% utilization!'.format(
                credit.description, credit.credit_utilization), 'warning')

    return render_template('dashboard.html',
                         expense_form=expense_form,
                         income_form=income_form,
                         expenses=expenses,
                         incomes=incomes,
                         credits=credits,
                         investments=investments,
                         total_expenses=total_expenses,
                         total_income=total_income,
                         total_credits=total_credits,
                         total_investments=total_investments,
                         balance=balance)

@app.route('/add_credit', methods=['POST'])
@login_required
def add_credit():
    amount = float(request.form['amount'])
    credit_limit = float(request.form.get('credit_limit', 0))  # Get credit limit from form
    
    # Check credit limit if provided
    if credit_limit > 0 and amount > credit_limit:
        flash('Cannot add credit! Amount (₹{:.2f}) exceeds credit limit (₹{:.2f})'.format(amount, credit_limit), 'danger')
        return redirect(url_for('dashboard'))

    description = request.form['description']
    due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
    
    credit = Credit(
        amount=amount,
        description=description,
        due_date=due_date,
        credit_limit=credit_limit,
        user_id=current_user.id
    )

    # Check if credit utilization would exceed 80%
    if credit.credit_utilization >= 80:
        flash('Warning: High credit utilization! This credit will utilize {:.1f}% of your credit limit.'.format(credit.credit_utilization), 'warning')
    elif credit.credit_utilization >= 50:
        flash('Notice: This credit will utilize {:.1f}% of your credit limit.'.format(credit.credit_utilization), 'info')

    db.session.add(credit)
    db.session.commit()
    flash('Credit added successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/add_investment', methods=['POST'])
@login_required
def add_investment():
    # Calculate current totals
    total_income = sum(income.amount for income in current_user.incomes)
    total_expenses = sum(expense.amount for expense in current_user.expenses)
    total_investments = sum(investment.amount for investment in current_user.investments)
    total_credits = sum(credit.amount for credit in current_user.credits if not credit.paid)
    total_committed = total_expenses + total_investments + total_credits

    amount = float(request.form['amount'])
    
    # Check if adding this investment would exceed income
    if total_committed + amount > total_income:
        flash('Cannot add investment! Total expenses, investments, and credits would exceed total income. Available balance: ₹{:.2f}'.format(total_income - total_committed), 'danger')
        return redirect(url_for('dashboard'))

    investment_type = request.form['type']
    description = request.form['description']
    returns = float(request.form['returns'])
    
    # Calculate current value based on returns percentage
    current_value = amount * (1 + returns/100)
    
    investment = Investment(
        amount=amount,
        type=investment_type,
        description=description,
        returns=returns,
        current_value=current_value,
        user_id=current_user.id
    )
    db.session.add(investment)
    db.session.commit()
    flash('Investment added successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/mark_credit_paid/<int:credit_id>')
@login_required
def mark_credit_paid(credit_id):
    credit = Credit.query.get_or_404(credit_id)
    if credit.user_id != current_user.id:
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('dashboard'))
    
    credit.paid = True
    db.session.commit()
    flash('Credit marked as paid!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/analytics')
@login_required
def analytics():
    # Get all financial data for the current user
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    incomes = Income.query.filter_by(user_id=current_user.id).all()
    credits = Credit.query.filter_by(user_id=current_user.id, paid=False).all()
    budgets = Budget.query.filter_by(user_id=current_user.id).all()

    # Prepare budget data with additional calculations
    budget_data = [{
        'category': budget.category,
        'amount': budget.amount,
        'spent_amount': budget.spent_amount,
        'remaining_amount': budget.remaining_amount,
        'percentage_used': budget.percentage_used
    } for budget in budgets]

    # Convert date objects to string format for JSON serialization
    expenses_data = [{
        'amount': expense.amount,
        'category': expense.category,
        'date': expense.date.strftime('%Y-%m-%d')
    } for expense in expenses]

    incomes_data = [{
        'amount': income.amount,
        'source': income.source,
        'date': income.date.strftime('%Y-%m-%d')
    } for income in incomes]

    credits_data = [{
        'amount': credit.amount,
        'description': credit.description,
        'due_date': credit.due_date.strftime('%Y-%m-%d'),
        'credit_limit': credit.credit_limit or 0
    } for credit in credits]

    return render_template('analytics.html',
                         expenses=expenses_data,
                         incomes=incomes_data,
                         credits=credits_data,
                         budgets=budgets,
                         budget_data=budget_data)

@app.route('/budget', methods=['GET', 'POST'])
@login_required
def budget():
    if request.method == 'POST':
        if 'budget_id' in request.form:
            # Handle budget edit
            budget_id = int(request.form['budget_id'])
            amount = float(request.form['amount'])
            
            budget = Budget.query.get_or_404(budget_id)
            if budget.user_id != current_user.id:
                flash('Unauthorized action!', 'danger')
                return redirect(url_for('budget'))
            
            budget.amount = amount
            db.session.commit()
            flash('Budget updated successfully!', 'success')
        else:
            # Handle new budget
            category = request.form['category']
            amount = float(request.form['amount'])
            month = int(request.form['month'])
            year = int(request.form['year'])
            
            # Check if budget already exists for this category and month/year
            existing_budget = Budget.query.filter_by(
                user_id=current_user.id,
                category=category,
                month=month,
                year=year
            ).first()
            
            if existing_budget:
                existing_budget.amount = amount
                flash('Budget updated successfully!', 'success')
            else:
                budget = Budget(
                    category=category,
                    amount=amount,
                    month=month,
                    year=year,
                    user_id=current_user.id
                )
                db.session.add(budget)
                flash('Budget added successfully!', 'success')
            
            db.session.commit()
        
        return redirect(url_for('budget'))
    
    # Get all budgets for display, ordered by month and year
    budgets = Budget.query.filter_by(user_id=current_user.id).order_by(
        Budget.year.desc(),
        Budget.month.desc()
    ).all()
    
    # Get unique expense categories for the user
    categories = db.session.query(Expense.category).filter_by(user_id=current_user.id).distinct().all()
    categories = [category[0] for category in categories]
    
    # Calculate total budget and total spent
    total_budget = sum(budget.amount for budget in budgets)
    total_spent = sum(budget.spent_amount for budget in budgets)
    
    return render_template('budget.html',
                         budgets=budgets,
                         categories=categories,
                         current_month=datetime.now().month,
                         current_year=datetime.now().year,
                         total_budget=total_budget,
                         total_spent=total_spent,
                         min=min)

@app.route('/clear_all_budgets', methods=['POST'])
@login_required
def clear_all_budgets():
    # Delete all budgets for the current user
    Budget.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('All budget records have been cleared!', 'success')
    return redirect(url_for('budget'))

@app.route('/clear_category/<category>', methods=['POST'])
@login_required
def clear_category(category):
    # Delete all expenses in this category
    Expense.query.filter_by(user_id=current_user.id, category=category).delete()
    
    # Delete the budget for this category
    current_date = datetime.now()
    Budget.query.filter_by(
        user_id=current_user.id,
        category=category,
        month=current_date.month,
        year=current_date.year
    ).delete()
    
    db.session.commit()
    flash(f'All records for category {category} have been cleared!', 'success')
    return redirect(url_for('budget'))

@app.route('/clear_all_records', methods=['POST'])
@login_required
def clear_all_records():
    # Delete ALL financial records for the current user
    Expense.query.filter_by(user_id=current_user.id).delete()
    Income.query.filter_by(user_id=current_user.id).delete()
    Credit.query.filter_by(user_id=current_user.id).delete()
    Investment.query.filter_by(user_id=current_user.id).delete()
    Budget.query.filter_by(user_id=current_user.id).delete()
    
    db.session.commit()
    flash('All financial records have been completely cleared!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/clear_income_records', methods=['POST'])
@login_required
def clear_income_records():
    # Keep the 5 most recent records
    recent_incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).limit(5).all()
    recent_ids = [income.id for income in recent_incomes]
    
    # Delete all except recent records
    Income.query.filter_by(user_id=current_user.id).filter(Income.id.notin_(recent_ids)).delete()
    db.session.commit()
    flash('Income records have been cleared (except recent transactions)!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/clear_expense_records', methods=['POST'])
@login_required
def clear_expense_records():
    # Keep the 5 most recent records
    recent_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(5).all()
    recent_ids = [expense.id for expense in recent_expenses]
    
    # Delete all except recent records
    Expense.query.filter_by(user_id=current_user.id).filter(Expense.id.notin_(recent_ids)).delete()
    db.session.commit()
    flash('Expense records have been cleared (except recent transactions)!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/clear_credit_records', methods=['POST'])
@login_required
def clear_credit_records():
    # Keep the 5 most recent records
    recent_credits = Credit.query.filter_by(user_id=current_user.id, paid=False).order_by(Credit.due_date).limit(5).all()
    recent_ids = [credit.id for credit in recent_credits]
    
    # Delete all except recent records
    Credit.query.filter_by(user_id=current_user.id).filter(Credit.id.notin_(recent_ids)).delete()
    db.session.commit()
    flash('Credit records have been cleared (except recent transactions)!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/clear_investment_records', methods=['POST'])
@login_required
def clear_investment_records():
    # Keep the 5 most recent records
    recent_investments = Investment.query.filter_by(user_id=current_user.id).order_by(Investment.date.desc()).limit(5).all()
    recent_ids = [investment.id for investment in recent_investments]
    
    # Delete all except recent records
    Investment.query.filter_by(user_id=current_user.id).filter(Investment.id.notin_(recent_ids)).delete()
    db.session.commit()
    flash('Investment records have been cleared (except recent transactions)!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5002) 