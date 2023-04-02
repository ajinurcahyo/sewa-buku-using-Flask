from flask import Flask, render_template, flash, redirect, url_for, request, session
from flask_mysqldb import MySQL
from datetime import datetime
import MySQLdb
import os
from werkzeug.utils import secure_filename
from models import MPengguna
from models import AddPost
from models import AddMember
from models import AddBook
from models import SewaBuku
from models import ReturnBook
from models import SearchBook

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_DB'] = 'sewa_bukudb'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

dir = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(dir, 'static/img')
ALLOWED_EXTENSIONS = {'png','jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        level = request.form['level']
        pengguna = MPengguna(username, password, level)

        if pengguna.authenticate():
            if level == 'User':
                session['username'] = username
                session['level'] = level
                session['user_id'] = pengguna.user_id
                return redirect(url_for('info'))
            else:
                session['username'] = username
                session['user_id'] = pengguna.user_id
                session['level'] = level
                return redirect(url_for('members'))
        else:
            flash("Gagal ! Tidak Cocok",'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

# Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    model = MPengguna()
    if request.method == 'POST':
        nama = request.form['nama']
        username = request.form['username']
        password = request.form['password']
        level = request.form['level']
        if len(nama) < 3:
            flash('Gagal Daftar Akun !', 'danger')
            return render_template('signup.html')
        else:
            data = (nama, username, password, level)
            model.insertDB(data)
            return redirect(url_for('login'))
    return render_template('signup.html')

# --------------- USER -----------------------#
# Info ( 3 buku terbanyak disewa )
@app.route('/')
def info():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT judul,pengarang,jml_disewa FROM books ORDER BY jml_disewa DESC LIMIT 3")
    books = cur.fetchall()
    msg = ''
    if result <= 0:
        msg = msg+'Tidak ditemukan'
    model = AddPost()
    if 'username' in session :
        user_id = session['user_id']
        username = session['username']
        level = session['level']
        container = []
        container = model.selectDB(user_id)
        return render_template('info.html', container=container, username=username, level=level, books=books, warning=msg)
    return redirect(url_for('login'))

# Buku
@app.route('/booksUsr')
def booksUsr():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT id,judul,pengarang,total_buku,jml_tersedia,jml_disewa FROM books")
    books = cur.fetchall()

    if result > 0:
        return render_template('buku_user.html', books=books)
    else:
        msg = 'Buku tidak ditemukan'
        return render_template('buku_user.html', warning=msg)
    cur.close()

# Detail Buku
@app.route('/book/<string:id>')
def viewBook(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM books WHERE id=%s", [id])
    book = cur.fetchone()

    if result > 0:
        return render_template('detail_buku.html', book=book)
    else:
        msg = 'Buku tidak tersedia'
        return render_template('detail_buku.html', warning=msg)
    cur.close()

# View member user
@app.route('/membersUsr')
def membersUsr():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM members")
    members = cur.fetchall()

    if result > 0:
        return render_template('member_user.html', members=members)
    else:
        msg = 'Member tidak ditemukan'
        return render_template('member_user.html', warning=msg)
    cur.close()

# Tambah member
@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    form = AddMember(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO members (nama, email) VALUES (%s, %s)", (name, email))
        mysql.connection.commit()
        cur.close()
        
        flash("Member berhasil ditambahkan", "success")
        return redirect(url_for('membersUsr'))
    return render_template('add_member.html', form=form)

# Sewa
@app.route('/sewa_buku', methods=['GET', 'POST'])
def sewa_buku():
    form = SewaBuku(request.form)
    # get value buku by id (judul)
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, judul FROM books")
    books = cur.fetchall()
    book_list = []
    for book in books:
        t = (book['id'], book['judul'])
        book_list.append(t)

    # get value member by id (nama)
    cur.execute("SELECT id, nama FROM members")
    members = cur.fetchall()
    member_list = []
    for member in members:
        t = (member['id'], member['nama'])
        member_list.append(t)
    form.id_buku.choices = book_list
    form.id_member.choices = member_list

    if request.method == 'POST' and form.validate():
        cur.execute("SELECT jml_tersedia FROM books WHERE id=%s", [form.id_buku.data])
        result = cur.fetchone()
        jml_tersedia = result['jml_tersedia']

        if(jml_tersedia < 1):
            error = 'Buku tidak tersedia'
            return render_template('sewa_buku.html', form=form, error=error)

        cur.execute("INSERT INTO transactions (id_buku,id_member,biaya_sewa) VALUES (%s, %s, %s)", [form.id_buku.data,form.id_member.data,form.biaya_sewa.data,])

        # Update jumlah buku yg tersedia, untuk disewa
        cur.execute(
            "UPDATE books SET jml_tersedia=jml_tersedia-1, jml_disewa=jml_disewa+1 WHERE id=%s", [form.id_buku.data])
        mysql.connection.commit()
        cur.close()
        flash("Buku berhasil disewa", "success")
        return redirect(url_for('transactionsUsr'))
    return render_template('sewa_buku.html', form=form)

# List transaksi sewa user
@app.route('/transactionsUsr')
def transactionsUsr():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM transactions")
    transactions = cur.fetchall()

    if result > 0:
        return render_template('transaksi_user.html', transactions=transactions)
    else:
        msg = 'Transaksi tidak ditemukan'
        return render_template('transaksi_user.html', warning=msg)
    cur.close()

# Detail member ( User )
@app.route('/member/<string:id>')
def viewMember(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM members WHERE id=%s", [id])
    member = cur.fetchone()

    if result > 0:
        return render_template('detail_member.html', member=member)
    else:
        msg = 'Member tidak ditemukan'
        return render_template('detail_member.html', warning=msg)
    cur.close()

# Pencarian ( buku )
@app.route('/search_book', methods=['GET', 'POST'])
def search_book():
    form = SearchBook(request.form)
    if request.method == 'POST' and form.validate():
        cur = mysql.connection.cursor()
        judul = '%'+form.judul.data+'%'
        result = cur.execute("SELECT * FROM books WHERE judul LIKE %s", [judul])
        books = cur.fetchall()
        cur.close()
        
        if result <= 0:
            msg = 'Buku Tidak Ditemukan'
            return render_template('cari_buku.html', form=form, warning=msg)
        flash("Buku Ditemukan", "success")
        return render_template('cari_buku.html', form=form, books=books)
    return render_template('cari_buku.html', form=form)

# Upload (foto)
@app.route('/add', methods=['GET', 'POST'])
def add_post():
    model = AddPost()
    if request.method == 'POST':
        f = request.files['file']
        user_id = session['user_id']
        if allowed_file(f.filename):
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            date = datetime.now()
            data = (user_id, date, filename)
            model.insertDB(data)
            return redirect(url_for('info'))
        else:
            flash("Gagal Upload File !", 'danger')
    return render_template('upload.html')

# ----------------- ADMIN ---------------------- #
# Data member
    # View member Admin
@app.route('/members')
def members():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM members")
    members = cur.fetchall()
    cur.close()
    
    model = AddPost()
    if 'username' in session and result > 0:
        user_id = session['user_id']
        username = session['username']
        level = session['level']
        container = []
        container = model.selectDB(user_id)
        return render_template('member_admin.html', container=container, username=username, level=level, members=members)
    else:
        msg = 'Member tidak ditemukan'
        return render_template('member_admin.html', warning=msg)
#return redirect(url_for('login'))

# Edit Member
@app.route('/edit_member/<string:id>', methods=['GET', 'POST'])
def edit_member(id):
    form = AddMember(request.form)

    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data

        cur = mysql.connection.cursor()
        cur.execute("UPDATE members SET nama=%s, email=%s WHERE id=%s", (name, email, id))
        mysql.connection.commit()
        cur.close()

        flash("Member Berhasil di update", "success")
        return redirect(url_for('members'))

    # select member by id
    cur2 = mysql.connection.cursor()
    cur2.execute("SELECT nama,email FROM members WHERE id=%s", [id])
    member = cur2.fetchone()
    return render_template('edit_member.html', form=form, member=member)

# Hapus Member
@app.route('/delete_member/<string:id>', methods=['POST'])
def delete_member(id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM members WHERE id=%s", [id])
        mysql.connection.commit()
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        flash("Member gagal dihapus", "danger")
        flash(str(e), "danger")
        return redirect(url_for('members'))
    finally:
        cur.close()

    flash("Member berhasil dihapus", "success")
    return redirect(url_for('members'))

# Data Buku 
# view
@app.route('/books')
def books():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT id,judul,pengarang,total_buku,jml_tersedia,jml_disewa FROM books")
    books = cur.fetchall()

    if result > 0:
        return render_template('buku_admin.html', books=books)
    else:
        msg = 'Buku tidak ditemukan'
        return render_template('buku_admin.html', warning=msg)
    cur.close()

# tambah Buku
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    form = AddBook(request.form)

    if request.method == 'POST' and form.validate():
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM books WHERE id=%s", [form.id.data])
        book = cur.fetchone()
        if(book):
            error = 'Buku dengan id tersebut sudah ada'
            return render_template('tambah_buku.html', form=form, error=error)
        cur.execute("INSERT INTO books (id,judul,pengarang,rating,isbn,bahasa,jml_halaman,jml_ulasan,tgl_terbit,penerbit,total_buku,jml_tersedia) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [
            form.id.data,form.judul.data,form.pengarang.data,form.rating.data,form.isbn.data,form.bahasa.data,form.jml_halaman.data,form.jml_ulasan.data,form.tgl_terbit.data,form.penerbit.data,form.total_buku.data,form.total_buku.data])
        mysql.connection.commit()
        cur.close()

        flash("Buku berhasil ditambah", "success")
        return redirect(url_for('books'))
    return render_template('tambah_buku.html', form=form)

# Edit Buku
@app.route('/edit_book/<string:id>', methods=['GET', 'POST'])
def edit_book(id):
    form = AddBook(request.form)
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM books WHERE id=%s", [id])
    book = cur.fetchone()

    if request.method == 'POST' and form.validate():
        if(form.id.data != id):
            cur.execute("SELECT id FROM books WHERE id=%s", [form.id.data])
            book = cur.fetchone()
            if(book):
                error = 'Buku dengan id tersebut sudah ada'
                return render_template('edit_buku.html', form=form, error=error, book=form.data)

        # menghitung jml buku yg tersedia (untuk disewa)
        jml_tersedia = book['jml_tersedia'] + \
            (form.total_buku.data - book['total_buku'])

        cur.execute("UPDATE books SET id=%s,judul=%s,pengarang=%s,rating=%s,isbn=%s,bahasa=%s,jml_halaman=%s,jml_ulasan=%s,tgl_terbit=%s,penerbit=%s,total_buku=%s,jml_tersedia=%s WHERE id=%s", [
            form.id.data,form.judul.data,form.pengarang.data,form.rating.data,form.isbn.data,form.bahasa.data,form.jml_halaman.data,form.jml_ulasan.data,form.tgl_terbit.data,form.penerbit.data,form.total_buku.data,jml_tersedia,id])
        mysql.connection.commit()
        cur.close()
        flash("Buku berhasil diupdate", "success")
        return redirect(url_for('books'))
    return render_template('edit_buku.html', form=form, book=book)

# Hapus buku
@app.route('/delete_book/<string:id>', methods=['POST'])
def delete_book(id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM books WHERE id=%s", [id])
        mysql.connection.commit()
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        flash("Buku gagal dihapus", "danger")
        flash(str(e), "danger")
        return redirect(url_for('books'))
    finally:
        cur.close()
    flash("Buku berhasil dihapus", "success")
    return redirect(url_for('books'))

# Data Sewa
# View
@app.route('/transactions')
def transactions():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM transactions")
    transactions = cur.fetchall()

    for transaction in transactions: # nilai transaksi jika tidak ada(none) maka kosong (-)
        for key, value in transaction.items():
            if value is None:
                transaction[key] = "-"

    if result > 0:
        return render_template('data_sewa.html', transactions=transactions)
    else:
        msg = 'Transaksi tidak ditemukan'
        return render_template('data_sewa.html', warning=msg)
    cur.close()

# Mengembalikan buku ( return)
@app.route('/return_book/<string:transaction_id>', methods=['GET', 'POST'])
def return_book(transaction_id):
    form = ReturnBook(request.form)
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM transactions WHERE id=%s", [transaction_id])
    transaction = cur.fetchone()

    # menghitung total biaya sewa ( /hari )
    date = datetime.now()
    difference = date - transaction['tgl_sewa']
    difference = difference.days
    total_tagihan = difference * transaction['biaya_sewa']

    if request.method == 'POST' and form.validate():
        cur.execute("SELECT total_pengeluaran FROM members WHERE id=%s", [transaction['id_member']])
        result = cur.fetchone()
        total_pengeluaran = result['total_pengeluaran']
        # Update tgl kembali, total tagihan, jumlah bayar utk transaksi
        cur.execute("UPDATE transactions SET tgl_kembali=%s,total_tagihan=%s,jml_bayar=%s WHERE id=%s", [date,total_tagihan,form.jml_bayar.data,transaction_id])

        # Update  total pengeluaran member
        cur.execute("UPDATE members SET total_pengeluaran=%s WHERE id=%s", [total_pengeluaran+form.jml_bayar.data,transaction['id_member']])

        # Update jumlah buku yg tersedia
        cur.execute("UPDATE books SET jml_tersedia=jml_tersedia+1 WHERE id=%s", [transaction['id_buku']])
        mysql.connection.commit()
        cur.close()
        flash("Buku berhasil dikembalikan", "success")
        return redirect(url_for('transactions'))
    return render_template('return_book.html', form=form, total_tagihan=total_tagihan, difference=difference, transaction=transaction)

# Logout
@app.route('/logout')
def logout():
    session.pop('username', '')
    return redirect(url_for('info'))

if __name__ == '__main__':
    app.secret_key = "secret"
    app.run(debug=True)
