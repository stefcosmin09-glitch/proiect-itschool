from flask import Flask, request, redirect

app = Flask(__name__)

to_do_list = ['Buy groceries', 'Clean the house', 'Pay bills']

@app.route('/')
def hello_world():
    tasks = ""
    for i, todo in enumerate(to_do_list):
        tasks += f'<li>{todo} <a href="/delete/{i}">X</a></li>'
    return f'''
        <h1>To do List</h1>
        <ul>{tasks}</ul>
        <form method="POST" action="/add">
            <input type="text" name="task" placeholder="New task">
            <button type="submit">Add Task</button>
        </form>
    '''

@app.route('/add', methods=['POST'])
def add_task():
    task = request.form.get('task')
    if task:
        to_do_list.append(task)
    return redirect('/')

@app.route('/delete/<int:index>')
def delete(index):
    to_do_list.pop(index)
    return redirect('/')

@app.route('/contact')
def contact():
    return '<h1>Contact Us</h1>'

@app.route('/about')
def about():
    return '<h1>About Us</h1>'

if __name__ == '__main__':
   app.run(debug=True, host='0.0.0.0', port=5000)
