import pytest
from app import app, loaded_tasks
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def reset_loaded_tasks():
    with open("tasks.json", "r") as json_file:
        initial_tasks = json.load(json_file)
    loaded_tasks.clear()
    loaded_tasks.extend(initial_tasks)

def test_index_route(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert "<h1>Tasks</h1>" in html
    for task in loaded_tasks:
        for key, value in task.items():
            key_cap = key.capitalize()
            value_cap = value.capitalize() if isinstance(value, str) else value
            
            assert f'<span class="key">{key_cap}: </span>' in html
            assert f'<span class="value">{value_cap}</span>' in html
    assert '<input type="text" name="category" placeholder="Category">' in html
    assert '<input type="text" name="description" placeholder="Description">' in html
    assert '<button type="submit">Submit</button>' in html

def test_get_all_tasks(client):
    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json 
    assert isinstance(tasks, list)

def test_get_completed_tasks(client):
    response = client.get("/tasks?completed=true")
    assert response.status_code == 200
    tasks = response.json
    assert all(task["status"] == "complete" for task in tasks)

def test_get_pending_tasks(client):
    response = client.get("/tasks?completed=false")
    assert response.status_code == 200
    tasks = response.json
    assert all(task["status"] == "pending" for task in tasks)

def test_get_tasks_invalid_parameter(client):
    response = client.get("/tasks?completed=invalid_value")
    assert response.status_code == 400
    error_message = response.json
    assert error_message == {"error": "Invalid value for completed. Use 'true' or 'false'."}

def test_add_task(client):
    new_task = {
        "description": "Complete assignment",
        "category": "work"
    }    
    response = client.post("/tasks", data=new_task)    
    assert response.status_code == 201 
    created_task = response.json
    assert created_task["description"] == "Complete assignment"
    assert created_task["category"] == "work"
    assert created_task["status"] == "pending"
    assert "id" in created_task 

def test_add_task_missing_both_fields(client):
    response = client.post("/tasks", data={})
    assert response.status_code == 400
    assert response.json == {"error": "description and category are required"}

def test_add_task_missing_description(client):
    response = client.post("/tasks", data={"category": "work"})
    assert response.status_code == 400
    assert response.json == {"error": "description is required"}

def test_add_task_missing_category(client):
    response = client.post("/tasks", data={"description": "Complete assignment"})
    assert response.status_code == 400
    assert response.json == {"error": "category is required"}
    
def test_get_task_by_id(client):
    for task in loaded_tasks:
        task_id = task["id"]
        response = client.get(f"/tasks/{task_id}")      
        assert response.status_code == 200
        response_task = response.json
        assert response_task["id"] == task["id"]
        assert response_task["description"] == task["description"]
        assert response_task["category"] == task["category"]
        assert response_task["status"] == task["status"]

def test_get_task_by_id_not_found(client):
    response = client.get("/tasks/999")
    assert response.status_code == 404
    assert response.json == {"error": "Task not found"}

def test_delete_task(client):
    task_id = 125
    for task in loaded_tasks:
        if task["id"] == task_id:
            description = task["description"]
    response = client.delete(f"/tasks/{task_id}", json={"password": "123"})
    assert response.status_code == 200
    expected_msg = f"The task with description, {description}! Has been deleted"
    assert response.json["msg"] == expected_msg
    remaining_ids = [task["id"] for task in loaded_tasks]
    assert task_id not in remaining_ids 

def test_delete_task_incorrect_password(client):
    for task in loaded_tasks:
        task_id = task["id"] 
        response = client.delete(f"/tasks/{task_id}", json={"password": "124"})        
        assert response.status_code == 401
        assert response.json == {"error": "Unauthorized access. Invalid password."}

def test_delete_task_not_found(client):
    response = client.delete(f"/tasks/999", json={"password": "123"})
    assert response.status_code == 404
    assert response.json == {"error": "Task not found"}

def test_replace_task_by_id(client):
    task_id = 131
    updated_data = {
        "description": "Updated description",
        "category": "Updated category"
    }
    response = client.put(f"/tasks/{task_id}", json=updated_data)
    assert response.status_code == 201
    response_task = response.json
    assert response_task["id"] == task_id
    assert response_task["description"] == updated_data["description"]
    assert response_task["category"] == updated_data["category"]
    assert response_task["status"] == "pending"

def test_replace_task_by_id_missing_description(client):
    task_id = 130
    incomplete_data = {
        "category": "Updated category"
    }
    response = client.put(f"/tasks/{task_id}", json=incomplete_data)
    assert response.status_code == 400
    assert response.json == {"error": "Both description and category are required"}

def test_replace_task_by_id_missing_category(client):
    task_id = 130 
    incomplete_data = {
        "description": "Updated category"
    }
    response = client.put(f"/tasks/{task_id}", json=incomplete_data)
    assert response.status_code == 400
    assert response.json == {"error": "Both description and category are required"}

def test_replace_task_by_id_not_found(client):
    non_existent_task_id = 9999 
    updated_data = {
        "description": "Updated description",
        "category": "Updated category"
    }
    response = client.put(f"/tasks/{non_existent_task_id}", json=updated_data)
    assert response.status_code == 404 
    assert response.json == {"error": "Task not found"}

def test_complete_task(client):
    task_id = 124
    response = client.put(f"/tasks/{task_id}/complete")
    assert response.status_code == 200
    assert response.json["status"] == "complete"

def test_complete_task_not_found(client):
    non_existent_task_id = 9999 
    response = client.put(f"/tasks/{non_existent_task_id}/complete")
    assert response.status_code == 404
    assert response.json == {"error": "Task not found"}

def test_get_all_categories(client):
    with open("tasks.json", "r") as json_file:
        tasks = json.load(json_file)
    expected_categories = list(set(task.get("category") for task in tasks))
    response = client.get("/tasks/categories")
    actual_categories = response.json
    assert sorted(actual_categories) == sorted(expected_categories)

def test_get_task_in_category_found(client):
    category_name = loaded_tasks[0]["category"]
    expected_tasks = [task for task in loaded_tasks if task["category"].capitalize() == category_name.capitalize()]
    response = client.get(f"/tasks/categories/{category_name}")
    assert response.status_code == 200
    assert response.json == expected_tasks

def test_get_task_in_category_not_found(client):
    non_existent_category = "NonExistentCategory"
    response = client.get(f"/tasks/categories/{non_existent_category}")
    assert response.status_code == 404
    assert response.json == {"error": "category not found"}   

