"""
StackConnect Phoenix 2026 — Demo App
Grand Phoenix Hotel Booking App
=================================
Generic hotel booking app for the self-healing demo.

Run:
  pip install flask
  python app.py
  Open: http://localhost:8080

To simulate the UI change (Demo 1):
  Change UI_BROKEN = False  →  UI_BROKEN = True
  Save. Restart. The button id changes from 'book-now' to 'reserve-room'.
"""
from flask import Flask, render_template_string

app = Flask(__name__)

# ── Toggle this to simulate the developer renaming the button ─────────────────
# False = normal state    (test passes)
# True  = broken state    (test breaks → healer fires)
UI_BROKEN = True

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Grand Phoenix Hotel — Book Your Stay</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:'Segoe UI',Arial,sans-serif}
body{background:#F0F4F8;min-height:100vh}
.header{background:#1A3A5C;color:white;padding:16px 40px;display:flex;align-items:center;justify-content:space-between}
.logo{font-size:22px;font-weight:700;letter-spacing:1px}
.nav a{color:#A0C4E8;text-decoration:none;margin-left:24px;font-size:14px}
.hero{background:linear-gradient(135deg,#1A3A5C,#2D6A9F);color:white;padding:60px 40px;text-align:center}
.hero h1{font-size:42px;margin-bottom:12px}
.hero p{font-size:18px;opacity:.8}
.form-wrap{max-width:800px;margin:-30px auto 40px;background:white;border-radius:12px;padding:32px;box-shadow:0 4px 24px rgba(0,0,0,.12)}
.form-title{font-size:20px;font-weight:600;color:#1A3A5C;margin-bottom:20px}
.form-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:16px}
.form-group label{display:block;font-size:12px;font-weight:600;color:#64748B;text-transform:uppercase;margin-bottom:6px}
.form-group input,.form-group select{width:100%;padding:10px 14px;border:1.5px solid #E2E8F0;border-radius:8px;font-size:15px;color:#1E293B;outline:none}
.form-group input:focus,.form-group select:focus{border-color:#2D6A9F}
.btn-book{width:100%;padding:14px;border:none;border-radius:8px;font-size:16px;font-weight:700;cursor:pointer;background:#E8611A;color:white;margin-top:8px;transition:.2s}
.btn-book:hover{background:#C94F10;transform:translateY(-1px)}
.rooms{max-width:800px;margin:0 auto 60px}
.rooms h2{font-size:22px;font-weight:700;color:#1A3A5C;margin-bottom:16px}
.room-card{background:white;border-radius:12px;padding:20px 24px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,.07);display:flex;justify-content:space-between;align-items:center}
.room-name{font-size:17px;font-weight:600;color:#1A3A5C}
.room-desc{font-size:13px;color:#64748B;margin-top:3px}
.room-price{font-size:22px;font-weight:700;color:#E8611A}
.room-night{font-size:12px;color:#94A3B8}
.status-bar{background:#ECFDF5;border:1px solid #6EE7B7;border-radius:8px;padding:10px 16px;margin-bottom:20px;font-size:13px;color:#065F46;font-family:monospace}
</style>
</head>
<body>
<div class="header">
  <div class="logo">🏨 Grand Phoenix Hotel</div>
  <nav class="nav"><a href="#">Rooms</a><a href="#">Dining</a><a href="#">Spa</a><a href="#">Contact</a></nav>
</div>
<div class="hero">
  <h1>Where Every Stay Is Unforgettable</h1>
  <p>Luxury accommodations in the heart of Phoenix, Arizona</p>
</div>
<div class="form-wrap">
  <div class="form-title">Book Your Stay</div>

  <!-- STATUS BAR: shows current button id for demo clarity -->
  <div class="status-bar">
    Demo state: <strong>{{ state }}</strong> — button id = <code>{{ btn_id }}</code>
  </div>

  <div class="form-row">
    <div class="form-group"><label>Check-in</label><input type="date" id="checkin"></div>
    <div class="form-group"><label>Check-out</label><input type="date" id="checkout"></div>
    <div class="form-group"><label>Guests</label>
      <select id="guests">
        <option>1 Guest</option><option>2 Guests</option><option>3 Guests</option>
      </select>
    </div>
  </div>
  <div class="form-row">
    <div class="form-group"><label>First Name</label><input type="text" id="first-name" placeholder="John"></div>
    <div class="form-group"><label>Last Name</label><input type="text" id="last-name" placeholder="Smith"></div>
    <div class="form-group"><label>Email</label><input type="email" id="email" placeholder="john@email.com"></div>
  </div>

  <!-- THE KEY BUTTON — id changes when UI_BROKEN = True -->
  <button id="{{ btn_id }}" class="btn-book" onclick="handleBook()">{{ btn_text }}</button>
</div>

<div class="rooms">
  <h2>Our Rooms</h2>
  {% for room in rooms %}
  <div class="room-card">
    <div><div class="room-name">{{ room.name }}</div><div class="room-desc">{{ room.desc }}</div></div>
    <div style="text-align:right"><div class="room-price">${{ room.price }}</div><div class="room-night">per night</div></div>
  </div>
  {% endfor %}
</div>
<script>
function handleBook() {
  const name = document.getElementById('first-name').value;
  const date = document.getElementById('checkin').value;
  if (!name || !date) { alert('Please fill in your name and check-in date.'); return; }
  alert('Booking confirmed for ' + name + '! Confirmation sent to your email.');
}
</script>
</body></html>"""

@app.route("/")
def index():
    if UI_BROKEN:
        btn_id   = "reserve-room"
        btn_attr = 'id="reserve-room"'
        btn_text = "Reserve Now"
        state    = "BROKEN — developer renamed button to reserve-room"
    else:
        btn_id   = "book-now"
        btn_attr = 'id="book-now"'
        btn_text = "Book Now"
        state    = "NORMAL — button id is book-now"

    rooms = [
        {"name":"Deluxe King Room",   "desc":"City view · King bed · 420 sq ft",           "price":289},
        {"name":"Premier Suite",       "desc":"Mountain view · Separate living · 680 sq ft", "price":489},
        {"name":"Presidential Suite",  "desc":"Panoramic · Butler service · 1200 sq ft",     "price":989},
    ]
    return render_template_string(HTML, btn_id=btn_id, btn_attr=btn_attr,
                                   btn_text=btn_text, state=state, rooms=rooms)

if __name__ == "__main__":
    print("\n" + "="*52)
    print("  Grand Phoenix Hotel — StackConnect Demo App")
    print(f"  UI_BROKEN = {UI_BROKEN}")
    print(f"  Button ID = {'reserve-room' if UI_BROKEN else 'book-now'}")
    print("  http://localhost:8080")
    print("  To break: set UI_BROKEN = True, save, restart")
    print("="*52 + "\n")
    app.run(port=8080, debug=False)
