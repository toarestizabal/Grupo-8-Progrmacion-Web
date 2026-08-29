"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const formLogin = document.querySelector("#formLogin");
    const formRecuperar = document.querySelector("#formRecuperar");
    const formPerfil = document.querySelector("#formPerfil");

    function claveValida(clave) {
        return clave.length >= 8 && clave.length <= 18 && /[A-Z]/.test(clave) && /[a-z]/.test(clave)
            && /[0-9]/.test(clave) && /[^A-Za-z0-9]/.test(clave);
    }

    function mostrar(formulario, texto, tipo = "danger") {
        const aviso = formulario.querySelector(".mensaje-formulario");
        aviso.className = `mensaje-formulario alert alert-${tipo}`;
        aviso.textContent = texto;
    }

    function fechaParaMostrar(fecha) {
        if (!/^\d{4}-\d{2}-\d{2}$/.test(fecha)) return fecha;
        const [anio, mes, dia] = fecha.split("-");
        return `${dia}-${mes}-${anio}`;
    }

    function validarFecha(fecha) {
        const partes = fecha.split("-").map(Number);
        if (partes.length !== 3) return null;

        const [dia, mes, anio] = partes;
        const nacimiento = new Date(anio, mes - 1, dia);
        const hoy = new Date();
        const fechaReal = nacimiento.getFullYear() === anio
            && nacimiento.getMonth() === mes - 1
            && nacimiento.getDate() === dia;

        if (!fechaReal || nacimiento > hoy) return null;

        let edad = hoy.getFullYear() - anio;
        if (hoy.getMonth() < mes - 1 || (hoy.getMonth() === mes - 1 && hoy.getDate() < dia)) edad--;
        if (edad < 13) return null;

        return `${anio}-${String(mes).padStart(2, "0")}-${String(dia).padStart(2, "0")}`;
    }

    formLogin?.addEventListener("submit", (evento) => {
        evento.preventDefault();
        const correo = formLogin.correo.value.trim().toLowerCase();
        const clave = formLogin.clave.value;
        const usuarios = PixelForge.leer(PixelForge.claves.usuarios, []);
        const usuario = usuarios.find((item) => item.correo.toLowerCase() === correo && item.clave === clave);

        if (!usuario) return mostrar(formLogin, "Correo o contraseña incorrectos.");
        if (!usuario.activo) return mostrar(formLogin, "Esta cuenta se encuentra desactivada.");

        PixelForge.guardar(PixelForge.claves.sesion, {
            id: usuario.id,
            nombre: usuario.nombre,
            correo: usuario.correo,
            rol: usuario.rol
        });
        window.location.href = usuario.rol === "administrador" ? "../admin/productos.html" : "../index.html";
    });

    formRecuperar?.addEventListener("submit", (evento) => {
        evento.preventDefault();
        const correo = formRecuperar.correo.value.trim().toLowerCase();
        const nueva = formRecuperar.clave.value;
        const repetir = formRecuperar.repetirClave.value;
        const usuarios = PixelForge.leer(PixelForge.claves.usuarios, []);
        const usuario = usuarios.find((item) => item.correo.toLowerCase() === correo);

        if (!usuario) return mostrar(formRecuperar, "No existe una cuenta asociada a ese correo.");
        if (!claveValida(nueva)) return mostrar(formRecuperar, "La contraseña no cumple los requisitos de seguridad.");
        if (nueva !== repetir) return mostrar(formRecuperar, "Las contraseñas no coinciden.");

        usuario.clave = nueva;
        PixelForge.guardar(PixelForge.claves.usuarios, usuarios);
        formRecuperar.reset();
        mostrar(formRecuperar, "Contraseña actualizada. Ya puedes iniciar sesión.", "success");
    });

    if (formPerfil) {
        const sesion = PixelForge.exigirSesion();
        if (!sesion) return;
        const usuarios = PixelForge.leer(PixelForge.claves.usuarios, []);
        const usuario = usuarios.find((item) => item.id === sesion.id);

        formPerfil.nombre.value = usuario.nombre;
        formPerfil.usuario.value = usuario.usuario;
        formPerfil.correo.value = usuario.correo;
        formPerfil.fecha.value = fechaParaMostrar(usuario.fecha);
        formPerfil.direccion.value = usuario.direccion || "";

        formPerfil.fecha.addEventListener("input", () => {
            const numeros = formPerfil.fecha.value.replace(/\D/g, "").slice(0, 8);
            formPerfil.fecha.value = numeros.length > 4
                ? `${numeros.slice(0, 2)}-${numeros.slice(2, 4)}-${numeros.slice(4)}`
                : numeros.length > 2
                    ? `${numeros.slice(0, 2)}-${numeros.slice(2)}`
                    : numeros;
            formPerfil.fecha.classList.remove("is-invalid");
        });

        formPerfil.addEventListener("submit", (evento) => {
            evento.preventDefault();
            const correo = formPerfil.correo.value.trim().toLowerCase();
            const repetido = usuarios.some((item) => item.id !== usuario.id && item.correo.toLowerCase() === correo);
            if (repetido) return mostrar(formPerfil, "Ese correo ya está registrado.");

            const fechaNacimiento = validarFecha(formPerfil.fecha.value);
            if (!fechaNacimiento) {
                formPerfil.fecha.classList.add("is-invalid");
                formPerfil.fecha.focus();
                return mostrar(formPerfil, "Revisa la fecha de nacimiento.");
            }

            formPerfil.fecha.classList.remove("is-invalid");
            usuario.nombre = formPerfil.nombre.value.trim();
            usuario.usuario = formPerfil.usuario.value.trim();
            usuario.correo = correo;
            usuario.fecha = fechaNacimiento;
            usuario.direccion = formPerfil.direccion.value.trim();

            const nueva = formPerfil.clave.value;
            if (nueva && !claveValida(nueva)) {
                return mostrar(formPerfil, "La nueva contraseña no cumple los requisitos.");
            }
            if (nueva) usuario.clave = nueva;

            PixelForge.guardar(PixelForge.claves.usuarios, usuarios);
            PixelForge.guardar(PixelForge.claves.sesion, { id: usuario.id, nombre: usuario.nombre, correo, rol: usuario.rol });
            mostrar(formPerfil, "Perfil actualizado correctamente.", "success");
            formPerfil.clave.value = "";
        });
    }
});
