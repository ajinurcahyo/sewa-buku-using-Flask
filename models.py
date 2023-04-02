from flask_wtf import Form
from wtforms import FileField, SubmitField
from wtforms import Form, validators, StringField, FloatField, IntegerField, DateField, SelectField, IntegerField
import pymysql
import config

db = cursor = None

class MPengguna():
    def __init__(self, username=None, password=None, level=None):
        self.username = username
        self.password = password
        #self.user_id = user_id
        self.level = level
    
    def openDB(self):
        global db, cursor
        db = pymysql.connect(
            host = config.DB_HOST,
            user = config.DB_USER,
            password = config.DB_PASSWORD,
            database = config.DB_NAME
        )
        cursor = db.cursor()
    
    def closeDB(self):
        global db, cursor
        db.close()

    def authenticate(self):
        self.openDB()
        cursor.execute("SELECT * FROM user WHERE username = '%s' AND password = MD5('%s') AND level ='%s'" % 
                    (self.username, self.password, self.level))

        account = cursor.fetchone()
        if account:
            self.user_id = account[0]
            self.username = account[1]
            #self.level = account[4]
            return True
        self.closeDB()
        return False

    def insertDB(self, data):
        self.openDB()
        cursor.execute("INSERT INTO user (nama, username, password, level) VALUES('%s','%s', MD5('%s'),'%s')" % data)
        db.commit()
        self.closeDB()

class AddPost:
    file = FileField('Pilih file yang akan diunggah')
    submit = SubmitField('Upload')
    def __init__(self, post_id=None, user_id=None, publish_date=None,image=None):
        self.post_id = post_id
        self.user_id = user_id
        self.publish_date = publish_date
        self.image = image

    def openDB(self):
        global db, cursor
        db = pymysql.connect(
            host = config.DB_HOST,
            user = config.DB_USER,
            password = config.DB_PASSWORD,
            database = config.DB_NAME
        )
        cursor = db.cursor()

    def closeDB(self):
        global db, cursor
        db.close()

    def insertDB(self, data):
        self.openDB()
        cursor.execute("INSERT INTO post (user_id, publish_date, image) VALUES('%s','%s','%s')" % (data))
        db.commit()
        self.closeDB()
    
    def selectDB(self, user_id):
        self.openDB()
        cursor.execute("SELECT * FROM post WHERE user_id='%s' ORDER BY post_id DESC" % (user_id))
        container = []
        for post_id, user_id, publish_date, image in cursor.fetchall():
            container.append((post_id, user_id, publish_date, image))
        self.closeDB()
        return container

# ---- form ----

class AddMember(Form):
    name = StringField('Nama', [validators.Length(min=1, max=50)])
    email = StringField('Email', [validators.length(min=6, max=50)])
    submit = SubmitField('Kirim')

class AddBook(Form):
    id = StringField('Book ID', [validators.Length(min=1, max=11)])
    judul = StringField('Judul', [validators.Length(min=2, max=255)])
    pengarang = StringField('Pengarang', [validators.Length(min=2, max=255)])
    rating = FloatField(
        'Rating', [validators.NumberRange(min=0, max=10)])
    isbn = StringField('ISBN', [validators.Length(min=10, max=10)])
    bahasa = StringField('Bahasa', [validators.Length(min=1, max=255)])
    jml_halaman = IntegerField('Jumlah Halaman', [validators.NumberRange(min=1)])
    jml_ulasan = IntegerField(
        'Jumlah Ulasan', [validators.NumberRange(min=0)])
    tgl_terbit = DateField(
        'Tanggal Terbit', [validators.InputRequired()])
    penerbit = StringField('Penerbit', [validators.Length(min=2, max=255)])
    total_buku = IntegerField(
        'Total Buku', [validators.NumberRange(min=1)])

class SewaBuku(Form):
    id_buku = SelectField('Judul Buku', choices=[], coerce=int)
    id_member = SelectField('Nama Member', choices=[], coerce=int)
    biaya_sewa = SelectField('Biaya Sewa /hari', choices=[(10000,10000)], coerce=int)

class ReturnBook(Form):
    jml_bayar = IntegerField('Jumlah Uang Bayar:', [validators.NumberRange(min=0)])

class SearchBook(Form):
    judul = StringField('Judul Buku:', [validators.Length(min=2, max=255)])