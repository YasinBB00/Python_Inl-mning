from flask import Flask, render_template, request
import json
app = Flask(__name__)


with open("tasks.json", "r") as json_file:
    loaded_tasks = json.load(json_file)   

def require_password(f):
    def wrapper(*args, **kwargs):
        data = request.json
        if not data or data.get("password") != "123":
            return {"error": "Unauthorized access. Invalid password."}, 401
        return f(*args, **kwargs)
    
    return wrapper

@app.route("/tasks", methods=["GET"])
def get_tasks():
    status_parameter = request.args.get("completed") or request.args.get("Completed") or request.args.get("COMPLETED")
    if status_parameter:
        if status_parameter == "true":
            filter_tasks = [task for task in loaded_tasks if task["status"] == "complete"]
        elif status_parameter == "false":
            filter_tasks = [task for task in loaded_tasks if task["status"] == "pending"]
        else:
            return {"error": "Invalid value for completed. Use 'true' or 'false'."}, 400
        return filter_tasks, 200
    return loaded_tasks, 200

@app.route("/tasks", methods=["POST"])
def add_task():
    data = request.form
    description = data.get("description")
    category = data.get("category")

    new_id = max([task["id"] for task in loaded_tasks], default=0) + 1

    new_task = {"id": new_id, "description": description, "category": category, "status": "pending"}

    if not description and not category:
        return {"error": "description and category are required"}, 400
    
    if not description:
        return {"error": "description is required"}, 400
    
    if not category:
        return {"error": "category is required"}, 400

    loaded_tasks.append(new_task)
    with open("tasks.json", "w") as json_file:
        json.dump(loaded_tasks, json_file)

    return new_task, 201

@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    for task in loaded_tasks:
        if task["id"] == task_id:
            return task
    return {"error": "Task not found"}, 404

@app.route("/tasks/<int:task_id>", methods=["DELETE"])
@require_password
def delete_task(task_id):
    for i, task in enumerate(loaded_tasks):
        if task["id"] == task_id:
            description = task["description"]
            loaded_tasks.pop(i)
            with open("tasks.json", "w") as json_file:
                json.dump(loaded_tasks, json_file)
            return {"msg": f"The task with description, {description}! Has been deleted"}, 200
    return {"error": "Task not found"}, 404

@app.route("/tasks/<int:task_id>", methods=["PUT"])
def replace_task_id_by_id(task_id):
    data = request.json
    description = data.get("description")
    category = data.get("category")

    if description is None or category is None:
        return {"error": "Both description and category are required"}, 400

    for i, task in enumerate(loaded_tasks):
        if task["id"] == task_id:
            updated_task = {
                "id": task_id,
                "description": description,
                "category": category,
                "status": "pending"
            }
            loaded_tasks[i] = updated_task
            with open("tasks.json", "w") as json_file:
                json.dump(loaded_tasks, json_file)
            return updated_task, 201

    return {"error": "Task not found"}, 404 

@app.route("/tasks/<int:task_id>/complete", methods=["PUT"])
def complete_task(task_id):
    for i, task in enumerate(loaded_tasks):
        if task["id"] == task_id:
            updated_task = {
                "id": task_id,
                "description": task["description"],
                "category": task["category"],
                "status": "complete"
            }
            loaded_tasks[i] = updated_task
            with open("tasks.json", "w") as json_file:
                json.dump(loaded_tasks, json_file)
                return updated_task, 200

    return {"error": "Task not found"}, 404

@app.route("/tasks/categories", methods=["GET"]) 
def get_all_categories():
    categories = []
    for task in loaded_tasks:
        category = task.get("category")
        if category not in categories:
            categories.append(category)    
    return categories, 200
        
@app.route("/tasks/categories/<category_name>", methods=["GET"]) 
def get_task_in_category(category_name):
    tasks_in_category = []
    for task in loaded_tasks:
        if task["category"].capitalize() == category_name.capitalize():
            tasks_in_category.append(task)
    if tasks_in_category:
        return tasks_in_category, 200
    return {"error": "category not found"}, 404

@app.route("/")
def index():  
    return render_template("index.html", title="Tasks", tasks=loaded_tasks), 200


        



      

