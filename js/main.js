/* ============================================================
   Jacket Masters — interacciones y animaciones
   ============================================================ */

(function () {
  "use strict";

  // Elementos comunes
  const nav = document.getElementById("nav");
  const navLinks = document.getElementById("navLinks");
  const navMenuBtn = document.getElementById("navMenuBtn");
  const navPanel = document.getElementById("navPanel");
  const navClose = document.getElementById("navClose");
  const heroTitle = document.querySelector(".hero__title");
  const cards = document.querySelectorAll(".card");
  const caracteristicasItems = document.querySelectorAll(".caracteristicas__item");
  const testimonios = document.querySelectorAll(".testimonio");
  const newsletterForm = document.getElementById("newsletterForm");
  const newsletterEmail = document.getElementById("newsletterEmail");
  const newsletterError = document.getElementById("newsletterError");

  // ===== MENU MOBILE =====
  function toggleNavPanel(open) {
    if (!navPanel) return;
    const isOpen = !!open;
    navPanel.classList.toggle("open", isOpen);
    navMenuBtn.setAttribute("aria-expanded", isOpen);
    document.body.style.overflow = isOpen ? "hidden" : "";
  }

  navMenuBtn.addEventListener("click", () => toggleNavPanel(true));
  navClose.addEventListener("click", () => toggleNavPanel(false));

  navPanel.addEventListener("click", (e) => {
    if (e.target === navPanel) toggleNavPanel(false);
  });

  // Cierra el panel al hacer clic en un enlace
  navLinks.addEventListener("click", (e) => {
    if (e.target.tagName === "A") {
      toggleNavPanel(false);
    }
  });

  // Cierra al tirar fuera (solo desktop)
  window.addEventListener("resize", () => {
    if (window.innerWidth > 768 && navPanel.classList.contains("open")) {
      toggleNavPanel(false);
    }
  });

  // ===== SCROLL REVEAL (IntersectionObserver) =====
  const revealElements = () => {
    const items = () => {
      return [
        ...document.querySelectorAll(".section, .card, .caracteristicas__item, .testimonio"),
        ...document.querySelectorAll(".hero__product-frame, .hero__title, .hero__subtitle, .hero__actions")
      ];
    };

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );

    items().forEach((el) => el.classList.add("is-visible"));
    // Re-ejecutar si se añaden elementos dinámicamente
    const ro = new MutationObserver(() => {
      const extra = () => {
        const current = new Set(items());
        document.querySelectorAll(".card, .caracteristicas__item, .testimonio, .section").forEach((el) => current.add(el));
        [...current].forEach((el) => {
          if (!el.classList.contains("is-visible")) {
            el.classList.add("is-visible");
            observer.observe(el);
          }
        });
      };
      if (document.body) ro.disconnect();
      ro.observe(document.body, { childList: true, subtree: true });
    });
  };

  revealElements();

  // ===== HERO TITLE ENTRANCE =====
  if (heroTitle) {
    const titleObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.style.opacity = "1";
            entry.target.style.transform = "translateY(0)";
            titleObserver.disconnect();
          }
        });
      },
      { threshold: 0.3 }
    );
    // La clase .hero__title ya viene con opacity 0 en CSS; la inyectamos aquí
    // (Ya está definido en el CSS, así que solo aplicamos la transición)
  }

  // ===== CHIPS DE TALLA =====
  const chips = document.querySelectorAll(".chip");
  const swatches = document.querySelectorAll(".swatch");
  const activeChip = document.querySelector(".chip--active");

  if (chips.length) {
    chips.forEach((chip) => {
      chip.addEventListener("click", () => {
        chips.forEach((c) => c.classList.remove("chip--active"));
        swatches.forEach((s) => s.classList.remove("swatch--active"));
        chip.classList.add("chip--active");
      });
    });

    swatches.forEach((sw) => {
      sw.addEventListener("click", () => {
        swatches.forEach((s) => s.classList.remove("swatch--active"));
        sw.classList.add("swatch--active");
      });
    });
  }

  // ===== TESTIMONIOS — indicador de carrusel (solo si hay más de uno) =====
  const testimoniosList = document.querySelector(".testimonios__list");
  if (testimonios.length > 1 && testimoniosList) {
    // Las tarjetas ya son un grid responsive; se deja como está.
  }

  // ===== NEWSLETTER FORM =====
  if (newsletterForm) {
    newsletterForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const email = newsletterEmail.value.trim();

      if (!email) {
        showNewsletterError("Escribe tu correo electrónico primero.");
        return;
      }

      // Validación básica de email
      const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRe.test(email)) {
        showNewsletterError("El correo no parece válido. Revisa y vuelve a intentar.");
        return;
      }

      // Simulación de envío (en una app real aquí iría un fetch)
      newsletterForm.classList.add("is-submitting");
      setTimeout(() => {
        newsletterForm.classList.remove("is-submitting");
        showNewsletterError("");
        newsletterEmail.value = "";
        // Aquí iría el fetch real a tu backend/Pipedream/n8n
        console.log("Newsletter:", email);
      }, 800);
    });
  }

  function showNewsletterError(msg) {
    newsletterError.textContent = msg;
    newsletterError.style.opacity = "1";
    setTimeout(() => {
      newsletterError.style.opacity = "0";
    }, 4000);
  }

  // ===== SMOOTH SCROLL =====
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (e) => {
      const href = anchor.getAttribute("href");
      if (href === "#" || href === "") return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        const offset = 92;
        const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
        window.scrollTo({ top, behavior: "smooth" });
      }
    });
  });

  // ===== NAVBAR SHADOW AL SCROLL =====
  let lastScroll = 0;
  window.addEventListener("scroll", () => {
    const current = window.pageYOffset;
    if (current > 20) {
      nav.style.boxShadow = "0 2px 20px rgba(0,0,0,0.35)";
    } else {
      nav.style.boxShadow = "none";
    }
    lastScroll = current;
  });

  // Indicador visual de talla seleccionada
  const sizeLabel = document.createElement("div");
  sizeLabel.className = "size-indicator visually-hidden";
  sizeLabel.id = "sizeIndicator";
  document.body.appendChild(sizeLabel);

  // Sincronizar con el primer chip activo
  setTimeout(() => {
    const active = document.querySelector(".chip--active");
    if (active) {
      sizeLabel.textContent = `Talla: ${active.textContent}`.trim();
    }
  }, 150);
})();
