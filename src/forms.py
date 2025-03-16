from flask_wtf import FlaskForm
from wtforms import FloatField, SelectField, StringField, SubmitField, DateField
from wtforms.validators import DataRequired, NumberRange

class ExpenseForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField('Category', validators=[DataRequired()], choices=[
        ('Food', 'Food'),
        ('Transportation', 'Transportation'),
        ('Housing', 'Housing'),
        ('Utilities', 'Utilities'),
        ('Entertainment', 'Entertainment'),
        ('Shopping', 'Shopping'),
        ('Healthcare', 'Healthcare'),
        ('Other', 'Other')
    ])
    payment_mode = SelectField('Payment Mode', validators=[DataRequired()], choices=[
        ('Cash', 'Cash'),
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('UPI', 'UPI'),
        ('Net Banking', 'Net Banking'),
        ('Wallet', 'Wallet'),
        ('Other', 'Other')
    ])
    description = StringField('Description')
    submit = SubmitField('Add Expense')

class IncomeForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    source = SelectField('Source', validators=[DataRequired()], choices=[
        ('Salary', 'Salary'),
        ('Freelance', 'Freelance'),
        ('Investments', 'Investments'),
        ('Rent', 'Rent'),
        ('Other', 'Other')
    ])
    submit = SubmitField('Add Income')

class CreditForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    description = StringField('Description', validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[DataRequired()])
    submit = SubmitField('Add Credit') 