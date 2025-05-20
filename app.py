from flask import Flask, request, jsonify, render_template
import sqlite3
import csv
import io
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('contacts.db')  # File-based database
    conn.row_factory = sqlite3.Row  # Enable row access by column name
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS contacts 
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 phone TEXT,
                 email TEXT,
                 address TEXT,
                 group_name TEXT)''')
    conn.commit()
    conn.close()
# Initialize database when the app starts
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contacts', methods=['GET'])
def get_contacts():
    search = request.args.get('search', '')
    group = request.args.get('group', '')
    conn = get_db_connection()
    c = conn.cursor()
    
    query = 'SELECT * FROM contacts WHERE 1=1'
    params = []
    
    if search:
        query += ' AND (name LIKE ? OR phone LIKE ? OR email LIKE ? OR address LIKE ?)'
        params.extend([f'%{search}%'] * 4)
    
    if group:
        query += ' AND group_name = ?'
        params.append(group)
    
    c.execute(query, params)
    contacts = [{'id': row['id'], 'name': row['name'], 'phone': row['phone'], 'email': row['email'], 
                'address': row['address'], 'group_name': row['group_name']} for row in c.fetchall()]
    conn.close()
    return jsonify(contacts)

@app.route('/contacts', methods=['POST'])
def add_contact():
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO contacts (name, phone, email, address, group_name) VALUES (?, ?, ?, ?, ?)',
             (data['name'], data['phone'], data['email'], data['address'], data['group_name']))
    conn.commit()
    contact_id = c.lastrowid
    conn.close()
    return jsonify({'id': contact_id})

@app.route('/contacts/<int:id>', methods=['PUT'])
def update_contact(id):
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE contacts SET name=?, phone=?, email=?, address=?, group_name=? WHERE id=?',
             (data['name'], data['phone'], data['email'], data['address'], data['group_name'], id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Contact updated'})

@app.route('/contacts/<int:id>', methods=['DELETE'])
def delete_contact(id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM contacts WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Contact deleted'})

@app.route('/groups', methods=['GET'])
def get_groups():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT DISTINCT group_name FROM contacts WHERE group_name IS NOT NULL')
    groups = [row['group_name'] for row in c.fetchall()]
    conn.close()
    return jsonify(groups)

@app.route('/export', methods=['GET'])
def export_contacts():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT name, phone, email, address, group_name FROM contacts')
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Phone', 'Email', 'Address', 'Group'])
    writer.writerows(c.fetchall())
    conn.close()
    return jsonify({'csv': output.getvalue()})

@app.route('/import', methods=['POST'])
def import_contacts():
    file = request.files['file']
    stream = io.StringIO(file.stream.read().decode('UTF-8'))
    reader = csv.reader(stream)
    next(reader)  # Skip header
    conn = get_db_connection()
    c = conn.cursor()
    for row in reader:
        c.execute('INSERT INTO contacts (name, phone, email, address, group_name) VALUES (?, ?, ?, ?, ?)', row)
    conn.commit()
    conn.close()
    return jsonify({'message': 'Contacts imported'})

if __name__ == '__main__':
    app.run(debug=True)