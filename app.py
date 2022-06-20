from flask import Flask
from flask import render_template, request, redirect, url_for, flash
from flaskext.mysql import MySQL
from decouple import config

app = Flask(__name__)
app.secret_key = config('SECRET_KEY')
mysql = MySQL()
app.config['MYSQL_DATABASE_HOST'] = config('DB_HOST')
app.config['MYSQL_DATABASE_USER'] = config('DB_USER')
app.config['MYSQL_DATABASE_PASSWORD']= config('DB_PASSWORD')
app.config['MYSQL_DATABASE_BD'] = config('DB_NAME')
mysql.init_app(app)


@app.route('/')
def index():
    sql = "SELECT * FROM estudio.factura JOIN estudio.cliente ON estudio.factura.cliente_id = estudio.cliente.id_cliente ORDER BY fecha DESC LIMIT 10"
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql)
    facturas = cursor.fetchall()
    conn.commit()
    return render_template("index.html", facturas = facturas)

@app.context_processor
def clientes():
    sql = "SELECT estudio.cliente.id_cliente, estudio.cliente.denominacion FROM estudio.cliente"
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql)
    clientes = cursor.fetchall()
    conn.commit()
    return dict(clientes=clientes)


@app.route('/nueva_factura')
def nueva_factura():
    return render_template("factura.html")


@app.route('/guardar_factura', methods=['POST'])
def guardar_factura():
    _cliente_id = request.form['cliente_id']
    _fecha = request.form['fecha']
    _concepto = str(request.form['concepto'])
    _importe = float(request.form['importe'])

    datos = (_cliente_id, _fecha, _concepto, _importe)

    sql = "INSERT INTO estudio.factura VALUES (NULL, %s, %s, %s, %s)"

    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql, datos)
    conn.commit()

    return redirect('/')

@app.route('/nuevo_recibo', methods=['POST'])
def nuevo_recibo():
    _id_cliente = request.form['id_cliente']
    _denominacion = request.form['denominacion']
    _id_factura = request.form['id_factura']
    _concepto = request.form['concepto']
    _importe = float(request.form['importe'])

    datos = (_id_cliente, _denominacion, _id_factura, _concepto, _importe)

    return render_template('recibo.html', datos_recibo = datos)

  
@app.route('/guardar_recibo', methods=['POST'])
def guardar_recibo():
    _fecha = request.form['fecha']
    _id_factura = request.form['id_factura']
    _importe = float(request.form['importe'])
    _id_cliente = request.form['id_cliente']

    sql = "INSERT INTO estudio.recibo VALUES (NULL, %s, %s, %s)"
    datos = (_fecha, _importe, _id_factura)

    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql, datos)
    conn.commit()

    return redirect(url_for('deuda', id = _id_cliente))



@app.route('/deuda/<int:id>')
def deuda(id):
    sql = f"SELECT estudio.cliente.id_cliente, estudio.cliente.denominacion, estudio.factura.id_factura, estudio.factura.fecha, estudio.factura.concepto, estudio.factura.importe FROM estudio.factura JOIN estudio.cliente ON estudio.factura.cliente_id = estudio.cliente.id_cliente WHERE estudio.factura.id_factura NOT IN(SELECT estudio.factura.id_factura FROM estudio.factura JOIN estudio.recibo ON estudio.factura.id_factura = estudio.recibo.factura_id) AND estudio.factura.cliente_id = {id}"
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql)
    deuda = cursor.fetchall()
    sql = f"SELECT SUM(estudio.factura.importe) FROM estudio.factura JOIN estudio.cliente ON estudio.factura.cliente_id = estudio.cliente.id_cliente WHERE estudio.factura.id_factura NOT IN(SELECT estudio.factura.id_factura FROM estudio.factura JOIN estudio.recibo ON estudio.factura.id_factura = estudio.recibo.factura_id) AND estudio.factura.cliente_id = {id}"
    cursor.execute(sql)
    total = cursor.fetchall()
    conn.commit()
    return render_template("deuda.html", deuda = deuda, total=total)


@app.route('/resumen/<int:id>')
def resumen(id):
    sql = f"SELECT 'Factura' AS nombre, estudio.factura.fecha AS fecha, estudio.factura.importe FROM estudio.factura WHERE estudio.factura.cliente_id = {id} UNION (SELECT 'Recibo' AS nombre, estudio.recibo.fecha AS fecha, estudio.recibo.importe_cobro FROM estudio.recibo WHERE estudio.recibo.factura_id IN (SELECT estudio.factura.id_factura FROM estudio.factura WHERE estudio.factura.cliente_id = {id})) ORDER BY fecha"
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql)
    resumen = cursor.fetchall()
    conn.commit()
    sql = f"SELECT SUM(estudio.factura.importe) FROM estudio.factura JOIN estudio.cliente ON estudio.factura.cliente_id = estudio.cliente.id_cliente WHERE estudio.factura.id_factura NOT IN(SELECT estudio.factura.id_factura FROM estudio.factura JOIN estudio.recibo ON estudio.factura.id_factura = estudio.recibo.factura_id) AND estudio.factura.cliente_id = {id}"
    cursor.execute(sql)
    total = cursor.fetchall()
    conn.commit()
    return render_template('/detalle_deuda.html', resumen=resumen, cliente_id = id, total_deuda = total)

if __name__ == "__main__":
    app.run(debug=config('DEBUG', cast=bool))