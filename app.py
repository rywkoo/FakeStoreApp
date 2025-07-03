from flask import Flask, render_template
import  requests

app = Flask(__name__)


@app.get('/')
@app.get('/home')
def home():
    products = []
    error = ''
    try:
        r = requests.get('https://fakestoreapi.com/products')
        if r.status_code == 200:
            products = r.json()
    except Exception as e:
        error = e
    return render_template('home.html', products=products, error=error)


@app.get('/about')
def about():
    return render_template('about.html')


@app.get('/api/products')
def getProducts():
    products = [
        {
            "id": 1,
            "title": "Fjallraven - Foldsack No. 1 Backpack, Fits 15 Laptops",
            "price": 109.95,
            "description": "Your perfect pack for everyday use and walks in the forest. Stash your laptop (up to 15 inches) in the padded sleeve, your everyday",
            "category": "men's clothing",
            "image": "https://fakestoreapi.com/img/81fPKd-2AYL._AC_SL1500_.jpg",
            "rating": {
                "rate": 3.9,
                "count": 120
            }
        },
    ]
    return products


if __name__ == '__main__':
    app.run()
