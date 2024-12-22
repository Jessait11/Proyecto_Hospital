from flask import Flask, render_template, request, redirect, url_for, flash, session
import pyodbc

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Conexión a la base de datos
def get_db_connection():
    try:
        conn = pyodbc.connect(
            "Driver={ODBC Driver 17 for SQL Server};"
            "Server=DESKTOP-VJDVO9P\\SQLEXPRESS01;"  # Cambia según tu configuración
            "Database=Hospital3;"
            "Trusted_Connection=yes;"
        )
        print("Conexión a la base de datos exitosa.")
        return conn
    except Exception as e:
        print(f"Error de conexión a la base de datos: {e}")
        raise

# Página principal
@app.route('/')
def index():
    return render_template(
        'home.html',
        title="Hospital Salud para Todos",
        about_text="Somos un hospital comprometido con la salud y el bienestar de nuestra comunidad, ofreciendo servicios médicos de calidad con tecnología de punta.",
        servicios=[
            {"titulo": "Consultas Generales", "descripcion": "Atención primaria con médicos altamente capacitados."},
            {"titulo": "Urgencias", "descripcion": "Servicio de urgencias disponible las 24 horas del día."},
            {"titulo": "Laboratorio Clínico", "descripcion": "Resultados precisos y rápidos para tus análisis médicos."},
            {"titulo": "Cardiología", "descripcion": "Diagnóstico y tratamiento avanzado en enfermedades del corazón."},
            {"titulo": "Dermatología", "descripcion": "Tratamiento de enfermedades de la piel con especialistas."},
            {"titulo": "Pediatría", "descripcion": "Cuidado integral para pacientes menores de 17 años."}
        ],
        especialistas_intro="Contamos con un equipo multidisciplinario de médicos expertos en diversas áreas.",
        direccion="Calle Salud #123, Ciudad, País",
        telefono="+52 555 123 4567",
        email="contacto@hospital.com",
        year=2024
    )

# Ruta para el inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Verificar las credenciales del usuario
            cursor.execute("""
                SELECT u.id_usuario, u.tipo_usuario, e.id_empleado
                FROM Usuario u
                LEFT JOIN Empleado e ON u.id_usuario = e.id_usuario
                WHERE u.email = ? AND u.contrasena = ?
            """, (email, password))
            user = cursor.fetchone()

            if user:
                id_usuario, tipo_usuario, id_empleado = user
                session['id_usuario'] = id_usuario
                session['tipo_usuario'] = tipo_usuario

                flash(f"Bienvenido, {tipo_usuario}.", "success")

                if tipo_usuario == "Paciente":
                    return redirect(url_for('dashboard_paciente'))
                elif tipo_usuario == "Empleado":
                    cursor.execute("""
                        SELECT 'Doctor' AS tipo_empleado
                        FROM Doctor
                        WHERE id_empleado = ?
                        UNION
                        SELECT 'Recepcionista' AS tipo_empleado
                        FROM Recepcionista
                        WHERE id_empleado = ?
                    """, (id_empleado, id_empleado))
                    empleado = cursor.fetchone()

                    if empleado and empleado.tipo_empleado == "Doctor":
                        return redirect(url_for('dashboard_doctor'))
                    elif empleado and empleado.tipo_empleado == "Recepcionista":
                        return redirect(url_for('dashboard_recepcionista'))
            else:
                flash("Correo o contraseña incorrectos.", "danger")

        except Exception as e:
            flash(f"Error al iniciar sesión: {e}", "danger")
            print(f"Error al procesar inicio de sesión: {e}")

    return render_template('login.html')

