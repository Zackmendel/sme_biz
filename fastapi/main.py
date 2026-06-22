from fastapi import FastAPI


app = FastAPI()

items =[
    {"item_id": 1, "name": "photocopy", "cost": 80, "quantity": 50},
    {"item_id": 2, "name": "printing", "cost": 90, "quantity": 10},
    {"item_id": 3, "name": "scan", "cost": 10, "quantity": 100},
    {"item_id": 4, "name": "lamination", "cost": 50, "quantity": 20},
    {"item_id": 5, "name": "binding", "cost": 100, "quantity": 5}
]



@app.get("/health")
def health_check():
    return({"status: ok"})

@app.get("/items")
def get_items():
    return items

@app.get("/items/{item_id}")
def get_item(item_id: int):
    for item in items:
        if item["item_id"] == item_id:
            return item
    return {"error": "Item not found"}