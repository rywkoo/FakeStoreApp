from flask import Flask, request, render_template, jsonify, flash, redirect, url_for
from flask_mail import Mail, Message
from data.faqs import faqs
import traceback
import requests
import json
import io
from datetime import date
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # required for flashing messages

# ======== CONFIGURE EMAIL =========
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'theareachmiku@gmail.com'
app.config['MAIL_PASSWORD'] = 'otppdcjyhanngoks'  # Avoid committing this to version control
app.config['MAIL_DEFAULT_SENDER'] = 'theareachmiku@gmail.com'

mail = Mail(app)

# ======== TELEGRAM CONFIG =========
TELEGRAM_BOT_TOKEN = '7884087901:AAGrPE8dJauRXZMZdw7mPktJsAnhSWQWIgs'
TELEGRAM_CHAT_ID = 'your_chat_id'

# ========== ROUTES ==========

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

@app.get('/product/<int:pro_id>')
def product(pro_id):
    product = None
    error = ''
    try:
        r = requests.get(f"https://fakestoreapi.com/products/{pro_id}")
        if r.status_code == 200:
            product = r.json()
    except Exception as e:
        error = e
    return render_template('productDetail.html', product=product, error=error)

@app.get('/store')
def store():
    products = []
    error = ''
    try:
        r = requests.get('https://fakestoreapi.com/products')
        if r.status_code == 200:
            products = r.json()
    except Exception as e:
        error = e
    return render_template('store.html', products=products, error=error)

@app.get('/cart')
def cart():
    product = []
    error = ''
    try:
        r = requests.get('https://fakestoreapi.com/products')
        if r.status_code == 200:
            product = r.json()
    except Exception as e:
        error = e
    return render_template('cartList.html', product=product, error=error)

@app.route("/support")
def support():
    return render_template("support.html", loop_faq=faqs)

@app.route("/email")
def email():
    return render_template("checkoutEmail.html", loop_faq=faqs)

# ========== INVOICE TO EMAIL + TELEGRAM ==========
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No JSON data received'}), 400

            name = data.get('name', '')
            phone = data.get('phone', '')
            email = data.get('email', '')
            address = data.get('address', '')
            cart_list = data.get('cart', [])

            # Calculate total (qty * price)
            total = sum(item.get('quantity', item.get('qty', 1)) * item.get('price', 0) for item in cart_list)

            # Render invoice HTML for email
            invoice_html = render_template('checkoutEmail.html',
                                           name=name,
                                           phone=phone,
                                           email=email,
                                           address=address,
                                           cart=cart_list,
                                           total=total)

            # Prepare email message
            msg = Message(subject='🧾 Your Order Invoice',
                          recipients=[email],
                          html=invoice_html)

            mail.send(msg)

            # Prepare Telegram text message
            message_lines = [
                f"<strong>🧾 Invoice #{date.today().strftime('%Y%m%d')}</strong>",
                f"<code>👤 {name}</code>",
                f"<code>📧 {email}</code>",
                f"<code>📆 {date.today()}</code>",
                f"<code>🏠 {address}</code>",
                "<code>=======================</code>",
            ]
            for i, item in enumerate(cart_list, start=1):
                qty = item.get('quantity', item.get('qty', 1))
                subtotal = qty * item.get('price', 0)
                message_lines.append(
                    f"<code>{i}. {item['title']} x{qty} = ${subtotal:.2f}</code>"
                )
            message_lines.append("<code>=======================</code>")
            message_lines.append(f"<code>💵 Total: ${total:.2f}</code>")

            telegram_message = "\n".join(message_lines)

            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": telegram_message, "parse_mode": "HTML"}
            )

            # Create PDF invoice in memory
            buffer = io.BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=letter)
            pdf.drawString(50, 750, f"Invoice for {name}")
            pdf.drawString(50, 735, f"Email: {email}")
            pdf.drawString(50, 720, f"Phone: {phone}")
            pdf.drawString(50, 705, f"Address: {address}")
            pdf.drawString(50, 690, "-" * 40)

            y = 670
            for i, item in enumerate(cart_list, start=1):
                qty = item.get('quantity', item.get('qty', 1))
                subtotal = qty * item.get('price', 0)
                pdf.drawString(50, y, f"{i}. {item['title']} x{qty} = ${subtotal:.2f}")
                y -= 20

            pdf.drawString(50, y - 10, f"Total: ${total:.2f}")
            pdf.save()
            buffer.seek(0)

            # Send PDF invoice to Telegram
            files = {'document': ('invoice.pdf', buffer, 'application/pdf')}
            data = {'chat_id': TELEGRAM_CHAT_ID}
            requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument',
                          data=data, files=files)

            return jsonify({'success': True})

        except Exception as e:
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # GET request: render the checkout page
    return render_template('checkOut.html')