# Ruta para el registro de pacientes
@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            nombre = request.form.get('nombre')
            apellido_paterno = request.form.get('apellido_paterno')
            apellido_materno = request.form.get('apellido_materno')
            calle = request.form.get('calle')
            numero = request.form.get('numero')
            colonia = request.form.get('colonia')
            codigo_postal = request.form.get('codigo_postal')
            ciudad = request.form.get('ciudad')
            estado = request.form.get('estado')
            curp = request.form.get('curp')
            telefono = request.form.get('telefono')
            email = request.form.get('email')
            contrasena = request.form.get('contrasena')

            try:
                cursor.execute("""
                    INSERT INTO Direccion (calle, numero, colonia, codigo_postal, ciudad, estado)
                    OUTPUT INSERTED.id_direccion
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (calle, numero, colonia, codigo_postal, ciudad, estado))
                id_direccion = cursor.fetchone()[0]

                cursor.execute("""
                    INSERT INTO Usuario (tipo_usuario, nombre, apellido_paterno, apellido_materno, id_direccion, curp, telefono, email, contrasena)
                    OUTPUT INSERTED.id_usuario
                    VALUES ('Paciente', ?, ?, ?, ?, ?, ?, ?, ?)
                """, (nombre, apellido_paterno, apellido_materno, id_direccion, curp, telefono, email, contrasena))
                id_usuario = cursor.fetchone()[0]

                cursor.execute("""
                    INSERT INTO Paciente (id_usuario)
                    VALUES (?)
                """, (id_usuario,))
                conn.commit()
                flash('Paciente registrado exitosamente. Inicia sesión.', 'success')
                return redirect(url_for('login'))

            except Exception as e:
                conn.rollback()
                flash(f"Error al registrar paciente: {e}", "danger")

    except Exception as e:
        flash(f"No se pudo cargar el formulario de registro: {e}", "danger")

    return render_template('register.html')

# Ruta para el panel del paciente
@app.route('/dashboard_paciente')
def dashboard_paciente():
    if 'id_usuario' not in session:
        flash("Por favor, inicia sesión para acceder a esta página.", "warning")
        return redirect(url_for('login'))
    return render_template('dashboard_paciente.html')

# Ruta para el perfil del paciente
@app.route('/perfil_paciente')
def perfil_paciente():
    if 'id_usuario' not in session:
        flash("Por favor, inicia sesión para acceder a esta página.", "warning")
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consulta para obtener los datos del paciente
        cursor.execute("""
            SELECT u.nombre, u.apellido_paterno, u.apellido_materno, u.email, u.telefono, u.curp,
                   d.calle, d.numero, d.colonia, d.codigo_postal, d.ciudad, d.estado
            FROM Usuario u
            INNER JOIN Direccion d ON u.id_direccion = d.id_direccion
            WHERE u.id_usuario = ?
        """, (session['id_usuario'],))
        perfil = cursor.fetchone()

        if perfil:
            datos = {
                "nombre": perfil[0],
                "apellido_paterno": perfil[1],
                "apellido_materno": perfil[2],
                "email": perfil[3],
                "telefono": perfil[4],
                "curp": perfil[5],
                "direccion": {
                    "calle": perfil[6],
                    "numero": perfil[7],
                    "colonia": perfil[8],
                    "codigo_postal": perfil[9],
                    "ciudad": perfil[10],
                    "estado": perfil[11]
                }
            }
            return render_template('perfil_paciente.html', datos=datos)
        else:
            flash("No se encontraron los datos del perfil.", "danger")
            return redirect(url_for('dashboard_paciente'))

    except Exception as e:
        flash(f"Error al obtener los datos del perfil: {e}", "danger")
        return redirect(url_for('dashboard_paciente'))
    finally:
        conn.close()


# Ruta para agendar citas (placeholder)
@app.route('/agendar_cita', methods=['GET', 'POST'])
def agendar_cita():
    if 'id_usuario' not in session:
        flash("Por favor, inicia sesión para acceder a esta página.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Lógica para agendar citas
        pass
    return render_template('agendar_cita.html')

# Ruta para el panel del doctor
@app.route('/dashboard_doctor')
def dashboard_doctor():
    if 'id_usuario' not in session:
        flash("Por favor, inicia sesión para acceder a esta página.", "warning")
        return redirect(url_for('login'))
    
    return render_template('dashboard_doctor.html')


# Ruta para el perfil del doctor
@app.route('/perfil_doctor')
def perfil_doctor():
    if 'id_usuario' not in session:
        flash("Por favor, inicia sesión para acceder a esta página.", "warning")
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.nombre, u.apellido_paterno, u.apellido_materno, u.email, u.telefono, u.curp,
                   d.calle, d.numero, d.colonia, d.codigo_postal, d.ciudad, d.estado,
                   es.nombre_especialidad, c.numero_consultorio
            FROM Usuario u
            INNER JOIN Direccion d ON u.id_direccion = d.id_direccion
            INNER JOIN Empleado e ON u.id_usuario = e.id_usuario
            INNER JOIN Doctor doc ON e.id_empleado = doc.id_empleado
            INNER JOIN Especialidad es ON doc.id_especialidad = es.id_especialidad
            INNER JOIN Consultorio c ON doc.id_consultorio = c.id_consultorio
            WHERE u.id_usuario = ?
        """, (session['id_usuario'],))
        datos = cursor.fetchone()

        if datos:
            perfil = {
                "nombre": datos[0],
                "apellido_paterno": datos[1],
                "apellido_materno": datos[2],
                "email": datos[3],
                "telefono": datos[4],
                "curp": datos[5],
                "direccion": {
                    "calle": datos[6],
                    "numero": datos[7],
                    "colonia": datos[8],
                    "codigo_postal": datos[9],
                    "ciudad": datos[10],
                    "estado": datos[11],
                },
                "especialidad": datos[12],
                "consultorio": datos[13],
            }
            return render_template('perfil_doctor.html', perfil=perfil)
        else:
            flash("No se encontraron los datos del perfil.", "danger")
            return redirect(url_for('dashboard_doctor'))

    except Exception as e:
        flash(f"Error al obtener los datos del perfil: {e}", "danger")
        print(f"Error: {e}")
        return redirect(url_for('dashboard_doctor'))
    finally:
        conn.close()

