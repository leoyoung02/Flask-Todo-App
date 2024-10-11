from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from .models import Todo
from . import db
import json

views = Blueprint('views', __name__)

def check_due_dates(due_date):
    if due_date:
        due_date_obj = due_date
        if due_date_obj < datetime.now():
            return 'expired'  # Task is expired
        elif due_date_obj <= datetime.now() + timedelta(days=7):
            return 'due_soon'  # Task is due within the next 7 days
    return 'upcoming'  # Task is upcoming


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': 
        title = request.form.get('title')#Gets the todo from the HTML 
        due_date = request.form['due_date']

        if len(title) < 1:
            flash('Title is too short!', category='error') 
        else:
            new_todo = Todo(title=title, user_id=current_user.id)  #providing the schema for the todo 

            if due_date:
                try:
                    # Attempt to parse the due_date
                    due_date = datetime.strptime(due_date, '%Y-%m-%d')
                except ValueError:
                    # If parsing fails, set due_date to now
                    due_date = None
                    flash('Invalid date format.', category='warning')
            else:
                # If no due_date is provided, set it to now
                due_date = None

            new_todo.due_date = due_date
            db.session.add(new_todo) #adding the todo to the database 
            db.session.commit()
            flash('Todo added!', category='success')
        return redirect(url_for('views.home'))


    todos = current_user.todos  # Accessing the user's todos
    # Filter logic
    filter_type = request.args.get('filter', 'all')  # Default to 'all'
    if filter_type == 'active':
        todos = [todo for todo in todos if not todo.is_completed]
    elif filter_type == 'completed':
        todos = [todo for todo in todos if todo.is_completed]

    # Sort logic
    sort_type = request.args.get('sort', 'date')  # Default sort by date
    order_type = request.args.get('order', 'asc')  # Default order is ascending

    if sort_type == 'date':
        todos = sorted(todos, key=lambda x: (x.due_date is None, x.due_date), reverse=(order_type == 'desc'))
    elif sort_type == 'completeness':
        todos = sorted(todos, key=lambda x: x.is_completed, reverse=(order_type == 'desc'))

    # Get Information
    expired_count = sum(1 for todo in todos if check_due_dates(todo.due_date) == 'expired')
    due_soon_count = sum(1 for todo in todos if check_due_dates(todo.due_date) == 'due_soon')
    completed_count = sum(1 for todo in todos if todo.is_completed)
    items_left = len(todos) - completed_count

    return render_template("home.html", user=current_user, todos=todos, check_due_dates=check_due_dates,
        expired_count=expired_count, due_soon_count=due_soon_count, items_left=items_left, filter_type=filter_type,
        sort_type=sort_type, order_type=order_type)


@views.route('/delete-todo', methods=['POST'])
def delete_todo():  
    todo = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
    todoId = todo['todoId']
    todo = Todo.query.get(todoId)
    if todo:
        if todo.user_id == current_user.id:
            db.session.delete(todo)
            db.session.commit()

    return jsonify({})

@views.route('/complete/<int:id>', methods=['POST'])
def complete(id):
    todo = Todo.query.get_or_404(id)
    todo.is_completed = not todo.is_completed  # Toggle completion status
    db.session.commit()



    # Redirect while preserving filter and sort parameters
    filter_type = request.args.get('filter', 'all')
    sort_type = request.args.get('sort', 'date')
    order_type = request.args.get('order', 'asc')

    return redirect(url_for('views.home', filter=filter_type, sort=sort_type, order=order_type))

@views.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    todo = Todo.query.get_or_404(id)
    if request.method == 'POST':
        todo.title = request.form['title']
        due_date = request.form['due_date']

        if due_date:
            try:
                # Attempt to parse the due_date
                due_date = datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                # If parsing fails, set due_date to now
                due_date = None
                flash('Invalid date format.', category='warning')
        else:
            # If no due_date is provided, set it to now
            due_date = None

        todo.due_date = due_date
        db.session.commit()
        return redirect('/')
    return render_template('edit.html', todo=todo, user=current_user)