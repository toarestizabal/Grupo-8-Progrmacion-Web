"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const formulario = document.querySelector("#formularioRegistro");

    if (!formulario) {
        return;
    }

    const campos = {
        nombre: document.querySelector("#nombreCompleto"),
        usuario: document.querySelector("#nombreUsuario"),
        correo: document.querySelector("#correo"),
        clave: document.querySelector("#clave"),
        repetirClave: document.querySelector("#repetirClave"),
        fecha: document.querySelector("#fechaNacimiento"),
        direccion: document.querySelector("#direccion")
    };

    const mensajeExito = document.querySelector("#mensajeExito");

    const fechaMaxima = new Date();
    fechaMaxima.setFullYear(fechaMaxima.getFullYear() - 13);
    campos.fecha.max = formatearFecha(fechaMaxima);

    function formatearFecha(fecha) {
        const anio = fecha.getFullYear();
        const mes = String(fecha.getMonth() + 1).padStart(2, "0");
        const dia = String(fecha.getDate()).padStart(2, "0");
        return `${anio}-${mes}-${dia}`;
    }

    function mostrarError(campo, mensaje) {
        campo.classList.remove("is-valid");
        campo.classList.add("is-invalid");
        campo.setCustomValidity(mensaje);

        const contenedor = campo.closest("div");
        const aviso = contenedor?.querySelector(".invalid-feedback");
        if (aviso) {
            aviso.textContent = mensaje;
        }

        return false;
    }

    function marcarValido(campo) {
        campo.classList.remove("is-invalid");
        campo.classList.add("is-valid");
        campo.setCustomValidity("");
        return true;
    }

    function validarTexto(campo, mensaje) {
        if (campo.value.trim() === "") {
            return mostrarError(campo, mensaje);
        }
        return marcarValido(campo);
    }

    function validarCorreo() {
        const correo = campos.correo.value.trim();
        const formatoCorreo = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (correo === "") {
            return mostrarError(campos.correo, "El correo electrónico es obligatorio.");
        }
        if (!formatoCorreo.test(correo)) {
            return mostrarError(campos.correo, "Ingresa un correo electrónico válido.");
        }
        return marcarValido(campos.correo);
    }

    function validarClave() {
        const clave = campos.clave.value;

        if (clave === "") {
            return mostrarError(campos.clave, "La contraseña es obligatoria.");
        }
        if (clave.length < 6 || clave.length > 18) {
            return mostrarError(campos.clave, "La contraseña debe tener entre 6 y 18 caracteres.");
        }
        if (!/[A-Z]/.test(clave)) {
            return mostrarError(campos.clave, "La contraseña debe contener al menos una letra mayúscula.");
        }
        if (!/[0-9]/.test(clave)) {
            return mostrarError(campos.clave, "La contraseña debe contener al menos un número.");
        }
        return marcarValido(campos.clave);
    }

    function validarRepeticion() {
        if (campos.repetirClave.value === "") {
            return mostrarError(campos.repetirClave, "Debes repetir la contraseña.");
        }
        if (campos.repetirClave.value !== campos.clave.value) {
            return mostrarError(campos.repetirClave, "Las contraseñas deben coincidir.");
        }
        return marcarValido(campos.repetirClave);
    }

    function validarFecha() {
        if (campos.fecha.value === "") {
            return mostrarError(campos.fecha, "La fecha de nacimiento es obligatoria.");
        }

        const partes = campos.fecha.value.split("-").map(Number);
        const nacimiento = new Date(partes[0], partes[1] - 1, partes[2]);
        const hoy = new Date();
        let edad = hoy.getFullYear() - nacimiento.getFullYear();
        const diferenciaMes = hoy.getMonth() - nacimiento.getMonth();

        if (diferenciaMes < 0 || (diferenciaMes === 0 && hoy.getDate() < nacimiento.getDate())) {
            edad--;
        }

        if (edad < 13 || nacimiento > hoy) {
            return mostrarError(campos.fecha, "Debes tener al menos 13 años para registrarte.");
        }
        return marcarValido(campos.fecha);
    }

    function validarFormulario() {
        const resultados = [
            validarTexto(campos.nombre, "El nombre completo es obligatorio."),
            validarTexto(campos.usuario, "El nombre de usuario es obligatorio."),
            validarCorreo(),
            validarClave(),
            validarRepeticion(),
            validarFecha()
        ];

        return resultados.every(Boolean);
    }

    campos.nombre.addEventListener("blur", () => validarTexto(campos.nombre, "El nombre completo es obligatorio."));
    campos.usuario.addEventListener("blur", () => validarTexto(campos.usuario, "El nombre de usuario es obligatorio."));
    campos.correo.addEventListener("blur", validarCorreo);
    campos.clave.addEventListener("blur", () => {
        validarClave();
        if (campos.repetirClave.value !== "") {
            validarRepeticion();
        }
    });
    campos.repetirClave.addEventListener("blur", validarRepeticion);
    campos.fecha.addEventListener("change", validarFecha);

    formulario.addEventListener("submit", (evento) => {
        evento.preventDefault();
        mensajeExito.classList.add("d-none");

        if (validarFormulario()) {
            mensajeExito.classList.remove("d-none");
            mensajeExito.scrollIntoView({ behavior: "smooth", block: "center" });
        } else {
            formulario.querySelector(".is-invalid")?.focus();
        }
    });

    formulario.addEventListener("reset", () => {
        window.setTimeout(() => {
            formulario.querySelectorAll(".is-valid, .is-invalid").forEach((campo) => {
                campo.classList.remove("is-valid", "is-invalid");
                campo.setCustomValidity("");
            });
            mensajeExito.classList.add("d-none");
        }, 0);
    });
});