# Ruta para el calendario del doctor
@app.route('/calendario_doctor')
def calendario_doctor():
    if 'id_usuario' not in session:
        flash("Por favor, inicia sesión para acceder a esta página.", "warning")
        return redirect(url_for('login'))
    return render_template('calendario_doctor.html')  # Archivo HTML correcto

# Ruta para ver y gestionar recetas del doctor
@app.route('/recetas_doctor')
def recetas_doctor():
    if 'id_usuario' not in session:
        flash("Por favor, inicia sesión para acceder a esta página.", "warning")
        return redirect(url_for('login'))
    
    # Aquí puedes agregar lógica para listar o mostrar recetas
    return render_template('recetas_doctor.html')

@app.route('/pacientes_asignados_doctor')
def pacientes_asignados_doctor():
    if 'id_usuario' not in session:
        flash("Por favor, inicia sesión para acceder a esta página.", "warning")
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consulta para obtener los pacientes asignados al doctor
        cursor.execute("""
            SELECT p.nombre, p.apellido_paterno, p.apellido_materno, c.fecha, c.hora, c.motivo
            FROM Cita c
            INNER JOIN Paciente p ON c.id_paciente = p.id_usuario
            WHERE c.id_doctor = (SELECT id_empleado FROM Empleado WHERE id_usuario = ?)
        """, (session['id_usuario'],))
        pacientes = cursor.fetchall()

        return render_template('pacientes_asignados_doctor.html', pacientes=pacientes)

    except Exception as e:
        flash(f"Error al obtener los pacientes asignados: {e}", "danger")
        return redirect(url_for('dashboard_doctor'))
    finally:
        conn.close()


# Ruta para el panel del recepcionista
@app.route('/dashboard_recepcionista')
def dashboard_recepcionista():
    if 'id_usuario' not in session:
        flash("Por favor, inicia sesión para acceder a esta página.", "warning")
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consulta para obtener los datos del recepcionista
        cursor.execute("""
            SELECT u.nombre, u.apellido_paterno, u.apellido_materno, e.id_empleado
            FROM Usuario u
            INNER JOIN Empleado e ON u.id_usuario = e.id_usuario
            WHERE u.id_usuario = ?
        """, (session['id_usuario'],))
        recepcionista = cursor.fetchone()

        if recepcionista:
            datos_recepcionista = {
                "nombre": recepcionista[0],
                "apellido_paterno": recepcionista[1],
                "apellido_materno": recepcionista[2],
                "id": recepcionista[3]
            }
            return render_template('dashboard_recepcionista.html', recepcionista=datos_recepcionista)
        else:
            flash("No se encontraron datos del recepcionista.", "danger")
            return redirect(url_for('login'))

    except Exception as e:
        flash(f"Error al cargar el panel: {e}", "danger")
        return redirect(url_for('login'))
    finally:
        conn.close()


@app.route('/doctores', methods=['GET'])
def doctores():
    if 'id_usuario' not in session:
        flash("Por favor, inicia sesión para acceder a esta página.", "warning")
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consulta para obtener la lista de doctores con especialidad y consultorio
        cursor.execute("""
            SELECT u.nombre, u.apellido_paterno, u.apellido_materno, es.nombre_especialidad, c.numero_consultorio
            FROM Usuario u
            INNER JOIN Empleado e ON u.id_usuario = e.id_usuario
            INNER JOIN Doctor d ON e.id_empleado = d.id_empleado
            INNER JOIN Especialidad es ON d.id_especialidad = es.id_especialidad
            INNER JOIN Consultorio c ON d.id_consultorio = c.id_consultorio
        """)
        doctores = cursor.fetchall()

        lista_doctores = []
        for doctor in doctores:
            lista_doctores.append({
                "nombre": doctor[0],
                "apellido_paterno": doctor[1],
                "apellido_materno": doctor[2],
                "especialidad": doctor[3],
                "consultorio": doctor[4]
            })

        return render_template('doctores.html', doctores=lista_doctores)

    except Exception as e:
        flash(f"Error al cargar la lista de doctores: {e}", "danger")
        return redirect(url_for('dashboard_recepcionista'))
    finally:
        conn.close()


@app.route('/pacientes')
def pacientes():
    return "Página de pacientes"

@app.route('/citas')
def citas():
    return "Página de citas"

@app.route('/consultorios')
def consultorios():
    return "Página de consultorios"

@app.route('/agregar_empleado')
def agregar_empleado():
    return "Página para agregar empleado"

@app.route('/farmacia')
def farmacia():
    # Aquí puedes agregar la lógica necesaria para la página de farmacia
    return render_template('farmacia.html')

@app.route('/cobro')
def cobro():
    # Aquí puedes agregar la lógica para la página de cobro
    return render_template('cobro.html')

@app.route('/historial_paciente')
def historial_paciente():
    # Aquí puedes agregar la lógica para el historial del paciente
    return render_template('historial_paciente.html')




# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesión exitosamente.", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
