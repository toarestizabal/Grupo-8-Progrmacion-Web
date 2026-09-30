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

    const catalogoExterno = document.querySelector("[data-catalogo-externo]");
    if (catalogoExterno) {
        const lista = catalogoExterno.querySelector("[data-lista-juegos]");
        const estado = catalogoExterno.querySelector("[data-estado-juegos]");
        const botonRecargar = document.querySelector("[data-recargar-juegos]");

        const crearTexto = (etiqueta, valor) => {
            const linea = document.createElement("p");
            const fuerte = document.createElement("strong");
            fuerte.textContent = `${etiqueta}: `;
            linea.append(fuerte, document.createTextNode(valor || "No informado"));
            return linea;
        };

        const crearTarjeta = (juego) => {
            const columna = document.createElement("article");
            columna.className = "col-12 col-md-6 col-lg-4";

            const tarjeta = document.createElement("div");
            tarjeta.className = "tarjeta tarjeta-externa h-100";

            if (juego.imagen) {
                const imagen = document.createElement("img");
                imagen.src = juego.imagen;
                imagen.alt = `Portada de ${juego.titulo}`;
                imagen.loading = "lazy";
                tarjeta.append(imagen);
            }

            const contenido = document.createElement("div");
            contenido.className = "contenido";
            const titulo = document.createElement("h2");
            titulo.textContent = juego.titulo;
            const descripcion = document.createElement("p");
            descripcion.textContent = juego.descripcion || "Sin descripción disponible.";
            contenido.append(
                titulo,
                descripcion,
                crearTexto("Género", juego.genero),
                crearTexto("Plataforma", juego.plataforma)
            );

            if (juego.enlace) {
                const enlace = document.createElement("a");
                enlace.className = "boton";
                enlace.href = juego.enlace;
                enlace.target = "_blank";
                enlace.rel = "noopener noreferrer";
                enlace.textContent = "Ver ficha externa";
                contenido.append(enlace);
            }

            tarjeta.append(contenido);
            columna.append(tarjeta);
            return columna;
        };

        const cargarJuegos = async () => {
            catalogoExterno.setAttribute("aria-busy", "true");
            estado.hidden = false;
            estado.className = "estado-servicio text-center";
            estado.textContent = "Cargando recomendaciones…";
            lista.replaceChildren();
            if (botonRecargar) botonRecargar.disabled = true;

            try {
                const respuesta = await fetch(catalogoExterno.dataset.endpoint, {
                    headers: { Accept: "application/json" },
                });
                const datos = await respuesta.json();
                if (!respuesta.ok) throw new Error(datos.detalle || "No fue posible cargar los juegos.");
                datos.resultados.forEach((juego) => lista.append(crearTarjeta(juego)));
                estado.hidden = true;
            } catch (error) {
                estado.className = "alert alert-danger";
                estado.textContent = error.message;
            } finally {
                catalogoExterno.setAttribute("aria-busy", "false");
                if (botonRecargar) botonRecargar.disabled = false;
            }
        };

        botonRecargar?.addEventListener("click", cargarJuegos);
        cargarJuegos();
    }

    const detalleExterno = document.querySelector("[data-detalle-externo]");
    if (detalleExterno) {
        const estado = detalleExterno.querySelector("[data-estado-detalle]");
        const contenido = detalleExterno.querySelector("[data-contenido-detalle]");

        const escribir = (selector, valor) => {
            const elemento = detalleExterno.querySelector(selector);
            if (elemento) elemento.textContent = valor;
        };

        const cargarDetalle = async () => {
            try {
                const respuesta = await fetch(detalleExterno.dataset.endpoint, {
                    headers: { Accept: "application/json" },
                });
                const datos = await respuesta.json();
                if (!respuesta.ok) {
                    throw new Error(datos.detalle || "No fue posible cargar la información.");
                }

                escribir("[data-titulo-externo]", datos.ficha.titulo);
                escribir("[data-resumen-externo]", datos.ficha.resumen);
                escribir("[data-desarrollador]", datos.ficha.desarrollador);
                escribir("[data-editor]", datos.ficha.editor);
                escribir("[data-plataformas]", datos.ficha.plataformas);
                escribir("[data-generos]", datos.ficha.generos);
                escribir("[data-lanzamiento]", datos.ficha.lanzamiento);
                escribir("[data-titulo-trailer]", datos.trailer.titulo);
                escribir("[data-canal-trailer]", datos.trailer.canal);

                const reproductor = detalleExterno.querySelector("[data-video-producto]");
                reproductor.src = datos.trailer.video;
                contenido.hidden = false;
                estado.hidden = true;
            } catch (error) {
                estado.className = "alert alert-danger";
                estado.textContent = error.message;
            } finally {
                detalleExterno.setAttribute("aria-busy", "false");
            }
        };

        cargarDetalle();
    }
});
