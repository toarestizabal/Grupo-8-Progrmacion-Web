"use strict";

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-toggle-password]").forEach((control) => {
        const campo = document.getElementById(control.dataset.togglePassword);
        if (!campo) return;
        control.addEventListener("change", () => {
            campo.type = control.checked ? "text" : "password";
        });
    });

    document.querySelectorAll("form[data-confirm]").forEach((formulario) => {
        formulario.addEventListener("submit", (evento) => {
            if (!window.confirm(formulario.dataset.confirm)) evento.preventDefault();
        });
    });

    document.querySelectorAll("[data-expiry]").forEach((campo) => {
        const formatearVencimiento = () => {
            const digitos = campo.value.replace(/\D/g, "").slice(0, 4);
            campo.value = digitos.length > 2
                ? `${digitos.slice(0, 2)}/${digitos.slice(2)}`
                : digitos;
        };

        campo.addEventListener("input", formatearVencimiento);
        formatearVencimiento();
    });
});
