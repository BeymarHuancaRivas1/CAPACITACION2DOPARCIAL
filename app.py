
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "huellitas-clave-de-desarrollo"  


def get_db_connection():

    conn = sqlite3.connect("bd_veterinaria.db")

    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@app.route("/")
def inicio():

    return redirect(url_for("listar_mascotas"))



@app.route("/mascotas")
def listar_mascotas():
    conn = get_db_connection()
    mascotas = conn.execute("SELECT * FROM mascotas ORDER BY nombre").fetchall()
    conn.close()
    return render_template("mascotas.html", mascotas=mascotas)


@app.route("/mascotas/nueva", methods=["GET", "POST"])
def nueva_mascota():
    if request.method == "POST":
        
        nombre = request.form["nombre"].strip()
        especie = request.form["especie"]
        raza = request.form["raza"].strip()
        dueno = request.form["dueno"].strip()
        telefono = request.form["telefono"].strip()

        conn = get_db_connection()
      
        conn.execute(
            "INSERT INTO mascotas (nombre, especie, raza, dueno, telefono) VALUES (?, ?, ?, ?, ?)",
            (nombre, especie, raza, dueno, telefono),
        )
        conn.commit()
        conn.close()

        flash(f"¡{nombre} ya está registrado en Huellitas! 🐶")
        return redirect(url_for("listar_mascotas"))

    return render_template("form_mascota.html", mascota=None)


@app.route("/mascotas/editar/<int:id>", methods=["GET", "POST"])
def editar_mascota(id):
    conn = get_db_connection()
    mascota = conn.execute("SELECT * FROM mascotas WHERE id = ?", (id,)).fetchone()

    if mascota is None:
        conn.close()
        flash("Esa mascota no existe o ya fue eliminada.", "error")
        return redirect(url_for("listar_mascotas"))

    if request.method == "POST":
        conn.execute(
            """UPDATE mascotas
               SET nombre = ?, especie = ?, raza = ?, dueno = ?, telefono = ?
               WHERE id = ?""",
            (
                request.form["nombre"].strip(),
                request.form["especie"],
                request.form["raza"].strip(),
                request.form["dueno"].strip(),
                request.form["telefono"].strip(),
                id,
            ),
        )
        conn.commit()
        conn.close()
        flash("Datos de la mascota actualizados.")
        return redirect(url_for("listar_mascotas"))

    conn.close()
    return render_template("form_mascota.html", mascota=mascota)


@app.route("/mascotas/eliminar/<int:id>", methods=["POST"])
def eliminar_mascota(id):
   
    conn = get_db_connection()
    conn.execute("DELETE FROM mascotas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Mascota eliminada.")
    return redirect(url_for("listar_mascotas"))




@app.route("/servicios")
def listar_servicios():
    conn = get_db_connection()
    servicios = conn.execute("SELECT * FROM servicios ORDER BY nombre").fetchall()
    conn.close()
    return render_template("servicios.html", servicios=servicios)


def leer_datos_servicio():
    """Saca los datos del formulario de servicio. Lo separé porque lo uso al crear y al editar."""
    return (
        request.form["nombre"].strip(),
        float(request.form["precio"]),
        int(request.form["duracion_min"]),
    )


@app.route("/servicios/nuevo", methods=["GET", "POST"])
def nuevo_servicio():
    if request.method == "POST":
        try:
            nombre, precio, duracion = leer_datos_servicio()
        except ValueError:
           
            flash("Revisa el precio y la duración, tienen que ser números.", "error")
            return redirect(url_for("nuevo_servicio"))

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO servicios (nombre, precio, duracion_min) VALUES (?, ?, ?)",
            (nombre, precio, duracion),
        )
        conn.commit()
        conn.close()
        flash(f"Servicio \"{nombre}\" agregado.")
        return redirect(url_for("listar_servicios"))

    return render_template("form_servicio.html", servicio=None)


@app.route("/servicios/editar/<int:id>", methods=["GET", "POST"])
def editar_servicio(id):
    conn = get_db_connection()
    servicio = conn.execute("SELECT * FROM servicios WHERE id = ?", (id,)).fetchone()

    if servicio is None:
        conn.close()
        flash("Ese servicio no existe.", "error")
        return redirect(url_for("listar_servicios"))

    if request.method == "POST":
        try:
            nombre, precio, duracion = leer_datos_servicio()
        except ValueError:
            conn.close()
            flash("Revisa el precio y la duración, tienen que ser números.", "error")
            return redirect(url_for("editar_servicio", id=id))

        conn.execute(
            "UPDATE servicios SET nombre = ?, precio = ?, duracion_min = ? WHERE id = ?",
            (nombre, precio, duracion, id),
        )
        conn.commit()
        conn.close()
        flash("Servicio actualizado.")
        return redirect(url_for("listar_servicios"))

    conn.close()
    return render_template("form_servicio.html", servicio=servicio)


@app.route("/servicios/eliminar/<int:id>", methods=["POST"])
def eliminar_servicio(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM servicios WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Servicio eliminado.")
    return redirect(url_for("listar_servicios"))


# ----------------------------------------------------------------
#  CITAS  (la tabla que une mascotas con servicios)
# ----------------------------------------------------------------

@app.route("/citas")
def listar_citas():
    conn = get_db_connection()
    
    citas = conn.execute("""
        SELECT citas.id,
               citas.fecha,
               citas.observacion,
               mascotas.nombre   AS mascota,
               mascotas.especie  AS especie,
               mascotas.dueno    AS dueno,
               servicios.nombre  AS servicio,
               servicios.precio  AS precio
        FROM citas
        JOIN mascotas  ON mascotas.id  = citas.mascota_id
        JOIN servicios ON servicios.id = citas.servicio_id
        ORDER BY citas.fecha
    """).fetchall()
    conn.close()


    total = sum(cita["precio"] for cita in citas)
    return render_template("citas.html", citas=citas, total=total)


@app.route("/citas/nueva", methods=["GET", "POST"])
def nueva_cita():
    conn = get_db_connection()

    if request.method == "POST":
        conn.execute(
            "INSERT INTO citas (mascota_id, servicio_id, fecha, observacion) VALUES (?, ?, ?, ?)",
            (
                request.form["mascota_id"],
                request.form["servicio_id"],
                request.form["fecha"],
                request.form["observacion"].strip(),
            ),
        )
        conn.commit()
        conn.close()
        flash("Cita agendada. ¡Los esperamos! 📅")
        return redirect(url_for("listar_citas"))

    # Para llenar los <select> del formulario
    mascotas = conn.execute("SELECT * FROM mascotas ORDER BY nombre").fetchall()
    servicios = conn.execute("SELECT * FROM servicios ORDER BY nombre").fetchall()
    conn.close()
    return render_template("form_cita.html", mascotas=mascotas, servicios=servicios)


@app.route("/citas/cancelar/<int:id>", methods=["POST"])
def cancelar_cita(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM citas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("La cita fue cancelada.")
    return redirect(url_for("listar_citas"))


if __name__ == "__main__":
    app.run(debug=True)
